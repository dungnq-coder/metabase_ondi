"""SQL query rewriter for cross-project Metabase migrations."""

from __future__ import annotations

import logging
import re
from collections.abc import Mapping, Set

logger = logging.getLogger(__name__)

_SUBQUERY_RE = re.compile(
    r'FROM\s*\(\s*SELECT\s*\*\s*FROM\s*(`[^`]+`)\s*\)',
    re.IGNORECASE | re.DOTALL,
)
_ALIAS_RE = re.compile(r'\bAS\s+(`)(?!dd\1)[A-Za-z0-9_.]+?\1', re.IGNORECASE)


def _flatten_redundant_subqueries(query: str) -> str:
    new_query = query
    for match in _SUBQUERY_RE.findall(new_query):
        new_query = re.sub(
            r'FROM\s*\(\s*SELECT\s*\*\s*FROM\s*' + re.escape(match) + r'\s*\)',
            f'FROM {match}',
            new_query,
            flags=re.IGNORECASE | re.DOTALL,
        )
        logger.info('Simplified redundant subquery: %s', match)
    return new_query


def _replace_table_names(query: str, table_mapping: Mapping[str, str]) -> str:
    new_query = query
    for old_full, new_full in table_mapping.items():
        pattern = re.escape(f'`{old_full}`')
        if re.search(pattern, new_query):
            new_query = re.sub(pattern, f'`{new_full}`', new_query)
            logger.info('Replaced `%s` -> `%s`', old_full, new_full)
    return new_query


def _apply_rename_if_spec(
    query: str,
    rename: Mapping[str, str],
    spec_tables: Set[str],
) -> tuple[str, bool]:
    if not any(spec in query for spec in spec_tables):
        return query, False

    db_changed = False
    new_query = query
    logger.info('Query contains a spec_table; applying rename mapping')
    for old_str, new_str in rename.items():
        if old_str in new_query:
            new_query = new_query.replace(old_str, new_str)
            db_changed = True
            logger.info('Renamed text: %s -> %s', old_str, new_str)
    return new_query, db_changed


def _strip_aliases(query: str) -> str:
    if _ALIAS_RE.search(query):
        logger.info('Removed alias patterns like AS `alias` (kept `dd`)')
        return _ALIAS_RE.sub('', query)
    return query


def rewrite_query(
    query: str,
    table_mapping: Mapping[str, str],
    *,
    rename: Mapping[str, str],
    spec_tables: Set[str],
) -> tuple[str, bool]:
    """Rewrite a SQL query for a different Metabase project.

    Steps:
      1. Flatten redundant `FROM (SELECT * FROM table)` subqueries.
      2. Replace fully-qualified backticked table names per `table_mapping`.
      3. If query references any name in `spec_tables`, apply `rename` substitutions.
         The boolean return signals whether such a rename ran (caller usually
         interprets this as "database changed").
      4. Strip Metabase-style aliases `AS \\`x\\`` except the literal `dd`.

    Returns:
        (new_query, db_changed)
    """
    new_query = _flatten_redundant_subqueries(query)
    new_query = _replace_table_names(new_query, table_mapping)
    new_query, db_changed = _apply_rename_if_spec(new_query, rename, spec_tables)
    new_query = _strip_aliases(new_query)
    return new_query, db_changed
