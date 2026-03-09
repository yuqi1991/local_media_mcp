import pytest
import os
import sys

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))


def test_config_loading():
    from src.config import Config
    config = Config()
    assert config.media_dir == "/media"
    assert config.download_dir == "/downloads"


def test_file_operations():
    from src.tools.file_ops import create_dir, list_dir
    import tempfile, shutil

    tmp = tempfile.mkdtemp()
    try:
        create_dir(os.path.join(tmp, "test"))
        result = list_dir(tmp)
        assert any(r["name"] == "test" for r in result)
    finally:
        shutil.rmtree(tmp)


def test_media_scanner():
    from src.tools.media_scanner import scan_media_library, MEDIA_EXTENSIONS
    assert ".mp4" in MEDIA_EXTENSIONS["video"]
    assert ".mkv" in MEDIA_EXTENSIONS["video"]


def test_nfo_generator():
    from src.tools.nfo_generator import read_nfo
    from src.scrapers.base import MediaMetadata
    import tempfile, os

    # Create a simple test NFO
    tmp = tempfile.mkdtemp()
    nfo_path = os.path.join(tmp, "test.nfo")

    # Write a simple NFO
    with open(nfo_path, "w", encoding="utf-8") as f:
        f.write('<?xml version="1.0" ?>\n<item><title>Test Movie</title><year>2024</year></item>')

    try:
        result = read_nfo(nfo_path)
        assert result["title"] == "Test Movie"
        assert result["year"] == "2024"
    finally:
        os.remove(nfo_path)
        os.rmdir(tmp)
