import os
import json
from datetime import datetime
from typing import List, Optional, Dict, Any
from pathlib import Path
from .video import Video

class Library:
    VIDEO_EXTENSIONS = [".mp4", ".mkv", ".avi", ".mov", ".wmv", ".flv", ".webm", ".m4v"]

    def __init__(self, media_dir: str, index_path: str):
        self.media_dir = media_dir
        self.index_path = index_path
        self._ensure_index_exists()

    def _ensure_index_exists(self):
        if not os.path.exists(self.index_path):
            Path(self.index_path).touch()

    def _load_index(self) -> List[Dict[str, Any]]:
        entries = []
        if os.path.exists(self.index_path):
            with open(self.index_path, "r", encoding="utf-8") as f:
                for line in f:
                    line = line.strip()
                    if line:
                        entries.append(json.loads(line))
        return entries

    def _save_index(self, entries: List[Dict[str, Any]]):
        with open(self.index_path, "w", encoding="utf-8") as f:
            for entry in entries:
                f.write(json.dumps(entry, ensure_ascii=False) + "\n")

    def _add_to_index(self, video: Video):
        entries = self._load_index()
        # 检查是否已存在
        for i, entry in enumerate(entries):
            if entry.get("catalog_number") == video.catalog_number:
                entries[i] = {
                    "catalog_number": video.catalog_number,
                    "video_path": video.video_path,
                    "imported_at": datetime.now().isoformat(),
                }
                self._save_index(entries)
                return
        # 新增
        entries.append({
            "catalog_number": video.catalog_number,
            "video_path": video.video_path,
            "imported_at": datetime.now().isoformat(),
        })
        self._save_index(entries)

    def _remove_from_index(self, catalog_number: str):
        entries = self._load_index()
        entries = [e for e in entries if e.get("catalog_number") != catalog_number]
        self._save_index(entries)

    def scan_source_dir(self, source_dir: str) -> List[Dict[str, Any]]:
        """扫描源目录，返回未入库的视频文件"""
        indexed = {v.catalog_number for v in self.list_videos()}
        results = []

        for root, dirs, files in os.walk(source_dir):
            for f in files:
                ext = os.path.splitext(f)[1].lower()
                if ext not in self.VIDEO_EXTENSIONS:
                    continue

                path = os.path.join(root, f)
                # 尝试从文件名提取番號
                catalog_number = self._extract_catalog_number(f)
                if catalog_number and catalog_number not in indexed:
                    results.append({
                        "filename": f,
                        "path": path,
                        "size": os.path.getsize(path),
                        "catalog_number": catalog_number,
                    })
                elif not catalog_number:
                    # 无法提取番號但未入库
                    results.append({
                        "filename": f,
                        "path": path,
                        "size": os.path.getsize(path),
                        "catalog_number": None,
                    })

        return results

    def _extract_catalog_number(self, filename: str) -> Optional[str]:
        """从文件名提取番號"""
        import re
        # 匹配常见番號格式: ABC-123, ABC123, ABF-061 等
        pattern = r"([A-Z]{2,10}[-_]?\d{2,5})"
        match = re.search(pattern, filename.upper())
        if match:
            result = match.group(1)
            return result.replace("_", "-")
        return None

    def import_video(self, video: Video, source_path: str = None) -> Video:
        """导入影片到媒体库"""
        catalog_number = video.catalog_number
        if not catalog_number:
            raise ValueError("Video must have catalog_number")

        # 创建影片目录
        video_dir = os.path.join(self.media_dir, catalog_number)
        os.makedirs(video_dir, exist_ok=True)

        # 移动视频文件
        if source_path and os.path.exists(source_path):
            dest_video = os.path.join(video_dir, f"{catalog_number}{os.path.splitext(source_path)[1]}")
            if source_path != dest_video:
                os.rename(source_path, dest_video)
            video.video_path = dest_video

        # 生成 NFO (先创建占位符，实际生成由调用方负责)
        video.nfo_path = os.path.join(video_dir, f"{catalog_number}.nfo")
        # 创建空的 NFO 占位符
        Path(video.nfo_path).touch()
        video.poster_path = os.path.join(video_dir, "poster.jpg")
        video.fanart_path = os.path.join(video_dir, "fanart.jpg")
        video.thumb_path = os.path.join(video_dir, "thumb.jpg")
        video.extrafanart_dir = os.path.join(video_dir, "extrafanart")

        # 更新索引
        self._add_to_index(video)

        return video

    def remove_video(self, catalog_number: str) -> bool:
        """从库中移除影片（删除文件，更新索引）"""
        video = self.get_video(catalog_number)
        if not video:
            return False

        # 删除影片目录
        video_dir = os.path.join(self.media_dir, catalog_number)
        if os.path.exists(video_dir):
            import shutil
            shutil.rmtree(video_dir)

        # 从索引移除
        self._remove_from_index(catalog_number)
        return True

    def get_video(self, catalog_number: str) -> Optional[Video]:
        """获取指定影片信息"""
        entries = self._load_index()
        for entry in entries:
            if entry.get("catalog_number") == catalog_number:
                video = Video(
                    title=entry.get("title", catalog_number),
                    extra={"catalog_number": catalog_number}
                )
                video.video_path = entry.get("video_path", "")
                return video
        return None

    def list_videos(self) -> List[Video]:
        """列出库中所有影片"""
        videos = []
        for entry in self._load_index():
            video = Video(
                title=entry.get("title", entry.get("catalog_number", "")),
                extra={"catalog_number": entry.get("catalog_number", "")}
            )
            video.video_path = entry.get("video_path", "")
            videos.append(video)
        return videos

    def search(self, query: str) -> List[Video]:
        """搜索影片"""
        results = []
        query_lower = query.lower()
        for video in self.list_videos():
            if query_lower in video.title.lower() or query_lower in video.catalog_number.lower():
                results.append(video)
        return results

    def get_stats(self) -> Dict[str, Any]:
        """获取库统计信息"""
        videos = self.list_videos()
        return {
            "total": len(videos),
            "recent_imports": [
                {"catalog_number": v.catalog_number}
                for v in videos[-10:]
            ]
        }