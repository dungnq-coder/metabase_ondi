"""Interactive menu for Metabase cards (list, view, update, delete)."""

from __future__ import annotations

import logging
from pathlib import Path
from typing import Any

import requests

from src.config.project_config import ProjectRegistry, ResolvedMapping
from src.connector.manager import MetabaseAPIManager
from src.mapping.card_processor import process_card
from src.mapping.field_mapper import build_global_field_mapping
from src.mapping.template_tags import (
    remap_template_tags_in,
    remap_template_tags_with_table_fallback,
    remove_unmapped_template_tags,
)
from src.menu_cli._base import confirm_and_delete, run_resource_menu
from src.utils.input_utils import input_int, input_str, input_yes_no
from src.utils.print_cards import print_card_details
from src.utils.screen_contact import clear_screen

logger = logging.getLogger(__name__)

# Keys safely accepted by the Metabase /api/card PUT endpoint.
ALLOWED_UPDATE_KEYS = frozenset(
    {
        'name',
        'dataset_query',
        'display',
        'description',
        'archived',
        'cache_ttl',
        'collection_id',
        'collection_position',
        'collection_preview',
        'dashboard_id',
        'dashboard_tab_id',
        'visualization_settings',
        'embedding_params',
        'embedding_type',
    }
)

_PROJECT_DIR = Path(__file__).resolve().parent.parent.parent / 'core' / 'projects'


def _short_db_code(db_name: str) -> str:
    return ''.join(word[0].lower() for word in db_name.split() if word)


def _list_cards(manager: MetabaseAPIManager) -> None:
    cards = manager.card.list_all_cards()
    clear_screen()
    print('📄 All Cards')
    print('=' * 60)
    for c in cards:
        print(f'[{c["id"]}] {c["name"]}')


def _view_card(manager: MetabaseAPIManager, cid: int) -> None:
    card = manager.card.get_card_detail(cid)
    clear_screen()
    print_card_details(card)
    input('🔙 Press Enter to return...')


def _create_card_placeholder() -> None:
    print('🔧 Create card → Function in development')
    input('🔙 Press Enter to return...')


def _select_card_ids(manager: MetabaseAPIManager) -> list[int] | None:
    print('=== 🔧 Update Cards Database/Table ===')
    print('1️⃣  Update ALL cards')
    print('2️⃣  Update cards in a specific collection')
    print('3️⃣  Update cards in a specific dashboard')
    print('4️⃣  Update specific card IDs (comma separated)')
    print('0️⃣  Cancel')

    choice = input_int('👉 Choose an option (0-4): ')
    if choice == 0 or choice is None:
        print('❌ Cancelled.')
        return None

    all_cards = manager.card.list_all_cards()
    if choice == 1:
        return [c['id'] for c in all_cards]
    if choice == 2:
        cid = input_int('Enter collection ID: ')
        return [c['id'] for c in all_cards if c.get('collection_id') == cid]
    if choice == 3:
        did = input_int('Enter dashboard ID: ')
        return [c['id'] for c in all_cards if c.get('dashboard_id') == did]
    if choice == 4:
        raw = input_str('Enter card IDs separated by comma: ') or ''
        return [int(s.strip()) for s in raw.split(',') if s.strip().isdigit()]
    print('❌ Invalid choice.')
    return None


def _resolve_target_db(
    manager: MetabaseAPIManager, sample_card_ids: list[int]
) -> tuple[int | None, str]:
    fallback_db = None
    for cid in sample_card_ids:
        card = manager.card.get_card_detail(cid)
        if card.get('database_id') is not None:
            fallback_db = card['database_id']
            break

    new_db = input_int('Enter new database ID (leave blank to keep current): ', allow_empty=True)
    if new_db is None:
        new_db = fallback_db
    if new_db is None:
        return None, ''

    detail = manager.database.get_database_detail(database_id=new_db).json()
    return new_db, str(detail.get('name', '')).strip()


def _db_short_code(
    manager: MetabaseAPIManager,
    db_id: int,
    db_name_cache: dict[int, str],
    registry: ProjectRegistry,
) -> str | None:
    """Look up Metabase DB name (cached), compute short code, resolve via registry aliases."""
    if db_id not in db_name_cache:
        detail = manager.database.get_database_detail(database_id=db_id).json()
        db_name_cache[db_id] = str(detail.get('name', '')).strip()
    return registry.resolve_short_code(_short_db_code(db_name_cache[db_id]))


def _collect_card_sql(card_detail: dict[str, Any]) -> str:
    """Concat every native SQL string in the card (top-level + every stage)."""
    dq = card_detail.get('dataset_query') or {}
    chunks: list[str] = []
    native = dq.get('native') or {}
    for key in ('query', 'native'):
        v = native.get(key)
        if isinstance(v, str):
            chunks.append(v)
    for stage in dq.get('stages') or []:
        if not isinstance(stage, dict):
            continue
        for key in ('native', 'query'):
            v = stage.get(key)
            if isinstance(v, str):
                chunks.append(v)
    return '\n'.join(chunks)


def _infer_source_from_sql(
    card_detail: dict[str, Any], registry: ProjectRegistry
) -> str | None:
    """When DB-based detection yields identity, infer source by scanning SQL.

    Counts how many of each project's target table names appear (backticked)
    in the card's SQL. Returns the short_code with the most hits, or None if
    no project's tables appear at all.
    """
    blob = _collect_card_sql(card_detail)
    if not blob:
        return None
    pivot = registry.pivot_short_code
    hits: dict[str, int] = {}
    for project in registry.all():
        if project.short_code == pivot:
            continue
        # `table_mapping` values are the project's own (non-pivot) table names.
        count = sum(1 for v in project.table_mapping.values() if f'`{v}`' in blob)
        if count > 0:
            hits[project.short_code] = count
    if not hits:
        return None
    best = max(hits, key=lambda k: hits[k])
    logger.info('Inferred source from SQL content: %s (hits=%s)', best, hits)
    return best


def _prompt_force_source(registry: ProjectRegistry) -> str | None:
    """Ask user whether to override source detection.

    Use case: a card whose `database_id` was already flipped to the target DB
    by a previous deep-copy. Auto-detection then returns target==source and
    yields an identity mapping that leaves stale table names untouched.
    """
    available = sorted(p.short_code for p in registry.all())
    raw = input_str(
        f'Force source short_code? (blank = auto-detect per card; available: {available}): ',
        required=False,
        allow_cancel=False,
    )
    if not raw:
        return None
    code = registry.resolve_short_code(raw.strip())
    if code is None:
        print(f'❌ Unknown short_code {raw!r}; falling back to auto-detect.')
        return None
    return code


def _process_and_send(
    manager: MetabaseAPIManager,
    cid: int,
    new_db_id: int,
    registry: ProjectRegistry,
    target_short: str,
    tables_cache: dict[int, list[dict[str, Any]]],
    fields_cache: dict[int, list[dict[str, Any]]],
    db_name_cache: dict[int, str],
    field_mapping_by_old_db: dict[int, dict[int, int]],
    resolved_by_old_db: dict[int, ResolvedMapping],
    dry_run: bool,
    forced_source: str | None = None,
) -> None:
    card_detail = manager.card.get_card_detail(cid)
    old_db_id_raw = card_detail.get('database_id')
    if old_db_id_raw is None:
        logger.warning('Card %s has no database_id; skipping', cid)
        return
    old_db_id: int = int(old_db_id_raw)

    for db_id in (old_db_id, new_db_id):
        if db_id not in tables_cache:
            try:
                tables_cache[db_id] = manager.database.get_all_table_in_specific_db(db_id)
            except Exception:
                tables_cache[db_id] = []
        if db_id not in fields_cache:
            try:
                fields_cache[db_id] = manager.database.get_fields_in_specific_db(db_id)
            except Exception:
                fields_cache[db_id] = []

    if old_db_id not in resolved_by_old_db:
        source_short = forced_source or _db_short_code(
            manager, old_db_id, db_name_cache, registry
        )
        # Auto-detect yielded identity (source == target) → card already
        # nominally in target DB. Stale foreign table refs may remain from
        # a previous deep-copy. Fall back to SQL content inference.
        if not forced_source and source_short == target_short:
            inferred = _infer_source_from_sql(card_detail, registry)
            if inferred is not None and inferred != target_short:
                logger.info(
                    'Card %s: DB-detected source==target (%s); SQL inference says %s',
                    cid,
                    target_short,
                    inferred,
                )
                source_short = inferred
        if source_short is None:
            logger.warning(
                'Card %s source DB %r (%s) has no project mapping; skipping',
                cid,
                db_name_cache.get(old_db_id),
                old_db_id,
            )
            return
        try:
            resolved_by_old_db[old_db_id] = registry.resolve(source_short, target_short)
        except Exception:
            logger.exception(
                'resolve(%s -> %s) failed; skipping card %s', source_short, target_short, cid
            )
            return
        logger.info(
            'Resolved mapping %s -> %s: %d table entries, %d rename entries',
            source_short,
            target_short,
            len(resolved_by_old_db[old_db_id].table_mapping),
            len(resolved_by_old_db[old_db_id].rename),
        )
    resolved = resolved_by_old_db[old_db_id]

    if old_db_id not in field_mapping_by_old_db:
        field_mapping_by_old_db[old_db_id] = build_global_field_mapping(
            old_tables=tables_cache.get(old_db_id, []),
            new_tables=tables_cache.get(new_db_id, []),
            old_fields=fields_cache.get(old_db_id, []),
            new_fields=fields_cache.get(new_db_id, []),
            table_mapping=resolved.table_mapping,
        )

    updated_card = process_card(
        manager=manager,
        card_detail=card_detail,
        global_field_mapping=field_mapping_by_old_db[old_db_id],
        new_db_id=new_db_id,
        table_mapping=resolved.table_mapping,
        rename_mapping=resolved.rename,
        spec_tables=registry.spec_tables,
        old_tables=tables_cache.get(old_db_id, []),
        new_tables=tables_cache.get(new_db_id, []),
    )
    print(f'📝 Card ID: {cid} ({updated_card.get("name")})')

    if dry_run:
        print('💡 Dry-run only, not applied.')
        return

    updated_card['database_id'] = new_db_id
    updated_card.setdefault('dataset_query', {})['database'] = new_db_id

    card_field_mapping = field_mapping_by_old_db[old_db_id]
    try:
        unresolved = remap_template_tags_with_table_fallback(
            dataset_query=updated_card['dataset_query'],
            field_mapping=card_field_mapping,
            old_fields=fields_cache.get(old_db_id, []),
            new_fields=fields_cache.get(new_db_id, []),
            old_tables=tables_cache.get(old_db_id, []),
            new_tables=tables_cache.get(new_db_id, []),
            table_mapping=resolved.table_mapping,
        )
        remap_template_tags_in(updated_card['dataset_query'], card_field_mapping)
        remove_unmapped_template_tags(updated_card['dataset_query'], card_field_mapping)
        if unresolved:
            logger.warning(
                'Card %s has %d unresolved template tags: %s', cid, len(unresolved), unresolved
            )
    except Exception:
        logger.exception('Failed to remap template-tags for card %s', cid)

    safe_payload = {k: v for k, v in updated_card.items() if k in ALLOWED_UPDATE_KEYS}
    try:
        manager.card.update_specific_card(cid, safe_payload)
        print('✅ Updated successfully.')
    except requests.exceptions.HTTPError as e:
        resp = e.response
        print('❌ Update failed with HTTPError')
        print('Status:', resp.status_code if resp is not None else 'N/A')
        print('Response body:', resp.text if resp is not None else 'N/A')
        raise


def _update_cards(manager: MetabaseAPIManager) -> None:
    card_ids = _select_card_ids(manager)
    if not card_ids:
        print('⚠️ No cards selected.')
        input('🔙 Press Enter to return...')
        return
    print(f'✅ Found {len(card_ids)} card(s) to update.')

    new_db_id, db_name = _resolve_target_db(manager, card_ids)
    if new_db_id is None:
        print('❌ Could not resolve target database. Aborting.')
        input('🔙 Press Enter to return...')
        return

    registry = ProjectRegistry.load(_PROJECT_DIR)
    raw_short = _short_db_code(db_name)
    target_short = registry.resolve_short_code(raw_short)
    if target_short is None:
        print(
            f'❌ No project mapping found for target database: {db_name!r} '
            f'(computed short={raw_short!r})'
        )
        print(f'Available: {sorted(p.short_code for p in registry.all())}')
        print(
            'Hint: add the computed short to `short_code_aliases` in the '
            'matching core/projects/<code>.yaml file.'
        )
        input('🔙 Press Enter to return...')
        return

    forced_source = _prompt_force_source(registry)
    if forced_source:
        print(f'🔧 Forcing source short_code = {forced_source!r} for all cards')

    dry_run = not input_yes_no('Do you want to APPLY changes? (Answer NO to perform a dry-run)')
    if dry_run:
        print('--- Running in dry-run mode; no updates will be sent to the API ---')

    tables_cache: dict[int, list[dict[str, Any]]] = {}
    fields_cache: dict[int, list[dict[str, Any]]] = {}
    db_name_cache: dict[int, str] = {new_db_id: db_name}
    field_mapping_by_old_db: dict[int, dict[int, int]] = {}
    resolved_by_old_db: dict[int, ResolvedMapping] = {}

    for cid in card_ids:
        try:
            _process_and_send(
                manager,
                cid,
                new_db_id,
                registry,
                target_short,
                tables_cache,
                fields_cache,
                db_name_cache,
                field_mapping_by_old_db,
                resolved_by_old_db,
                dry_run,
                forced_source=forced_source,
            )
        except Exception:
            logger.exception('Failed processing card %s', cid)

    print('🎯 Done updating cards.')
    input('🔙 Press Enter to return...')


def _delete_card(manager: MetabaseAPIManager) -> None:
    cid = input_int("Enter card ID to delete (or 'q' to cancel): ")
    if cid is None:
        print('Delete cancelled.')
        input('🔙 Press Enter to return...')
        return
    confirm_and_delete('card', cid, manager.card.delete_specific_card)


def card_menu(manager: MetabaseAPIManager) -> None:
    run_resource_menu(
        title='Cards',
        list_fn=lambda: _list_cards(manager),
        actions={
            'c': ('Create new card', _create_card_placeholder),
            'u': ('Update card', lambda: _update_cards(manager)),
            'd': ('Delete card', lambda: _delete_card(manager)),
        },
        id_handler=lambda cid: _view_card(manager, cid),
    )
