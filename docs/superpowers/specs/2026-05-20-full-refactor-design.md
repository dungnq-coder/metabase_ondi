# Full project refactor — design

**Date:** 2026-05-20
**Branch:** dev
**Author:** dungnq (assisted)

## Goals

1. Move hardcoded per-project mapping data (`sr`/`nw`/`bl`) out of Python source into per-project YAML files. New project = new file, not new code edit.
2. Split monolithic files: `cards_menu.py` (993 LOC) → menu + card processor module. `mapping.py` → focused modules (`sql_rewriter`, `field_mapper`, `template_tags`).
3. Replace fragile `Base._api_url` mutation pattern with a real HTTP client (session, timeout, retry).
4. Add ruff + pytest + mypy. Unit tests cover SQL rewriter, field mapper, project config loader.
5. Unify logging — replace `print()` debug spam with `logging`. Menu-facing prints stay.
6. Fix latent bugs: `fs_timline_event` typo; `replace_table_names_in_query` signature lies about return type.

## Non-goals

- Rewriting Metabase API behavior. Endpoints called and payloads sent must remain equivalent.
- Refactoring `utils/print_*.py` cosmetic functions.
- Switching from `requests` to `httpx`.
- Adding async.

## Target directory layout

```
metabase_ondi/
├── pyproject.toml                 # ruff, pytest, mypy; drops yapf
├── .pre-commit-config.yaml        # ruff-format + ruff lint; drops yapf/isort
├── core/
│   ├── config.yaml                # metabase creds (unchanged)
│   └── projects/                  # NEW
│       ├── _global.yaml           # ignored_tables, spec_tables
│       ├── sr.yaml
│       ├── nw.yaml
│       └── bl.yaml
├── src/
│   ├── config/
│   │   ├── __init__.py
│   │   ├── base_config.py         # moved from core/; typo fixed
│   │   └── project_config.py      # NEW: loads core/projects/*.yaml
│   ├── http/
│   │   ├── __init__.py
│   │   └── client.py              # NEW: session, retry, timeout
│   ├── connector/
│   │   ├── manager.py             # passes shared client
│   │   └── api/                   # uses src/http/client.py; no _api_url mutation
│   ├── mapping/                   # NEW (replaces src/utils/mapping.py)
│   │   ├── __init__.py
│   │   ├── sql_rewriter.py
│   │   ├── field_mapper.py
│   │   ├── template_tags.py
│   │   └── card_processor.py      # extracted from cards_menu.py
│   ├── menu_cli/
│   │   ├── _base.py               # NEW: shared show_menu + loop
│   │   ├── cards_menu.py          # ~150 LOC
│   │   └── ...
│   └── utils/                     # input_utils, icons, format_time, print_* unchanged
├── tests/
│   ├── __init__.py
│   ├── test_sql_rewriter.py
│   ├── test_field_mapper.py
│   ├── test_template_tags.py
│   ├── test_project_config.py
│   └── test_http_client.py
└── main.py                        # configures root logger
```

## Component contracts

### `src/config/project_config.py`

```python
@dataclass(frozen=True)
class ProjectConfig:
    short_code: str           # "sr", "nw", "bl"
    display_name: str         # "Sword Rouge Lite"
    table_mapping: dict[str, str]
    rename: dict[str, str]

class ProjectRegistry:
    @classmethod
    def load(cls, projects_dir: Path) -> "ProjectRegistry": ...
    def get(self, short_code: str) -> ProjectConfig | None: ...
    def all(self) -> list[ProjectConfig]: ...
    @property
    def ignored_tables(self) -> set[str]: ...
    @property
    def spec_tables(self) -> set[str]: ...
```

Loader validates: `short_code` unique across files; required keys present; no Python eval.

### `src/mapping/sql_rewriter.py`

```python
def rewrite_query(
    query: str,
    table_mapping: Mapping[str, str],
    *,
    rename: Mapping[str, str],
    spec_tables: Set[str],
) -> tuple[str, bool]:
    """Returns (new_query, db_changed). Same behavior as old replace_table_names_in_query."""
```

Pure function. No globals. No prints — uses `logger.debug`/`info`. Helpers (`_flatten_redundant_subqueries`, `_replace_table_names`, `_strip_aliases`) become private functions.

### `src/mapping/field_mapper.py`

```python
def map_field_ids_by_table(
    old_fields: Sequence[Field],
    new_fields: Sequence[Field],
    old_table_id: int,
    new_table_id: int,
) -> dict[int, int]: ...

def build_global_field_mapping(
    old_db_id: int,
    new_db_id: int,
    tables_old: Sequence[Table],
    tables_new: Sequence[Table],
    fields_old: Sequence[Field],
    fields_new: Sequence[Field],
    table_mapping: Mapping[str, str],
) -> dict[int, int]: ...

def find_new_table_id(
    old_table_id: int,
    tables_old: Sequence[Table],
    tables_new: Sequence[Table],
    table_mapping: Mapping[str, str],
    cache: dict[int, int | None] | None = None,
) -> int | None: ...
```

Cache is a parameter, not a module global. Caller owns it.

### `src/mapping/template_tags.py`

`remap_template_tags_in`, `remove_unmapped_template_tags`, `remap_template_tags_with_table_fallback` — moved verbatim, prints replaced with logger.

### `src/mapping/card_processor.py`

`process_card`, `special_process_card`, `remap_field_ids` — pulled out of `cards_menu.py`. Take `ProjectConfig` instead of raw `table_mapping`/`rename` args.

### `src/http/client.py`

```python
class MetabaseClient:
    def __init__(
        self,
        base_url: str,
        api_token: str,
        *,
        auth_type: Literal["api_key", "session"] = "api_key",
        timeout: float = 30.0,
        max_retries: int = 3,
    ): ...

    def get(self, path: str, *, params: dict | None = None) -> requests.Response: ...
    def post(self, path: str, *, json: dict | None = None, params: dict | None = None) -> requests.Response: ...
    def put(self, path: str, *, json: dict | None = None, params: dict | None = None) -> requests.Response: ...
    def delete(self, path: str, *, params: dict | None = None) -> requests.Response: ...
```

Internals: `requests.Session` with `HTTPAdapter(max_retries=Retry(total=3, backoff_factor=0.5, status_forcelist=[429,500,502,503,504]))`. Headers set once on session. `path` is appended to `base_url`.

API classes (`CardAPI`, etc.) take `client: MetabaseClient` + `resource: str` (e.g. `"card"`), drop `set_self_url`/`get_self_url`/`try-finally`.

### `src/menu_cli/_base.py`

```python
def show_menu(title: str, options: list[str]) -> str: ...

def run_menu_loop(title: str, actions: dict[str, tuple[str, Callable[[], None]]]) -> None:
    """actions = {'1': ('Label', handler), ...}. 'b' or '0' exits."""
```

Each `*_menu.py` declares its action dict, drops repeated `while True` boilerplate.

## Logging

- `main.py` calls `logging.basicConfig(level=os.environ.get("METABASE_CLI_LOG", "INFO"), format="%(asctime)s %(levelname)s %(name)s: %(message)s")`.
- All `print('[PROCESS] ...')` debug lines in `card_processor.py` → `logger.debug`.
- All `log(...)` closures in `mapping.py` → module-level `logger.info`/`warning`.
- Menu prints (`'📦 Metabase CLI Tool'`, `'✅ Updated successfully.'`) stay as `print()` — they're TTY UI.

## Tooling

`pyproject.toml`:
```toml
[project.optional-dependencies]
dev = ["pytest>=8", "pytest-cov>=5", "ruff>=0.6", "mypy>=1.11", "types-requests", "types-PyYAML"]

[tool.ruff]
line-length = 100
target-version = "py311"

[tool.ruff.lint]
select = ["E", "F", "I", "UP", "B", "SIM", "RUF"]

[tool.ruff.format]
quote-style = "single"
indent-style = "space"

[tool.mypy]
python_version = "3.11"
strict = true
files = ["src", "core"]

[tool.pytest.ini_options]
testpaths = ["tests"]
addopts = "-q"
```

`.pre-commit-config.yaml`: drop yapf + isort; add `astral-sh/ruff-pre-commit` with `ruff` and `ruff-format` hooks. Keep detect-secrets, trailing-whitespace, check-yaml.

## Test plan

| Test file | Coverage |
| --- | --- |
| `test_sql_rewriter.py` | subquery flattening, exact-backtick table replace, alias removal preserves `dd`, spec_table triggers rename + sets `db_changed=True`, no-op when no match |
| `test_field_mapper.py` | case-insensitive match, missing fields collected, full + short name fallback in `find_new_table_id`, cache parameter respected |
| `test_template_tags.py` | direct mapping wins over fallback, date field fallback picks priority name, unmapped tag triggers warning but is kept |
| `test_project_config.py` | loads all YAML files, duplicate short_code raises, missing required key raises, YAML parse error has clear message |
| `test_http_client.py` | retry on 503 with mocked adapter, timeout passed to request, auth header set, path joining handles trailing slashes |

Mock `requests` via `responses` or `pytest-mock`; no live network calls.

## Migration order

Each step ships as a commit. Tests run after each.

1. **Tooling** — `pyproject.toml`, `.pre-commit-config.yaml`, `tests/__init__.py`. No source changes.
2. **`mapping/sql_rewriter.py`** — extract pure function + tests. Old `replace_table_names_in_query` re-exports it for one commit, then callers updated.
3. **`mapping/field_mapper.py`** — extract `map_field_ids_by_table_id`. Same shim approach.
4. **`config/project_config.py` + `core/projects/*.yaml`** — load tables from YAML. `cards_menu.py` uses `ProjectRegistry` instead of `TABLE_MAPPING_BY_KEY`.
5. **`http/client.py`** — new client. Migrate `base_api_class.py` and each `*_api.py` to use it; remove `set_self_url`/`get_self_url`. One API per commit.
6. **`mapping/card_processor.py`** — move `process_card` + helpers out of `cards_menu.py`.
7. **`mapping/template_tags.py`** — move template-tag helpers.
8. **`menu_cli/_base.py`** — extract shared loop; refactor each menu.
9. **Logging swap + typo fixes** — `print` → `logger` in `src/`; `fs_timline_event` → `fs_timeline_event`; signature fix on `rewrite_query`.
10. **`src/utils/mapping.py` deleted** — confirm no remaining imports.
11. **README update** — new layout, running tests, log env var.

## Risks + mitigations

| Risk | Mitigation |
| --- | --- |
| API behavior drift in card update | All processor logic preserved; tests cover SQL rewrite + field mapping pure functions. Dry-run mode in `update_cards` stays. |
| YAML mapping load failure crashes CLI | `ProjectRegistry.load` validates at startup; clear error before menu shown. |
| Retry causes duplicate POST/PUT against Metabase | `Retry(allowed_methods=frozenset(["GET", "HEAD", "OPTIONS"]))` — retries only safe methods. |
| Logging spam under default `INFO` | Card processor debug prints moved to `logger.debug` (off by default). |
| `mypy --strict` floods errors on first run | Apply per-module; allow `# type: ignore[...]` with reason where typing third-party JSON dicts is infeasible. |

## Out-of-scope follow-ups (do not include)

- Replace `requests` with `httpx` async client
- Persist `TABLE_ID_CACHE` between CLI runs
- Add a `metabase-cli` console_script entry point
- Containerize (Dockerfile)
