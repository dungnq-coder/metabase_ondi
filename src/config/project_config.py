"""Load and validate per-project YAML mapping configs."""

from __future__ import annotations

import logging
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import yaml

logger = logging.getLogger(__name__)

GLOBAL_FILENAME = '_global.yaml'
_REQUIRED_KEYS = ('short_code', 'display_name', 'table_mapping')


class ProjectConfigError(ValueError):
    """Raised when a project YAML file is missing or malformed."""


@dataclass(frozen=True)
class ProjectConfig:
    short_code: str
    display_name: str
    table_mapping: dict[str, str]
    rename: dict[str, str]
    short_code_aliases: frozenset[str] = frozenset()


@dataclass(frozen=True)
class GlobalConfig:
    ignored_tables: frozenset[str]
    spec_tables: frozenset[str]
    pivot_short_code: str = 'fs'


@dataclass(frozen=True)
class ResolvedMapping:
    """Concrete (source -> target) mapping produced by ProjectRegistry.resolve()."""

    table_mapping: dict[str, str]
    rename: dict[str, str]


class ProjectRegistry:
    """Holds all per-project configs plus shared globals."""

    def __init__(self, projects: dict[str, ProjectConfig], globals_: GlobalConfig):
        self._projects = projects
        self._globals = globals_
        self._alias_index: dict[str, str] = {}
        for project in projects.values():
            for alias in project.short_code_aliases:
                normalized = alias.lower()
                existing = self._alias_index.get(normalized)
                if existing and existing != project.short_code:
                    raise ProjectConfigError(
                        f"Alias {alias!r} maps to both {existing!r} and {project.short_code!r}"
                    )
                self._alias_index[normalized] = project.short_code

    @classmethod
    def load(cls, projects_dir: Path) -> ProjectRegistry:
        if not projects_dir.is_dir():
            raise ProjectConfigError(f'Projects directory not found: {projects_dir}')

        globals_ = _load_globals(projects_dir / GLOBAL_FILENAME)

        projects: dict[str, ProjectConfig] = {}
        for path in sorted(projects_dir.glob('*.yaml')):
            if path.name == GLOBAL_FILENAME:
                continue
            project = _load_project(path)
            if project.short_code in projects:
                raise ProjectConfigError(f"Duplicate short_code '{project.short_code}' in {path}")
            projects[project.short_code] = project
            logger.info('Loaded project config: %s (%s)', project.short_code, path.name)

        return cls(projects, globals_)

    def get(self, short_code: str) -> ProjectConfig | None:
        return self._projects.get(short_code)

    def resolve_short_code(self, candidate: str) -> str | None:
        """Map a candidate code (or alias) to a known project short_code.

        Lookup order: exact short_code match, then alias index.
        """
        if candidate in self._projects:
            return candidate
        return self._alias_index.get(candidate.lower())

    def all(self) -> list[ProjectConfig]:
        return list(self._projects.values())

    @property
    def ignored_tables(self) -> frozenset[str]:
        return self._globals.ignored_tables

    @property
    def spec_tables(self) -> frozenset[str]:
        return self._globals.spec_tables

    @property
    def pivot_short_code(self) -> str:
        return self._globals.pivot_short_code

    def resolve(self, source_short: str, target_short: str) -> ResolvedMapping:
        """Build a (source -> target) table_mapping + rename.

        All per-project YAML files declare entries as `pivot -> project`.
        This method composes/inverts those to yield any direction:

          - source == target            : empty (identity, no rewrite needed)
          - source == pivot             : target.forward
          - target == pivot             : invert(source.forward)
          - otherwise                   : compose(invert(source), target.forward)
        """
        if source_short == target_short:
            return ResolvedMapping({}, {})

        pivot = self._globals.pivot_short_code
        source = self.get(source_short)
        target = self.get(target_short)
        if source is None:
            raise ProjectConfigError(f'Unknown source short_code: {source_short!r}')
        if target is None:
            raise ProjectConfigError(f'Unknown target short_code: {target_short!r}')

        if source_short == pivot:
            return ResolvedMapping(dict(target.table_mapping), dict(target.rename))
        if target_short == pivot:
            return ResolvedMapping(_invert(source.table_mapping), _invert(source.rename))
        return ResolvedMapping(
            _compose(_invert(source.table_mapping), target.table_mapping),
            _compose(_invert(source.rename), target.rename),
        )


def _read_yaml(path: Path) -> dict[str, Any]:
    try:
        with path.open('r', encoding='utf-8') as fh:
            data = yaml.safe_load(fh)
    except FileNotFoundError as e:
        raise ProjectConfigError(f'Config file not found: {path}') from e
    except yaml.YAMLError as e:
        raise ProjectConfigError(f"YAML parse error in '{path}': {e}") from e
    if data is None:
        return {}
    if not isinstance(data, dict):
        raise ProjectConfigError(f'Top-level of {path} must be a mapping')
    return data


def _load_globals(path: Path) -> GlobalConfig:
    if not path.exists():
        return GlobalConfig(frozenset(), frozenset())
    data = _read_yaml(path)
    return GlobalConfig(
        ignored_tables=frozenset(data.get('ignored_tables', []) or []),
        spec_tables=frozenset(data.get('spec_tables', []) or []),
        pivot_short_code=str(data.get('pivot_short_code', 'fs')),
    )


def _invert(d: dict[str, str]) -> dict[str, str]:
    """Swap keys/values. On duplicate values, last write wins."""
    return {v: k for k, v in d.items()}


def _compose(a: dict[str, str], b: dict[str, str]) -> dict[str, str]:
    """Return {x: b[y]} for every x -> y in a where y is a key in b."""
    return {x: b[y] for x, y in a.items() if y in b}


def _load_project(path: Path) -> ProjectConfig:
    data = _read_yaml(path)
    missing = [k for k in _REQUIRED_KEYS if k not in data]
    if missing:
        raise ProjectConfigError(f'{path}: missing required keys: {missing}')
    aliases_raw = data.get('short_code_aliases') or []
    if not isinstance(aliases_raw, list):
        raise ProjectConfigError(f'{path}: short_code_aliases must be a list')
    return ProjectConfig(
        short_code=str(data['short_code']),
        display_name=str(data['display_name']),
        table_mapping=dict(data['table_mapping'] or {}),
        rename=dict(data.get('rename') or {}),
        short_code_aliases=frozenset(str(a).lower() for a in aliases_raw),
    )
