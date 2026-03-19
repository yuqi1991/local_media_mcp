import sys
sys.path.insert(0, "src")

from models.video import Video

def test_video_creation():
    video = Video(
        title="Test Title",
        catalog_number="TEST-001",
        video_path="/media/test.mp4"
    )
    assert video.title == "Test Title"
    assert video.extra["catalog_number"] == "TEST-001"

def test_video_extra_fields():
    video = Video(
        title="JAV Title",
        extra={
            "catalog_number": "ABF-061",
            "studio": "Moodyz",
            "maker": "S1 NO.1 STYLE",
        }
    )
    assert video.extra["catalog_number"] == "ABF-061"
    assert video.extra["studio"] == "Moodyz"

def test_video_to_dict():
    video = Video(title="Test", extra={"catalog_number": "ABC-123"})
    d = video.to_dict()
    assert d["title"] == "Test"
    assert d["catalog_number"] == "ABC-123"

def test_video_from_dict():
    data = {
        "title": "Test Title",
        "catalog_number": "XYZ-999",
        "studio": "Test Studio"
    }
    video = Video.from_dict(data)
    assert video.title == "Test Title"
    assert video.catalog_number == "XYZ-999"
    assert video.extra["studio"] == "Test Studio"