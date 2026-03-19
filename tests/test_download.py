import sys
sys.path.insert(0, "src")

def test_download_manager_import():
    from tools.download import DownloadManager
    # Just verify the import works
    assert True

def test_download_manager_init():
    from tools.download import DownloadManager
    dm = DownloadManager(host="localhost", port=6800, secret="test")
    assert dm.host == "http://localhost"
    assert dm.port == 6800
