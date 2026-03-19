import pytest
import os
import sys

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))


def test_config_loading():
    from src.config import Config
    config = Config()
    assert config.media_dir == "/media/jav/JAV_output"
    assert config.download_dir == "/downloads"
