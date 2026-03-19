import sys
import os
import tempfile
import shutil
sys.path.insert(0, "src")

from tools.nfo_generator import generate_nfo, read_nfo
from models.video import Video

def test_generate_nfo_with_extra():
    tmp = tempfile.mkdtemp()
    try:
        video = Video(
            title="测试标题",
            original_title="Test Title",
            year=2023,
            plot="剧情简介",
            genres=["成人", "单机"],
            director="导演",
            actors=["演员A", "演员B"],
            rating=8.5,
            release_date="2023-07-25",
            extra={
                "catalog_number": "ABF-061",
                "studio": "Moodyz",
                "maker": "S1 NO.1 STYLE",
                "customrating": "JP-18+",
            }
        )
        video_path = os.path.join(tmp, "ABF-061.mp4")
        with open(video_path, "w") as f:
            f.write("test")

        nfo_path = generate_nfo(video, video_path)

        assert os.path.exists(nfo_path)

        # 验证 extra 字段被写入
        data = read_nfo(nfo_path)
        assert data.get("num") == "ABF-061"
        assert data.get("studio") == "Moodyz"
        assert data.get("maker") == "S1 NO.1 STYLE"
    finally:
        shutil.rmtree(tmp)