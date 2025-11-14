import os
from typing import Any, Optional

import yaml


def load_config(filename: str = 'config.yaml') -> dict:
    try:
        base_dir = os.path.dirname(os.path.abspath(__file__))
        file_path = os.path.join(base_dir, '..', 'core', filename)
        with open(file_path, 'r', encoding='utf-8') as file:
            return yaml.safe_load(file) or {}
    except FileNotFoundError:
        raise FileNotFoundError(f'Configuration file not found: {file_path}')
    except yaml.YAMLError as e:
        raise ValueError(f"YAML parsing error in '{file_path}': {e}")


def save_yaml(data: dict, filename: str = 'config.yaml'):
    base_dir = os.path.dirname(os.path.abspath(__file__))
    file_path = os.path.join(base_dir, '..', 'core', filename)
    with open(file_path, 'w', encoding='utf-8') as file:
        yaml.safe_dump(data, file, allow_unicode=True, sort_keys=False)


class DotDict(dict):
    """
    Dictionary with dot notation access.
    """

    def __getattr__(self, item):
        val = self.get(item)
        if isinstance(val, dict):
            return DotDict(val)
        return val

    def __setattr__(self, key, value):
        self[key] = value

    def __delattr__(self, key):
        del self[key]


class BaseConfig:
    """
    Extended BaseConfig: supports reading + writing via dot-notation.
    """

    def __init__(self, config_data: Optional[dict] = None):
        self._config_file = 'config.yaml'
        self._config = config_data or self._load_main_config()

    def _load_main_config(self) -> dict:
        return load_config(self._config_file)

    # -------------------------------
    # GET via dot-notation
    # -------------------------------
    def get(self, key_path: str, default: Any = None) -> Any:
        keys = key_path.split('.')
        value = self._config
        for key in keys:
            if not isinstance(value, dict):
                return default
            value = value.get(key)
            if value is None:
                return default
        return value

    # -------------------------------
    # SET via dot-notation
    # -------------------------------
    def set(self, key_path: str, value: Any):
        """
        Set a config value by dot-notation "a.b.c"
        Automatically creates missing nested levels.
        """
        keys = key_path.split('.')
        node = self._config
        for key in keys[:-1]:
            if key not in node or not isinstance(node[key], dict):
                node[key] = {}  # auto-create nested dict
            node = node[key]

        node[keys[-1]] = value

    # -------------------------------
    # Save loaded config back to YAML
    # -------------------------------
    def save(self):
        save_yaml(self._config, self._config_file)

    # -------------------------------
    # Magic access
    # -------------------------------
    def __getitem__(self, item: str) -> Any:
        return self._config.get(item)

    def __getattr__(self, item: str) -> Any:
        value = self._config.get(item)
        if isinstance(value, dict):
            return DotDict(value)
        return value

    @property
    def config(self) -> dict:
        return self._config

    @property
    def yaml_template_config(self) -> dict:
        if not hasattr(self, '_yaml_template_config'):
            self._yaml_template_config = load_config(self._config_file)
        return self._yaml_template_config

    # Examples of custom properties
    @property
    def base_url(self) -> str:
        return self.get('metabase.base_url', '')

    @property
    def api_token(self) -> str:
        return self.get('metabase.api_token', '')

    @property
    def service_account(self) -> str:
        return self.get('gcp.service_account_path', '')
