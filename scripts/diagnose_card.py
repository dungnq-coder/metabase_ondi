"""One-shot diagnostic: fetch a card by ID and dry-run the rewriter.

Usage:
  python scripts/diagnose_card.py <CARD_ID> [TARGET_SHORT] [--source SOURCE_SHORT]

Prints:
  - query_type, source_card_id, database_id
  - dataset_query structure
  - every SQL string found (top native + staged native)
  - which mapping keys appear in each SQL
  - char counts (ASCII vs smart-quote backticks)
  - unified diff of rewriter output
"""

from __future__ import annotations

import difflib
import sys
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parent.parent
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

from src.config.base_config import BaseConfig  # noqa: E402
from src.config.project_config import ProjectRegistry  # noqa: E402
from src.connector.manager import MetabaseAPIManager  # noqa: E402
from src.mapping.sql_rewriter import rewrite_query  # noqa: E402

PROJECTS_DIR = Path(__file__).resolve().parent.parent / 'core' / 'projects'


def _short_db_code(name: str) -> str:
    return ''.join(w[0].lower() for w in name.split() if w)


def _collect_sql_locations(dq: dict) -> list[tuple[str, str]]:
    """Return [(location_label, sql_string), ...] for every SQL string in the card."""
    found: list[tuple[str, str]] = []
    native = dq.get('native') or {}
    for key in ('query', 'native'):
        v = native.get(key)
        if isinstance(v, str) and v.strip():
            found.append((f'dataset_query.native.{key}', v))
    for idx, st in enumerate(dq.get('stages') or []):
        if not isinstance(st, dict):
            continue
        for key in ('native', 'query'):
            v = st.get(key)
            if isinstance(v, str) and v.strip():
                found.append((f'dataset_query.stages[{idx}].{key}', v))
    return found


def _parse_args(argv: list[str]) -> tuple[int, str, str | None]:
    if len(argv) < 2:
        print(
            'usage: python scripts/diagnose_card.py <CARD_ID> [TARGET_SHORT] '
            '[--source SOURCE_SHORT]'
        )
        sys.exit(2)
    card_id = int(argv[1])
    target_short = 'fs'
    force_source: str | None = None
    i = 2
    while i < len(argv):
        if argv[i] == '--source' and i + 1 < len(argv):
            force_source = argv[i + 1]
            i += 2
        else:
            target_short = argv[i]
            i += 1
    return card_id, target_short, force_source


def main() -> None:
    card_id, target_short, force_source = _parse_args(sys.argv)

    cfg = BaseConfig()
    m = MetabaseAPIManager(api_token=cfg.api_token, base_url=cfg.base_url)
    card = m.card.get_card_detail(card_id)
    print(f'=== Card {card_id}: {card.get("name")!r} ===')
    print(f'  query_type     : {card.get("query_type")}')
    print(f'  source_card_id : {card.get("source_card_id")}')
    print(f'  database_id    : {card.get("database_id")}')
    print(f'  table_id       : {card.get("table_id")}')

    db_id = card.get('database_id')
    db_name = ''
    if db_id is not None:
        db_name = m.database.get_database_detail(database_id=db_id).json().get('name', '')
    raw_short = _short_db_code(str(db_name))
    registry = ProjectRegistry.load(PROJECTS_DIR)
    detected_source = registry.resolve_short_code(raw_short)
    source_short = force_source or detected_source
    print(f'  source DB name : {db_name!r}')
    print(f'  computed short : {raw_short!r} -> auto-resolved {detected_source!r}')
    if force_source:
        print(f'  FORCED source  : {force_source!r}')
    print(f'  target short   : {target_short!r}')

    dq = card.get('dataset_query', {}) or {}
    print(f'  dataset_query keys: {list(dq.keys())}')

    if source_short is None:
        print('ABORT: source DB short_code not in registry. Pass --source <code> to override.')
        return
    res = registry.resolve(source_short, target_short)
    print(f'  mapping size   : {len(res.table_mapping)} table entries')

    sql_locations = _collect_sql_locations(dq)
    if not sql_locations:
        print('NOTE: no native SQL strings found anywhere in dataset_query.')
        print(f'Full dataset_query repr: {dq!r}')
        return

    for label, sql in sql_locations:
        print(f'\n========== {label} ({len(sql)} chars) ==========')
        print('--- repr (first 800 chars) ---')
        print(repr(sql[:800]))
        print('--- mapping keys present ---')
        any_hit = False
        for k in res.table_mapping:
            if f'`{k}`' in sql:
                print(f'  HIT (backticked)   {k}')
                any_hit = True
            elif k in sql:
                print(f'  HIT (no backticks) {k}')
                any_hit = True
        if not any_hit:
            print('  (none)')
        backtick_count = sql.count('`')
        smart_left = sql.count('‘')
        smart_right = sql.count('’')
        smart_grave = sql.count('ˋ')
        print(
            f'--- chars: ASCII `=={backtick_count}, U+2018={smart_left}, '
            f'U+2019={smart_right}, U+02CB={smart_grave} ---'
        )

        new_sql, db_changed = rewrite_query(
            sql, res.table_mapping, rename=res.rename, spec_tables=registry.spec_tables
        )
        print(f'--- rewriter output (db_changed={db_changed}) ---')
        if sql == new_sql:
            print('NO CHANGES.')
        else:
            for line in difflib.unified_diff(
                sql.splitlines(keepends=True),
                new_sql.splitlines(keepends=True),
                fromfile='before',
                tofile='after',
                n=1,
            ):
                sys.stdout.write(line)


if __name__ == '__main__':
    main()
