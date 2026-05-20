"""Transform a Metabase card payload for use in a new database."""

from __future__ import annotations

import copy
import logging
from collections.abc import Mapping, Sequence
from typing import Any

from src.connector.manager import MetabaseAPIManager
from src.mapping.field_mapper import Table, TableCache, find_new_table_id
from src.mapping.sql_rewriter import rewrite_query
from src.mapping.template_tags import remap_field_ids

logger = logging.getLogger(__name__)


def special_process_card(
    manager: MetabaseAPIManager, card_detail: dict[str, Any]
) -> dict[str, Any]:
    """When a card embeds another card by id, retarget it to the new dashboard's copy."""
    updated = copy.deepcopy(card_detail)
    source_card_id = card_detail.get('source_card_id')
    if not source_card_id:
        return updated

    name = manager.card.get_card_detail(source_card_id).get('name')
    dashboard_id = card_detail.get('dashboard_id')

    for c in manager.card.list_all_cards():
        if (
            c['name'] == name
            and c['dashboard_id'] == dashboard_id
            and c['id'] != card_detail.get('id')
        ):
            updated['source_card_id'] = c['id']
            updated['dataset_query']['query']['source-table'] = f'card__{c["id"]}'
            break
    return updated


def _process_mbql_query(
    updated_card: dict[str, Any],
    dataset_query: dict[str, Any],
    global_field_mapping: Mapping[int, int],
    table_mapping: Mapping[str, str],
    old_tables: Sequence[Table],
    new_tables: Sequence[Table],
    table_id_cache: TableCache | None,
) -> dict[str, Any]:
    query = dataset_query.get('query') or dataset_query
    is_full_mbql = 'query' not in dataset_query

    old_table_id = None
    if isinstance(query, dict):
        old_table_id = query.get('source-table') or query.get('source-query', {}).get(
            'source-table'
        )
        if not old_table_id and isinstance(query.get('stages'), list):
            for st in query['stages']:
                if st.get('source-table'):
                    old_table_id = st['source-table']
                    break
    if not old_table_id:
        old_table_id = updated_card.get('table_id')

    if not (old_table_id and old_tables and new_tables):
        logger.debug('process_card: missing table data (table_id=%s)', old_table_id)
        return dataset_query

    new_table_id = find_new_table_id(
        old_table_id, old_tables, new_tables, table_mapping, cache=table_id_cache
    )
    if not new_table_id:
        logger.debug('process_card: no new_table_id for %s', old_table_id)
        return dataset_query

    sub_keys = ('breakout', 'aggregation', 'filter', 'expressions', 'order-by')

    if is_full_mbql:
        for idx, st in enumerate(query.get('stages', [])):
            if st.get('source-table') == old_table_id:
                st['source-table'] = new_table_id
            query['stages'][idx] = remap_field_ids(st, global_field_mapping)
        for key in sub_keys:
            if key in query:
                query[key] = remap_field_ids(query[key], global_field_mapping)
        updated_card['table_id'] = new_table_id
        dataset_query = query
    else:
        if query.get('source-query') is not None:
            query['source-query']['source-table'] = new_table_id
        else:
            query['source-table'] = new_table_id
        for key in sub_keys:
            if key in query:
                query[key] = remap_field_ids(query[key], global_field_mapping)
        dataset_query['query'] = query

    for md in updated_card.get('result_metadata') or []:
        if not isinstance(md, dict):
            continue
        if isinstance(md.get('field_ref'), list):
            md['field_ref'] = remap_field_ids(md['field_ref'], global_field_mapping)
        if md.get('table_id') == old_table_id:
            md['table_id'] = new_table_id

    return dataset_query


def _process_native_query(
    dataset_query: dict[str, Any],
    global_field_mapping: Mapping[int, int],
    table_mapping: Mapping[str, str],
    rename_mapping: Mapping[str, str],
    spec_tables: set[str] | frozenset[str],
) -> tuple[dict[str, Any], bool]:
    native = dataset_query.get('native')
    staged_native = None
    native_stage_idx = None
    sql_query: str | None = None
    location: tuple[str, int | None] = ('top', None)

    if native:
        sql_query = native.get('query') or native.get('native')
    else:
        for idx, st in enumerate(dataset_query.get('stages') or []):
            if st.get('lib/type') == 'mbql.stage/native' or 'native' in st:
                staged_native = st
                native_stage_idx = idx
                sql_query = st.get('native') or st.get('query')
                location = ('stage', idx)
                break

    change_db = False
    if sql_query:
        new_sql, change_db = rewrite_query(
            sql_query, table_mapping, rename=rename_mapping, spec_tables=spec_tables
        )
        if location[0] == 'top':
            assert native is not None
            if 'query' in native:
                native['query'] = new_sql
            else:
                native['native'] = new_sql
            dataset_query['native'] = native
        else:
            assert native_stage_idx is not None
            dataset_query.setdefault('stages', [])[native_stage_idx]['native'] = new_sql

    tags = (
        (native or {}).get('template-tags')
        if native
        else (staged_native or {}).get('template-tags')
    )
    for tag_info in tags.values() if isinstance(tags, dict) else []:
        dim = tag_info.get('dimension')
        if isinstance(dim, list) and len(dim) >= 2 and dim[0] == 'field':
            field_idx: int | None = next(
                (i for i in range(1, len(dim)) if isinstance(dim[i], int)), None
            )
            if field_idx is not None:
                old_id = dim[field_idx]
                dim[field_idx] = global_field_mapping.get(old_id, old_id)

    return dataset_query, change_db


def process_card(
    manager: MetabaseAPIManager,
    card_detail: dict[str, Any],
    global_field_mapping: Mapping[int, int],
    new_db_id: int,
    table_mapping: Mapping[str, str],
    rename_mapping: Mapping[str, str],
    spec_tables: set[str] | frozenset[str],
    old_tables: Sequence[Table] | None = None,
    new_tables: Sequence[Table] | None = None,
    table_id_cache: TableCache | None = None,
) -> dict[str, Any]:
    """Update a card payload to point at `new_db_id` with remapped tables/fields."""
    card_id = card_detail.get('id')
    logger.debug('Processing card %s (%s)', card_id, card_detail.get('name'))

    updated_card = copy.deepcopy(card_detail)
    dataset_query = updated_card.get('dataset_query', {})
    old_db_id = updated_card['database_id']

    updated_card['database_id'] = new_db_id
    dataset_query['database'] = new_db_id

    if updated_card.get('source_card_id'):
        try:
            updated_card = special_process_card(manager, updated_card)
        except Exception:
            logger.exception('special_process_card failed for %s', card_id)
        return updated_card

    query_type = updated_card.get('query_type')

    if query_type == 'query':
        dataset_query = _process_mbql_query(
            updated_card,
            dataset_query,
            global_field_mapping,
            table_mapping,
            old_tables or [],
            new_tables or [],
            table_id_cache,
        )
    elif query_type == 'native':
        dataset_query, change_db = _process_native_query(
            dataset_query,
            global_field_mapping,
            table_mapping,
            rename_mapping,
            spec_tables,
        )
        logger.debug('Native query change_db=%s', change_db)

    updated_card['dataset_query'] = dataset_query
    logger.debug('Card %s: db %s -> %s', card_id, old_db_id, updated_card['database_id'])
    return updated_card
