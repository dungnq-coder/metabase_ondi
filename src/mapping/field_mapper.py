"""Map field IDs between two Metabase databases (old -> new)."""

from __future__ import annotations

import logging
from collections.abc import Mapping, Sequence
from typing import Any

logger = logging.getLogger(__name__)

# Field/Table are loosely-typed JSON dicts from the Metabase API.
Field = dict[str, Any]
Table = dict[str, Any]
TableCache = dict[int, int | None]


def _index_by_table(fields: Sequence[Field]) -> dict[int, list[Field]]:
    """Group fields by `table_id` in one O(N) pass."""
    out: dict[int, list[Field]] = {}
    for f in fields:
        tid = f.get('table_id')
        if tid is not None:
            out.setdefault(tid, []).append(f)
    return out


def map_field_ids_by_table(
    old_fields: Sequence[Field],
    new_fields: Sequence[Field],
    old_table_id: int,
    new_table_id: int,
) -> dict[int, int]:
    """Match fields by name (case-insensitive) between two tables.

    Returns: {old_field_id: new_field_id}. Logs any unmatched old-side fields.
    """
    return _map_one_table(
        [f for f in old_fields if f['table_id'] == old_table_id],
        [f for f in new_fields if f['table_id'] == new_table_id],
        old_table_id,
        new_table_id,
    )


def _map_one_table(
    old_in_table: Sequence[Field],
    new_in_table: Sequence[Field],
    old_table_id: int,
    new_table_id: int,
) -> dict[int, int]:
    new_by_name = {f['name'].lower(): f['id'] for f in new_in_table}

    mapping: dict[int, int] = {}
    not_found: list[str] = []
    for old in old_in_table:
        new_id = new_by_name.get(old['name'].lower())
        if new_id is not None:
            mapping[old['id']] = new_id
        else:
            not_found.append(old['name'])

    logger.info(
        'Mapped %d/%d fields for table %s -> %s',
        len(mapping),
        len(old_in_table),
        old_table_id,
        new_table_id,
    )
    if not_found:
        logger.warning(
            'Fields not found in new table %s (%d): %s',
            new_table_id,
            len(not_found),
            ', '.join(not_found),
        )
    return mapping


def find_new_table_id(
    old_table_id: int,
    old_tables: Sequence[Table],
    new_tables: Sequence[Table],
    table_mapping: Mapping[str, str],
    cache: TableCache | None = None,
) -> int | None:
    """Resolve the new-DB table_id matching an old-DB table_id.

    Lookup order:
      1. cache hit (caller-owned)
      2. exact full-name match in `table_mapping`
      3. short-name fallback (last dotted segment)
      4. if no mapping, use the old table's short name verbatim
    """
    if cache is not None and old_table_id in cache:
        return cache[old_table_id]

    old_table = next((t for t in old_tables if t.get('table_id') == old_table_id), None)
    if old_table is None:
        if cache is not None:
            cache[old_table_id] = None
        return None

    old_full = old_table.get('table_name', '')
    old_short = old_full.split('.')[-1]

    mapped_full = table_mapping.get(old_full)
    if mapped_full is None:
        mapped_full = next(
            (
                new_full
                for full_old, new_full in table_mapping.items()
                if full_old.split('.')[-1] == old_short
            ),
            None,
        )
    target_short = mapped_full.split('.')[-1] if mapped_full else old_short

    new_table = next(
        (t for t in new_tables if t.get('table_name', '').split('.')[-1] == target_short),
        None,
    )
    new_id = new_table.get('table_id') if new_table else None
    if cache is not None:
        cache[old_table_id] = new_id
    return new_id


def build_global_field_mapping(
    old_tables: Sequence[Table],
    new_tables: Sequence[Table],
    old_fields: Sequence[Field],
    new_fields: Sequence[Field],
    table_mapping: Mapping[str, str],
    cache: TableCache | None = None,
) -> dict[int, int]:
    """Build {old_field_id: new_field_id} across all tables in the DB.

    Indexes fields by `table_id` once up front so each table lookup is O(1),
    avoiding the O(N_fields x N_tables) re-scan in the per-table call path.
    """
    old_by_table = _index_by_table(old_fields)
    new_by_table = _index_by_table(new_fields)

    global_mapping: dict[int, int] = {}
    for old_table in old_tables:
        old_id = old_table['table_id']
        new_table_id = find_new_table_id(
            old_id, old_tables, new_tables, table_mapping, cache=cache
        )
        if new_table_id is None:
            continue
        global_mapping.update(
            _map_one_table(
                old_by_table.get(old_id, []),
                new_by_table.get(new_table_id, []),
                old_id,
                new_table_id,
            )
        )
    logger.info('Global field mapping built: %d fields', len(global_mapping))
    return global_mapping
