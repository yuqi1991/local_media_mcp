import os
from pathlib import Path
from typing import List, Dict, Any

# 支持的视频格式
MEDIA_EXTENSIONS = {
    "video": [".mp4", ".mkv", ".avi", ".mov", ".wmv", ".flv", ".webm", ".m4v"],
    "image": [".jpg", ".jpeg", ".png", ".gif", ".webp", ".bmp"],
    "nfo": [".nfo"]
}


def scan_media_library(path: str, recursive: bool = True) -> List[Dict[str, Any]]:
    """扫描媒体库，返回所有媒体文件"""
    if not os.path.isdir(path):
        raise ValueError(f"Not a directory: {path}")

    result = []

    if recursive:
        for root, dirs, files in os.walk(path):
            for f in files:
                full_path = os.path.join(root, f)
                file_ext = Path(f).suffix.lower()

                file_type = None
                for t, exts in MEDIA_EXTENSIONS.items():
                    if file_ext in exts:
                        file_type = t
                        break

                if file_type:
                    result.append({
                        "name": f,
                        "path": full_path,
                        "type": file_type,
                        "size": os.path.getsize(full_path)
                    })
    else:
        for f in os.listdir(path):
            full_path = os.path.join(path, f)
            if os.path.isfile(full_path):
                file_ext = Path(f).suffix.lower()

                file_type = None
                for t, exts in MEDIA_EXTENSIONS.items():
                    if file_ext in exts:
                        file_type = t
                        break

                if file_type:
                    result.append({
                        "name": f,
                        "path": full_path,
                        "type": file_type,
                        "size": os.path.getsize(full_path)
                    })

    return result
