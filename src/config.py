import os
import yaml
from pathlib import Path


class Config:
    def __init__(self, config_path: str = "config.yaml"):
        self.config_path = config_path
        self._config = self._load_config()

    def _load_config(self) -> dict:
        if not Path(self.config_path).exists():
            return self._default_config()

        with open(self.config_path, 'r', encoding='utf-8') as f:
            return yaml.safe_load(f)

    def _default_config(self) -> dict:
        return {
            "server": {"host": "0.0.0.0", "port": 8000},
            "aria2": {"rpc_host": "localhost", "rpc_port": 6800, "rpc_secret": ""},
            "paths": {"media_dir": "/media", "download_dir": "/downloads"},
            "scrapers": {"tmdb": {"api_key": ""}, "tvdb": {"api_key": ""}, "douban": {"enabled": False}}
        }

    @property
    def media_dir(self) -> str:
        return os.environ.get("MEDIA_DIR", self._config.get("paths", {}).get("media_dir", "/media"))

    @property
    def download_dir(self) -> str:
        return os.environ.get("DOWNLOAD_DIR", self._config.get("paths", {}).get("download_dir", "/downloads"))

    @property
    def aria2_secret(self) -> str:
        return os.environ.get("ARIA2_RPC_SECRET", self._config.get("aria2", {}).get("rpc_secret", ""))

    @property
    def tmdb_api_key(self) -> str:
        return os.environ.get("TMDB_API_KEY", self._config.get("scrapers", {}).get("tmdb", {}).get("api_key", ""))

    @property
    def tvdb_api_key(self) -> str:
        return os.environ.get("TVDB_API_KEY", self._config.get("scrapers", {}).get("tvdb", {}).get("api_key", ""))
