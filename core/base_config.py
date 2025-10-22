import os
from typing import Any, Optional

import yaml


def load_config(filename: str = 'config.yaml') -> dict:
    """
    Load YAML configuration from the core directory.
    """
    try:
        base_dir = os.path.dirname(os.path.abspath(__file__))
        file_path = os.path.join(base_dir, '..', 'core', filename)
        with open(file_path, 'r') as file:
            return yaml.safe_load(file) or {}
    except FileNotFoundError:
        raise FileNotFoundError(f'Configuration file not found: {file_path}')
    except yaml.YAMLError as e:
        raise ValueError(f"YAML parsing error in '{file_path}': {e}")


class DotDict(dict):
    """
    Dictionary with dot notation access.
    """

    def __getattr__(self, item):
        return self.get(item)

    def __setattr__(self, key, value):
        self[key] = value

    def __delattr__(self, key):
        del self[key]


class BaseConfig:
    """
    Base class for accessing configuration values via dot notation or key path.
    """

    def __init__(self, config_data: Optional[dict] = None):
        self._config = config_data or self._load_main_config()

    def _load_main_config(self) -> dict:
        return load_config()

    def get(self, key_path: str, default: Any = None) -> Any:
        """
        Get config value from dot-separated key path. E.g., "database.host".
        """
        keys = key_path.split('.')
        value = self._config
        for key in keys:
            if isinstance(value, dict):
                value = value.get(key)
                if value is None:
                    return default
            else:
                return default
        return value

    def __getitem__(self, item: str) -> Any:
        return self._config.get(item)

    def __getattr__(self, item: str) -> Any:
        """
        Allow dot notation access, e.g., config.database.host
        """
        value = self._config.get(item)
        if isinstance(value, dict):
            return DotDict(value)
        return value

    @property
    def config(self) -> dict:
        """
        Return the full configuration dictionary.
        """
        return self._config

    @property
    def yaml_template_config(self) -> dict:
        """
        Lazy load template config from config.yaml
        """
        if not hasattr(self, '_yaml_template_config'):
            self._yaml_template_config = load_config()
        return self._yaml_template_config

    @property
    def base_url(self) -> str:
        """
        Get the base URL from configuration.
        """
        return self.get('metabase.base_url', '')

    @property
    def api_token(self) -> str:
        """
        Get the API token from configuration.
        """
        return self.get('metabase.api_token', '')
