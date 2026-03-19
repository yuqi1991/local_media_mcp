import sys
import os
import tempfile
import shutil
sys.path.insert(0, "src")

from models.library import Library
from models.video import Video

def test_library_init():
    tmp = tempfile.mkdtemp()
    try:
        lib = Library(media_dir=tmp, index_path=os.path.join(tmp, "index.jsonl"))
        assert lib.media_dir == tmp
        assert os.path.exists(lib.index_path)
    finally:
        shutil.rmtree(tmp)

def test_library_index_add():
    tmp = tempfile.mkdtemp()
    try:
        lib = Library(media_dir=tmp, index_path=os.path.join(tmp, "index.jsonl"))
        video = Video(title="Test", extra={"catalog_number": "TEST-001"})
        lib._add_to_index(video)

        videos = lib.list_videos()
        assert len(videos) == 1
        assert videos[0].catalog_number == "TEST-001"
    finally:
        shutil.rmtree(tmp)

def test_library_index_remove():
    tmp = tempfile.mkdtemp()
    try:
        lib = Library(media_dir=tmp, index_path=os.path.join(tmp, "index.jsonl"))
        video = Video(title="Test", extra={"catalog_number": "TEST-001"})
        lib._add_to_index(video)

        lib._remove_from_index("TEST-001")
        videos = lib.list_videos()
        assert len(videos) == 0
    finally:
        shutil.rmtree(tmp)

def test_library_import_video():
    tmp = tempfile.mkdtemp()
    try:
        lib = Library(media_dir=tmp, index_path=os.path.join(tmp, "index.jsonl"))

        # Create a test video file
        source_dir = os.path.join(tmp, "source")
        os.makedirs(source_dir)
        source_file = os.path.join(source_dir, "TEST-001.mp4")
        with open(source_file, "w") as f:
            f.write("test content")

        video = Video(
            title="Test Video",
            extra={"catalog_number": "TEST-001"}
        )

        imported = lib.import_video(video, source_path=source_file)

        assert os.path.exists(imported.video_path)
        assert "TEST-001" in imported.video_path
        assert os.path.exists(imported.nfo_path)

    finally:
        shutil.rmtree(tmp)