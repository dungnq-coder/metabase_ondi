"""Remap field IDs inside Metabase native-query `template-tags`.

Three strategies layered:
  1. `remap_template_tags_in`           — replace via given field_mapping.
  2. `remove_unmapped_template_tags`    — log unmapped tags, but keep them.
  3. `remap_template_tags_with_table_fallback` — full fallback chain
     (direct -> by table+name -> by global name -> date-field heuristic).
"""

from __future__ import annotations

import logging
import re
from collections.abc import Mapping, Sequence
from typing import Any

from src.mapping.field_mapper import (
    Field,
    Table,
    TableCache,
    find_new_table_id,
)

logger = logging.getLogger(__name__)


def remap_field_ids(obj: Any, field_mapping: Mapping[int, int]) -> Any:
    """Walk a Metabase MBQL fragment and remap `['field', <id>, ...]` refs."""
    if isinstance(obj, list):
        if len(obj) >= 2 and obj[0] == 'field':
            field_idx = next(
                (idx for idx in range(1, len(obj)) if isinstance(obj[idx], int)),
                None,
            )
            if field_idx is not None:
                old_id = obj[field_idx]
                new_id = field_mapping.get(old_id, old_id)
                return [
                    'field'
                    if i == 0
                    else (new_id if i == field_idx else remap_field_ids(item, field_mapping))
                    for i, item in enumerate(obj)
                ]
        return [remap_field_ids(item, field_mapping) for item in obj]
    if isinstance(obj, dict):
        return {k: remap_field_ids(v, field_mapping) for k, v in obj.items()}
    return obj


def remap_template_tags_in(obj: Any, field_mapping: Mapping[int, int]) -> Any:
    """Find every `template-tags` dict and remap any `dimension` field refs."""
    if isinstance(obj, dict):
        for k, v in obj.items():
            if k == 'template-tags' and isinstance(v, dict):
                for tag_info in v.values():
                    if isinstance(tag_info, dict) and 'dimension' in tag_info:
                        tag_info['dimension'] = remap_field_ids(
                            tag_info['dimension'], field_mapping
                        )
            else:
                remap_template_tags_in(v, field_mapping)
    elif isinstance(obj, list):
        for item in obj:
            remap_template_tags_in(item, field_mapping)
    return obj


def remove_unmapped_template_tags(obj: Any, field_mapping: Mapping[int, int]) -> Any:
    """Remap template-tag dimensions where possible; log (but keep) unmapped ones."""
    if not isinstance(obj, dict):
        return obj

    tags = obj.get('template-tags')
    if isinstance(tags, dict):
        for tag_name, tag_info in tags.items():
            if not (isinstance(tag_info, dict) and 'dimension' in tag_info):
                continue
            dim = tag_info['dimension']
            if not isinstance(dim, list):
                continue
            field_idx = next(
                (idx for idx in range(1, len(dim)) if isinstance(dim[idx], int)),
                None,
            )
            if field_idx is None:
                continue
            old_id = dim[field_idx]
            new_id = field_mapping.get(old_id)
            if new_id and new_id != old_id:
                dim[field_idx] = new_id
            else:
                logger.warning("Template tag '%s' keeps unmapped field id %s", tag_name, old_id)

    for v in obj.values():
        if isinstance(v, dict):
            remove_unmapped_template_tags(v, field_mapping)
        elif isinstance(v, list):
            for item in v:
                if isinstance(item, dict):
                    remove_unmapped_template_tags(item, field_mapping)
    return obj


def _normalize_name(value: Any) -> str | None:
    if not value:
        return None
    return str(value).strip().strip('`').lower()


def _alias_candidates(value: Any) -> list[str]:
    if not value:
        return []
    raw = str(value).strip().replace('`', '')
    candidates: list[str] = []
    last = raw.split('.')[-1].strip()
    if last:
        candidates.append(last.lower())
    candidates.extend(m.lower() for m in re.findall(r'([A-Za-z_][A-Za-z0-9_]*)', raw))
    return candidates


def _candidate_names_for_tag(
    tag_name: str, tag_info: dict[str, Any], old_field: Field | None
) -> list[str]:
    candidates: list[str] = []

    def add(value: Any) -> None:
        normalized = _normalize_name(value)
        if normalized:
            candidates.append(normalized)

    if old_field:
        add(old_field.get('name'))
        add(old_field.get('display_name'))
        for alias in _alias_candidates(old_field.get('nfc_path')):
            add(alias)

    add(tag_info.get('name'))
    add(tag_info.get('display-name'))
    for alias in _alias_candidates(tag_info.get('alias')):
        add(alias)
    add(tag_name)

    base_type = None
    effective_type = None
    dimension = tag_info.get('dimension')
    if isinstance(dimension, list):
        for item in dimension:
            if isinstance(item, dict):
                base_type = item.get('base-type') or base_type
                effective_type = item.get('effective-type') or effective_type

    widget_type = (tag_info.get('widget-type') or '').lower()
    type_signals = (
        base_type,
        effective_type,
        old_field.get('name') if old_field else None,
        tag_name,
        tag_info.get('display-name'),
    )
    is_date_like = 'date' in widget_type or any(
        v and 'date' in str(v).lower() for v in type_signals
    )
    if is_date_like:
        candidates.extend(
            ['date', 'event_date', 'created_date', 'created_at', 'install_date', 'transaction_date']
        )

    seen: set[str] = set()
    ordered: list[str] = []
    for c in candidates:
        if c not in seen:
            seen.add(c)
            ordered.append(c)
    return ordered


def _is_date_field(field: Field) -> bool:
    if not isinstance(field, dict):
        return False
    for key in ('name', 'display_name', 'base_type', 'effective_type', 'semantic_type'):
        if field.get(key) and 'date' in str(field[key]).lower():
            return True
    return False


def _pick_date_field_fallback(
    new_fields: Sequence[Field], new_table_id: int, candidate_names: Sequence[str]
) -> int | None:
    table_date_fields = [
        f
        for f in new_fields
        if isinstance(f, dict) and f.get('table_id') == new_table_id and _is_date_field(f)
    ]
    if not table_date_fields:
        return None
    priority = [_normalize_name(n) for n in candidate_names] + [
        'date',
        'event_date',
        'created_date',
        'created_at',
    ]
    for name in priority:
        if not name:
            continue
        for f in table_date_fields:
            if _normalize_name(f.get('name')) == name:
                return f.get('id')
    if len(table_date_fields) == 1:
        return table_date_fields[0].get('id')
    for f in table_date_fields:
        if _normalize_name(f.get('name')) in {'date', 'event_date', 'created_date'}:
            return f.get('id')
    return None


def _infer_target_table_ids(
    dataset_query: dict[str, Any], new_tables: Sequence[Table]
) -> list[int]:
    sql_chunks: list[str] = []
    native = dataset_query.get('native')
    if isinstance(native, dict):
        sql_chunks.extend(
            v for v in (native.get('query'), native.get('native')) if isinstance(v, str)
        )
    for stage in dataset_query.get('stages') or []:
        if not isinstance(stage, dict):
            continue
        for key in ('native', 'query'):
            v = stage.get(key)
            if isinstance(v, str):
                sql_chunks.append(v)

    table_ids: list[int] = []
    seen: set[int] = set()
    for sql in sql_chunks:
        for name in re.findall(r'`([^`]+)`', sql):
            matched = next(
                (
                    t
                    for t in new_tables
                    if t.get('table_name') == name
                    or t.get('table_name', '').split('.')[-1] == name.split('.')[-1]
                ),
                None,
            )
            if matched and matched.get('table_id') and matched['table_id'] not in seen:
                seen.add(matched['table_id'])
                table_ids.append(matched['table_id'])
    return table_ids


def remap_template_tags_with_table_fallback(
    dataset_query: dict[str, Any],
    field_mapping: dict[int, int],
    old_fields: Sequence[Field],
    new_fields: Sequence[Field],
    old_tables: Sequence[Table],
    new_tables: Sequence[Table],
    table_mapping: Mapping[str, str],
    table_id_cache: TableCache | None = None,
) -> list[tuple[str, int, list[str]]]:
    """Strong remap with fallbacks. Returns list of (tag_name, old_id, candidates) for unresolved tags."""
    if not isinstance(dataset_query, dict):
        return []

    old_field_by_id = {f.get('id'): f for f in old_fields if isinstance(f, dict)}
    inferred_targets = _infer_target_table_ids(dataset_query, new_tables)
    new_field_by_table_name = {
        (f.get('table_id'), _normalize_name(f.get('name'))): f.get('id')
        for f in new_fields
        if isinstance(f, dict)
    }
    new_field_by_name: dict[str, int] = {}
    for f in new_fields:
        if not isinstance(f, dict):
            continue
        fid = f.get('id')
        if fid is None:
            continue
        for key in (f.get('name'), f.get('display_name'), f.get('semantic_type')):
            n = _normalize_name(key)
            if n and n not in new_field_by_name:
                new_field_by_name[n] = fid

    unresolved: list[tuple[str, int, list[str]]] = []

    def walk(obj: Any) -> None:
        if isinstance(obj, dict):
            for k, v in obj.items():
                if k == 'template-tags' and isinstance(v, dict):
                    for tag_name, tag_info in v.items():
                        _process_tag(tag_name, tag_info)
                else:
                    walk(v)
        elif isinstance(obj, list):
            for item in obj:
                walk(item)

    def _process_tag(tag_name: str, tag_info: Any) -> None:
        if not isinstance(tag_info, dict):
            return
        dim = tag_info.get('dimension')
        if not (isinstance(dim, list) and len(dim) >= 2 and dim[0] == 'field'):
            return
        field_idx = next((idx for idx in range(1, len(dim)) if isinstance(dim[idx], int)), None)
        if field_idx is None:
            return

        old_id = dim[field_idx]
        new_id = field_mapping.get(old_id)
        old_field = old_field_by_id.get(old_id)
        candidate_names = _candidate_names_for_tag(tag_name, tag_info, old_field)

        if not new_id and old_field:
            old_table_id = old_field.get('table_id')
            new_table_id = (
                find_new_table_id(
                    old_table_id, old_tables, new_tables, table_mapping, cache=table_id_cache
                )
                if old_table_id
                else None
            )
            if new_table_id:
                for cand in candidate_names:
                    new_id = new_field_by_table_name.get((new_table_id, cand))
                    if new_id:
                        break
                if not new_id:
                    new_id = _pick_date_field_fallback(new_fields, new_table_id, candidate_names)
        elif not new_id and len(inferred_targets) == 1:
            new_id = _pick_date_field_fallback(new_fields, inferred_targets[0], candidate_names)

        if not new_id:
            for cand in candidate_names:
                new_id = new_field_by_name.get(cand)
                if new_id:
                    break

        if new_id:
            dim[field_idx] = new_id
            field_mapping[old_id] = new_id
        else:
            unresolved.append((tag_name, old_id, candidate_names))

    walk(dataset_query)
    return unresolved
