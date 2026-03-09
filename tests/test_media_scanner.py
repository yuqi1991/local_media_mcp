import pytest
import os
import tempfile
import shutil

from src.tools.media_scanner import scan_media_library, MEDIA_EXTENSIONS


@pytest.fixture
def temp_dir():
    tmp = tempfile.mkdtemp()
    yield tmp
    shutil.rmtree(tmp)


def test_scan_media_library(temp_dir):
    # Create test media files
    os.makedirs(os.path.join(temp_dir, "movie1"))
    open(os.path.join(temp_dir, "movie1", "movie1.mp4"), "w").write("video")
    open(os.path.join(temp_dir, "movie1", "poster.jpg"), "w").write("image")

    result = scan_media_library(temp_dir)
    assert len(result) >= 1
    assert any(r["name"].endswith(".mp4") for r in result)


def test_media_extensions():
    assert ".mp4" in MEDIA_EXTENSIONS["video"]
    assert ".mkv" in MEDIA_EXTENSIONS["video"]
    assert ".jpg" in MEDIA_EXTENSIONS["image"]
    assert ".nfo" in MEDIA_EXTENSIONS["nfo"]
