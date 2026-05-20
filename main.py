"""Entry point for the Metabase CLI."""

from __future__ import annotations

import logging
import os

from src.config.base_config import BaseConfig
from src.connector.manager import MetabaseAPIManager
from src.menu_cli._base import show_menu
from src.menu_cli.cards_menu import card_menu
from src.menu_cli.collections_menu import collection_menu
from src.menu_cli.dashboards_menu import dashboard_menu
from src.menu_cli.database_menu import database_menu
from src.menu_cli.permission_menu import permissions_menu


def run_cli() -> None:
    config = BaseConfig()
    manager = MetabaseAPIManager(api_token=config.api_token, base_url=config.base_url)

    main_actions = {
        '1': collection_menu,
        '2': dashboard_menu,
        '3': card_menu,
        '4': database_menu,
        '5': permissions_menu,
    }

    while True:
        choice = show_menu(
            '📦 Metabase CLI Tool',
            ['Collections', 'Dashboards', 'Cards', 'Database', 'Permission', 'Exit'],
        )
        if choice == '6':
            print('👋 Exiting Metabase CLI. Goodbye!')
            break
        action = main_actions.get(choice)
        if action is not None:
            action(manager)
        else:
            input('❗ Invalid choice. Press Enter to continue.')


def _configure_logging() -> None:
    level = os.environ.get('METABASE_CLI_LOG', 'WARNING').upper()
    logging.basicConfig(
        level=level,
        format='%(asctime)s %(levelname)s %(name)s: %(message)s',
    )


if __name__ == '__main__':
    _configure_logging()
    run_cli()
