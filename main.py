from core.base_config import BaseConfig
from src.connector.manager import MetabaseAPIManager
from src.menu_cli.cards_menu import card_menu
from src.menu_cli.collections_menu import collection_menu
from src.menu_cli.dashboards_menu import dashboard_menu
from src.menu_cli.database_menu import database_menu
from src.menu_cli.permission_menu import permissions_menu
from src.utils.screen_contact import clear_screen


def show_menu(title: str, options: list[str]) -> str:
    clear_screen()
    print(f'{title}')
    print('=' * 60)
    for idx, option in enumerate(options, start=1):
        print(f'{idx}. {option}')
    return input('\n🔢 Choose an option: ')


def run_cli():
    config = BaseConfig()
    manager = MetabaseAPIManager(api_token=config.api_token,
                                 base_url=config.base_url)

    while True:
        choice = show_menu('📦 Metabase CLI Tool', [
            'Collections', 'Dashboards', 'Cards', 'Database', 'Permission',
            'Exit'
        ])
        if choice == '1':
            collection_menu(manager)
        elif choice == '2':
            dashboard_menu(manager)
        elif choice == '3':
            card_menu(manager)
        elif choice == '4':
            database_menu(manager)
        elif choice == '5':
            permissions_menu(manager)
        elif choice == '6':
            print('👋 Exiting Metabase CLI. Goodbye!')
            break
        else:
            input('❗ Invalid choice. Press Enter to continue.')


if __name__ == '__main__':
    run_cli()
