import pytest
import os
import tempfile
import shutil
from src.tools.file_ops import list_dir, move_file, copy_file, delete_file, create_dir, get_file_info


@pytest.fixture
def temp_dir():
    tmp = tempfile.mkdtemp()
    yield tmp
    shutil.rmtree(tmp)


def test_list_dir(temp_dir):
    os.makedirs(os.path.join(temp_dir, "subdir"))
    open(os.path.join(temp_dir, "file.txt"), "w").write("test")

    result = list_dir(temp_dir)
    assert len(result) == 2
    assert "subdir" in [r["name"] for r in result]
    assert "file.txt" in [r["name"] for r in result]


def test_create_dir(temp_dir):
    result = create_dir(os.path.join(temp_dir, "newdir"))
    assert os.path.isdir(os.path.join(temp_dir, "newdir"))


def test_get_file_info(temp_dir):
    filepath = os.path.join(temp_dir, "test.txt")
    with open(filepath, "w") as f:
        f.write("hello")

    info = get_file_info(filepath)
    assert info["name"] == "test.txt"
    assert info["size"] == 5


def test_move_file(temp_dir):
    src = os.path.join(temp_dir, "source.txt")
    dst = os.path.join(temp_dir, "moved.txt")

    with open(src, "w") as f:
        f.write("test")

    result = move_file(src, dst)
    assert os.path.exists(dst)
    assert not os.path.exists(src)


def test_copy_file(temp_dir):
    src = os.path.join(temp_dir, "source.txt")
    dst = os.path.join(temp_dir, "copied.txt")

    with open(src, "w") as f:
        f.write("test")

    result = copy_file(src, dst)
    assert os.path.exists(dst)
    assert os.path.exists(src)


def test_delete_file(temp_dir):
    filepath = os.path.join(temp_dir, "delete_me.txt")
    with open(filepath, "w") as f:
        f.write("test")

    result = delete_file(filepath)
    assert not os.path.exists(filepath)
