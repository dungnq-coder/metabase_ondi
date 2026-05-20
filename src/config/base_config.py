"""Load Metabase CLI runtime config from `core/config.yaml`."""

from __future__ import annotations

import os
from pathlib import Path
from typing import Any

import yaml

DEFAULT_CONFIG_FILENAME = 'config.yaml'
_CORE_DIR = Path(__file__).resolve().parent.parent.parent / 'core'


def _config_path(filename: str) -> Path:
    return _CORE_DIR / filename


def load_config(filename: str = DEFAULT_CONFIG_FILENAME) -> dict[str, Any]:
    path = _config_path(filename)
    try:
        with path.open('r', encoding='utf-8') as fh:
            return yaml.safe_load(fh) or {}
    except FileNotFoundError as e:
        raise FileNotFoundError(f'Configuration file not found: {path}') from e
    except yaml.YAMLError as e:
        raise ValueError(f"YAML parsing error in '{path}': {e}") from e


def save_yaml(data: dict[str, Any], filename: str = DEFAULT_CONFIG_FILENAME) -> None:
    path = _config_path(filename)
    with path.open('w', encoding='utf-8') as fh:
        yaml.safe_dump(data, fh, allow_unicode=True, sort_keys=False)


class BaseConfig:
    """Read+write access to `core/config.yaml` with dot-notation `get`."""

    def __init__(self, config_data: dict[str, Any] | None = None):
        self._config_file = DEFAULT_CONFIG_FILENAME
        self._config: dict[str, Any] = (
            config_data if config_data is not None else load_config(self._config_file)
        )

    def get(self, key_path: str, default: Any = None) -> Any:
        node: Any = self._config
        for key in key_path.split('.'):
            if not isinstance(node, dict):
                return default
            node = node.get(key)
            if node is None:
                return default
        return node

    def set(self, key_path: str, value: Any) -> None:
        keys = key_path.split('.')
        node = self._config
        for key in keys[:-1]:
            if key not in node or not isinstance(node[key], dict):
                node[key] = {}
            node = node[key]
        node[keys[-1]] = value

    def save(self) -> None:
        save_yaml(self._config, self._config_file)

    @property
    def config(self) -> dict[str, Any]:
        return self._config

    # ---- Convenience accessors ----

    @property
    def base_url(self) -> str:
        return str(self.get('metabase.base_url', ''))

    @property
    def api_token(self) -> str:
        return str(self.get('metabase.api_token', ''))

    @property
    def service_account(self) -> str:
        return str(self.get('gcp.service_account_path', ''))

    @property
    def fs_timeline_event(self) -> tuple[Any, Any]:
        return self.get('metabase.time_line_dh_id'), self.get('gcp.dh_patch_note')

    @property
    def sr_timeline_event(self) -> tuple[Any, Any]:
        return self.get('metabase.time_line_sr_id'), self.get('gcp.sr_patch_note')


# Allow legacy environment override of config path (used for tests).
_env_path = os.environ.get('METABASE_CLI_CONFIG_DIR')
if _env_path:
    _CORE_DIR = Path(_env_path)
