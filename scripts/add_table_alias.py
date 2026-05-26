"""Add a backticked alias to every reference of a specific table in a card.

Transformation:
    `proj.dataset.table`           ->  `proj.dataset.table` AS `dataset.table`
    `proj.dataset.table` AS `x`    ->  (left alone; already aliased)

Affects every native SQL string in the card (top-level + every stage).

Usage:
    python scripts/add_table_alias.py --card-id 6361 \
        --table fortias-saga.flattened_table.huynn_dh_active_daily
    # dry-run by default; prints unified diff

    python scripts/add_table_alias.py --card-id 6361 \
        --table fortias-saga.flattened_table.huynn_dh_active_daily --apply
    # writes back via /api/card/<id> PUT

    python scripts/add_table_alias.py --dashboard-id 999 \
        --table fortias-saga.flattened_table.huynn_dh_active_daily --apply
    # apply to every card on dashboard 999
"""

from __future__ import annotations

import argparse
import difflib
import re
import sys
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parent.parent
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

from src.config.base_config import BaseConfig  # noqa: E402
from src.connector.manager import MetabaseAPIManager  # noqa: E402

# Keys safely accepted by Metabase /api/card PUT. Mirrors cards_menu.ALLOWED_UPDATE_KEYS.
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


def _alias_for(full: str) -> str:
    """Strip the leading project segment; keep dataset.table as the alias."""
    parts = full.split('.', 1)
    return parts[1] if len(parts) == 2 else full


def add_alias_in_sql(sql: str, table_full: str) -> tuple[str, int]:
    """Insert `` AS `<alias>` `` after each unaliased ref of `table_full`.

    Returns (new_sql, n_replacements). Skips occurrences already followed by
    `AS ...` (case-insensitive, any whitespace).
    """
    alias = _alias_for(table_full)
    backticked = f'`{table_full}`'
    # Negative lookahead: NOT followed by optional whitespace + AS keyword.
    pattern = re.compile(
        re.escape(backticked) + r'(?!\s+AS\b)',
        re.IGNORECASE,
    )
    new_sql, n = pattern.subn(f'{backticked} AS `{alias}`', sql)
    return new_sql, n


def _rewrite_dataset_query(dq: dict, table_full: str) -> tuple[dict, int]:
    """Walk dataset_query, rewrite every native SQL location, count total replacements."""
    total = 0
    native = dq.get('native') or {}
    for key in ('query', 'native'):
        v = native.get(key)
        if isinstance(v, str) and v:
            new_v, n = add_alias_in_sql(v, table_full)
            if n > 0:
                native[key] = new_v
                total += n
    if native:
        dq['native'] = native
    for stage in dq.get('stages') or []:
        if not isinstance(stage, dict):
            continue
        for key in ('native', 'query'):
            v = stage.get(key)
            if isinstance(v, str) and v:
                new_v, n = add_alias_in_sql(v, table_full)
                if n > 0:
                    stage[key] = new_v
                    total += n
    return dq, total


def _process_card(
    manager: MetabaseAPIManager, card_id: int, table_full: str, apply: bool
) -> None:
    card = manager.card.get_card_detail(card_id)
    name = card.get('name')
    dq = card.get('dataset_query') or {}

    before_blob = _collect_sql(dq)
    new_dq, n = _rewrite_dataset_query(dict(dq), table_full)
    after_blob = _collect_sql(new_dq)

    print(f'\n=== Card {card_id}: {name!r} ===')
    print(f'  replacements: {n}')
    if n == 0:
        print('  (nothing to change)')
        return

    for line in difflib.unified_diff(
        before_blob.splitlines(keepends=True),
        after_blob.splitlines(keepends=True),
        fromfile='before',
        tofile='after',
        n=1,
    ):
        sys.stdout.write(line)

    if not apply:
        print('  (dry-run; pass --apply to write back)')
        return

    payload = {k: v for k, v in card.items() if k in ALLOWED_UPDATE_KEYS}
    payload['dataset_query'] = new_dq
    try:
        manager.card.update_specific_card(card_id, payload)
        print(f'  ✅ Card {card_id} updated.')
    except Exception as e:
        print(f'  ❌ Card {card_id} update failed: {e}')


def _collect_sql(dq: dict) -> str:
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


def main() -> None:
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    target = p.add_mutually_exclusive_group(required=True)
    target.add_argument('--card-id', type=int, help='operate on a single card')
    target.add_argument('--dashboard-id', type=int, help='operate on every card of this dashboard')
    p.add_argument(
        '--table',
        required=True,
        help='fully-qualified table name without backticks, e.g. '
        'fortias-saga.flattened_table.huynn_dh_active_daily',
    )
    p.add_argument(
        '--apply',
        action='store_true',
        help='write back via Metabase API (default is dry-run)',
    )
    args = p.parse_args()

    cfg = BaseConfig()
    manager = MetabaseAPIManager(api_token=cfg.api_token, base_url=cfg.base_url)

    if args.card_id is not None:
        card_ids = [args.card_id]
    else:
        all_cards = manager.card.list_all_cards()
        card_ids = [c['id'] for c in all_cards if c.get('dashboard_id') == args.dashboard_id]
        print(f'Found {len(card_ids)} card(s) on dashboard {args.dashboard_id}')

    for cid in card_ids:
        try:
            _process_card(manager, cid, args.table, args.apply)
        except Exception as e:
            print(f'❌ Card {cid} failed: {e}')


if __name__ == '__main__':
    main()
