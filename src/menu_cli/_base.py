"""Shared menu loop for `src/menu_cli/*` modules."""

from __future__ import annotations

from collections.abc import Callable
from typing import Any

from src.utils.input_utils import input_str
from src.utils.screen_contact import clear_screen

ID_ACTION_KEY = '__id__'


def show_menu(title: str, options: list[str]) -> str:
    """Render a numbered menu and return the user's raw choice."""
    clear_screen()
    print(title)
    print('=' * 60)
    for idx, option in enumerate(options, start=1):
        print(f'{idx}. {option}')
    return input('\n🔢 Choose an option: ')


def run_resource_menu(
    title: str,
    *,
    list_fn: Callable[[], None],
    actions: dict[str, tuple[str, Callable[[], None]]],
    id_handler: Callable[[int], None] | None = None,
) -> None:
    """Render a CRUD-style menu: list -> choose action key or numeric ID.

    `actions` keys are single-character lowercase strings (e.g. 'c', 'u', 'd').
    'b' (back) is added automatically and must NOT appear in `actions`.
    If `id_handler` is set, numeric inputs are routed to it.
    """
    if 'b' in actions:
        raise ValueError("'b' is reserved for back; do not include in actions")

    while True:
        list_fn()
        print('\nOptions:')
        if id_handler is not None:
            print('  [id] - View by ID')
        for key, (label, _) in actions.items():
            print(f'  {key}    - {label}')
        print('  b    - Back to main menu')

        choice = (
            (input_str('\n🔢 Choose (ID / action): ', required=True, allow_cancel=False) or '')
            .strip()
            .lower()
        )

        if choice == 'b':
            break

        handler = actions.get(choice)
        if handler is not None:
            handler[1]()
            continue

        if id_handler is not None and choice.isdigit():
            id_handler(int(choice))
            continue

        input('❗ Invalid choice. Press Enter to continue.')


def confirm_and_delete(
    label: str,
    target_id: int,
    delete_fn: Callable[[int], Any],
) -> None:
    """Common confirm-then-delete flow used by every menu."""
    from src.utils.input_utils import input_yes_no

    if not input_yes_no(f'Are you sure you want to delete {label} ID {target_id}?'):
        print(f'Delete {label} cancelled.')
        input('🔙 Press Enter to return...')
        return
    res = delete_fn(target_id)
    status = getattr(res, 'status_code', None)
    if status is None or status < 400:
        print(f'✅ {label.capitalize()} ID {target_id} deleted successfully.')
    else:
        print(f'❌ Failed to delete {label} ID {target_id}. Status: {status}')
    input('🔙 Press Enter to return...')
