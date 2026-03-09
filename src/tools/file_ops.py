import os
import shutil
from pathlib import Path
from typing import List, Dict, Any, Optional
from dataclasses import dataclass


@dataclass
class FileInfo:
    name: str
    path: str
    is_dir: bool
    size: int
    modified_time: float


def list_dir(path: str) -> List[Dict[str, Any]]:
    """列出目录内容"""
    if not os.path.isdir(path):
        raise ValueError(f"Not a directory: {path}")

    result = []
    for name in os.listdir(path):
        full_path = os.path.join(path, name)
        stat = os.stat(full_path)
        result.append({
            "name": name,
            "path": full_path,
            "is_dir": os.path.isdir(full_path),
            "size": stat.st_size if not os.path.isdir(full_path) else 0,
            "modified_time": stat.st_mtime
        })
    return result


def move_file(src: str, dst: str) -> Dict[str, str]:
    """移动/重命名文件"""
    if not os.path.exists(src):
        raise FileNotFoundError(f"Source not found: {src}")

    os.makedirs(os.path.dirname(dst), exist_ok=True)
    shutil.move(src, dst)
    return {"from": src, "to": dst}


def copy_file(src: str, dst: str) -> Dict[str, str]:
    """复制文件"""
    if not os.path.exists(src):
        raise FileNotFoundError(f"Source not found: {src}")

    os.makedirs(os.path.dirname(dst), exist_ok=True)
    if os.path.isdir(src):
        shutil.copytree(src, dst)
    else:
        shutil.copy2(src, dst)
    return {"from": src, "to": dst}


def delete_file(path: str) -> Dict[str, str]:
    """删除文件或目录"""
    if not os.path.exists(path):
        raise FileNotFoundError(f"Not found: {path}")

    if os.path.isdir(path):
        shutil.rmtree(path)
    else:
        os.remove(path)
    return {"deleted": path}


def create_dir(path: str) -> Dict[str, str]:
    """创建目录"""
    os.makedirs(path, exist_ok=True)
    return {"created": path}


def get_file_info(path: str) -> Dict[str, Any]:
    """获取文件信息"""
    if not os.path.exists(path):
        raise FileNotFoundError(f"Not found: {path}")

    stat = os.stat(path)
    return {
        "name": os.path.basename(path),
        "path": os.path.abspath(path),
        "is_dir": os.path.isdir(path),
        "size": stat.st_size,
        "modified_time": stat.st_mtime,
        "created_time": stat.st_ctime
    }
