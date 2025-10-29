from src.connector.api.card_api import CardAPI
from src.connector.api.collection_api import CollectionAPI
from src.connector.api.dashboard_api import DashboardAPI
from src.connector.api.database_api import DatabaseAPI
from src.connector.api.permission_api import PermissionsAPI


class MetabaseAPIManager:
    """
    Manages and provides Metabase API clients (Card, Collection, Dashboard,...).

    Initialized with an API token and base URL, this class creates and caches API clients,
    simplifying and standardizing access to different endpoints.

    Attributes:
        _api_token (str): API token used for authentication in requests.
        _base_url (str): Base URL for the Metabase API.
        _clients (dict): Cache of instantiated API clients.

    Methods:
        card: Returns an instance of CardAPI.
        collection: Returns an instance of CollectionAPI.
        dashboard: Returns an instance of DashboardAPI.
    """

    def __init__(self, api_token: str, base_url: str):
        """
        Initialize MetabaseAPIManager.

        Args:
            api_token (str): API token used for authentication.
            base_url (str): Base URL for Metabase API (e.g., 'https://your-metabase.com/api/card/').
        """
        self._api_token = api_token
        self._base_url = base_url.rstrip(
            '/')  # remove trailing slash if present
        self._clients = {}

    def _get_client(self, cls, endpoint: str):
        """
        Retrieve or create an API client instance.

        Args:
            cls (class): API client class to instantiate.
            endpoint (str): Endpoint path for the specific API (e.g., 'card', 'dashboard').

        Returns:
            instance: An instance of the API client.
        """
        if cls not in self._clients:
            full_url = f'{self._base_url}/{endpoint}/'
            self._clients[cls] = cls(self._api_token, full_url)
        return self._clients[cls]

    @property
    def card(self) -> CardAPI:
        """API client for Metabase Cards."""
        return self._get_client(CardAPI, 'card')

    @property
    def collection(self) -> CollectionAPI:
        """API client for Metabase Collections."""
        return self._get_client(CollectionAPI, 'collection')

    @property
    def dashboard(self) -> DashboardAPI:
        """API client for Metabase Dashboards."""
        return self._get_client(DashboardAPI, 'dashboard')

    @property
    def database(self) -> DatabaseAPI:
        """API client for Metabase databases."""
        return self._get_client(DatabaseAPI, 'database')

    @property
    def permissions(self) -> PermissionsAPI:
        """API client for Metabase permissions."""
        return self._get_client(PermissionsAPI, 'permissions')
