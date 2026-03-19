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
            "paths": {
                "media_dir": "/media/jav/JAV_output",
                "download_dir": "/downloads",
                "source_dir": "/media/jav",
                "index_path": "/app/config/library_index.jsonl"
            },
            "bt_tracker": {
                "update_url": "https://raw.githubusercontent.com/ngosang/trackerslist/master/trackers_best.txt"
            }
        }

    @property
    def server_host(self) -> str:
        return self._config.get("server", {}).get("host", "0.0.0.0")

    @property
    def server_port(self) -> int:
        return self._config.get("server", {}).get("port", 8000)

    @property
    def media_dir(self) -> str:
        return os.environ.get("MEDIA_DIR", self._config.get("paths", {}).get("media_dir", "/media/jav/JAV_output"))

    @property
    def download_dir(self) -> str:
        return os.environ.get("DOWNLOAD_DIR", self._config.get("paths", {}).get("download_dir", "/downloads"))

    @property
    def source_dir(self) -> str:
        return os.environ.get("SOURCE_DIR", self._config.get("paths", {}).get("source_dir", "/media/jav"))

    @property
    def index_path(self) -> str:
        return os.environ.get("INDEX_PATH", self._config.get("paths", {}).get("index_path", "/app/config/library_index.jsonl"))

    @property
    def aria2_rpc_host(self) -> str:
        return os.environ.get("ARIA2_RPC_HOST", self._config.get("aria2", {}).get("rpc_host", "localhost"))

    @property
    def aria2_rpc_port(self) -> int:
        return os.environ.get("ARIA2_RPC_PORT", self._config.get("aria2", {}).get("rpc_port", 6800))

    @property
    def aria2_secret(self) -> str:
        return os.environ.get("ARIA2_RPC_SECRET", self._config.get("aria2", {}).get("rpc_secret", ""))

    @property
    def bt_tracker_url(self) -> str:
        return self._config.get("bt_tracker", {}).get("update_url",
            "https://raw.githubusercontent.com/ngosang/trackerslist/master/trackers_best.txt")
