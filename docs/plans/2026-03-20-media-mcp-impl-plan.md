# Media MCP + JAV Merge Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Merge jav_archive into media_mcp, creating a unified MCP server for NAS-based Jellyfin library management.

**Architecture:** Three-layer architecture (MCP/CLI → Video/Library models → file operations). MCP exposes only video-level operations; scraping done by remote LLM Agent skill.

**Tech Stack:** Python 3.11, FastMCP, aria2p, Pillow, python-dotenv, pyyaml

---

## Phase 1: Project Restructuring

### Task 1: Create Directory Structure

**Files:**
- Create: `src/models/__init__.py`
- Create: `src/models/video.py`
- Create: `src/models/library.py`
- Create: `src/cli/__init__.py`
- Create: `src/cli/commands.py`

**Step 1: Create directories**

```bash
mkdir -p src/models src/cli
```

**Step 2: Create empty __init__.py files**

```bash
touch src/models/__init__.py src/cli/__init__.py
```

**Step 3: Commit**

```bash
git add src/models src/cli
git commit -m "feat: create models/ and cli/ directory structure"
```

---

### Task 2: Remove Old Files

**Files:**
- Delete: `src/tools/file_ops.py`
- Delete: `src/tools/media_scanner.py`
- Delete: `src/scrapers/` (entire directory)
- Modify: `src/tools/__init__.py` (remove scrapers imports)

**Step 1: Remove old files**

```bash
rm src/tools/file_ops.py src/tools/media_scanner.py
rm -rf src/scrapers
```

**Step 2: Update tools/__init__.py**

Remove imports of removed modules.

**Step 3: Commit**

```bash
git rm src/tools/file_ops.py src/tools/media_scanner.py
git rm -rf src/scrapers
git commit -m "feat: remove old file_ops, media_scanner, and scrapers"
```

---

## Phase 2: Core Models

### Task 3: Create Video Dataclass

**Files:**
- Create: `src/models/video.py`
- Test: `tests/test_video.py`

**Step 1: Write the failing test**

```python
# tests/test_video.py
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
```

**Step 2: Run test to verify it fails**

```bash
pytest tests/test_video.py -v
```

**Step 3: Write implementation**

```python
# src/models/video.py
from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional

@dataclass
class Video:
    # 通用字段
    title: str = ""
    original_title: str = ""
    year: int = 0
    plot: str = ""
    genres: List[str] = field(default_factory=list)
    director: str = ""
    actors: List[str] = field(default_factory=list)
    rating: float = 0.0
    poster_url: str = ""
    backdrop_url: str = ""
    release_date: str = ""

    # 文件路径
    video_path: str = ""
    nfo_path: str = ""

    # 封面本地路径
    poster_path: str = ""
    fanart_path: str = ""
    thumb_path: str = ""
    extrafanart_dir: str = ""

    # 扩展字段 (Jellyfin NFO 支持的 JAV 专用字段)
    extra: Dict[str, Any] = field(default_factory=dict)

    @property
    def catalog_number(self) -> str:
        return self.extra.get("catalog_number", "")

    @property
    def studio(self) -> str:
        return self.extra.get("studio", "")

    @property
    def maker(self) -> str:
        return self.extra.get("maker", "")

    def to_dict(self) -> Dict[str, Any]:
        return {
            "title": self.title,
            "original_title": self.original_title,
            "year": self.year,
            "plot": self.plot,
            "genres": self.genres,
            "director": self.director,
            "actors": self.actors,
            "rating": self.rating,
            "poster_url": self.poster_url,
            "backdrop_url": self.backdrop_url,
            "release_date": self.release_date,
            "video_path": self.video_path,
            "nfo_path": self.nfo_path,
            "poster_path": self.poster_path,
            "fanart_path": self.fanart_path,
            "thumb_path": self.thumb_path,
            "extrafanart_dir": self.extrafanart_dir,
            "catalog_number": self.catalog_number,
            "studio": self.studio,
            "extra": self.extra,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Video":
        extra = data.get("extra", {})
        if "catalog_number" in data:
            extra["catalog_number"] = data["catalog_number"]
        if "studio" in data:
            extra["studio"] = data["studio"]
        if "maker" in data:
            extra["maker"] = data["maker"]

        return cls(
            title=data.get("title", ""),
            original_title=data.get("original_title", ""),
            year=data.get("year", 0),
            plot=data.get("plot", ""),
            genres=data.get("genres", []),
            director=data.get("director", ""),
            actors=data.get("actors", []),
            rating=data.get("rating", 0.0),
            poster_url=data.get("poster_url", ""),
            backdrop_url=data.get("backdrop_url", ""),
            release_date=data.get("release_date", ""),
            video_path=data.get("video_path", ""),
            nfo_path=data.get("nfo_path", ""),
            poster_path=data.get("poster_path", ""),
            fanart_path=data.get("fanart_path", ""),
            thumb_path=data.get("thumb_path", ""),
            extrafanart_dir=data.get("extrafanart_dir", ""),
            extra=extra,
        )
```

**Step 4: Run test to verify it passes**

```bash
pytest tests/test_video.py -v
```

**Step 5: Commit**

```bash
git add src/models/video.py tests/test_video.py
git commit -m "feat: add Video dataclass with extra fields support"
```

---

### Task 4: Create Library Class

**Files:**
- Create: `src/models/library.py`
- Test: `tests/test_library.py`

**Step 1: Write the failing test**

```python
# tests/test_library.py
import sys
import os
import tempfile
import shutil
sys.path.insert(0, "src")

from models.library import Library, Video

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
```

**Step 2: Run test to verify it fails**

```bash
pytest tests/test_library.py -v
```

**Step 3: Write implementation**

```python
# src/models/library.py
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

        # 生成 NFO
        video.nfo_path = os.path.join(video_dir, f"{catalog_number}.nfo")
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
                {"catalog_number": v.catalog_number, "imported_at": v.imported_at}
                for v in videos[-10:]
            ]
        }
```

**Step 4: Run test to verify it passes**

```bash
pytest tests/test_library.py -v
```

**Step 5: Commit**

```bash
git add src/models/library.py tests/test_library.py
git commit -m "feat: add Library class with jsonl indexing"
```

---

## Phase 3: NFO Generator Enhancement

### Task 5: Update NFO Generator for Jellyfin/JAV Format

**Files:**
- Modify: `src/tools/nfo_generator.py`
- Test: `tests/test_nfo_generator.py`

**Step 1: Write the failing test**

```python
# tests/test_nfo_generator.py
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
        open(video_path, "w").close()

        nfo_path = generate_nfo(video, video_path)

        assert os.path.exists(nfo_path)

        # 验证 extra 字段被写入
        data = read_nfo(nfo_path)
        assert data.get("num") == "ABF-061"
        assert data.get("studio") == "Moodyz"
        assert data.get("maker") == "S1 NO.1 STYLE"
    finally:
        shutil.rmtree(tmp)
```

**Step 2: Run test to verify it fails**

```bash
pytest tests/test_nfo_generator.py -v
```

**Step 3: Write implementation**

Update `src/tools/nfo_generator.py` to support extra fields and Jellyfin format:

```python
# src/tools/nfo_generator.py
import os
import xml.etree.ElementTree as ET
from typing import Dict, Any, List
from models.video import Video

def generate_nfo(video: Video, media_path: str = None, media_type: str = "movie") -> str:
    """生成 Jellyfin 兼容的 NFO 文件"""
    root = ET.Element("movie")

    def add_text(parent, tag, text):
        if text:
            elem = ET.SubElement(parent, tag)
            elem.text = str(text)
            return elem
        return None

    # 基础信息
    add_text(root, "title", video.title)
    add_text(root, "originaltitle", video.original_title)
    add_text(root, "year", str(video.year) if video.year else "")
    add_text(root, "plot", video.plot)
    add_text(root, "director", video.director)

    # 评分
    if video.rating:
        add_text(root, "rating", str(video.rating))
        ratings = ET.SubElement(root, "ratings")
        rating_elem = ET.SubElement(ratings, "rating")
        rating_elem.set("name", "javdb")
        rating_elem.set("max", "5")
        rating_elem.set("default", "true")
        value_elem = ET.SubElement(rating_elem, "value")
        value_elem.text = str(video.rating)

    # Genre (Jellyfin uses <genre> tag)
    for g in video.genres:
        add_text(root, "genre", g)

    # Tag (additional categorization)
    for g in video.genres:
        add_text(root, "tag", g)

    # 演员
    for actor_name in video.actors:
        actor_elem = ET.SubElement(root, "actor")
        name_elem = ET.SubElement(actor_elem, "name")
        name_elem.text = actor_name
        type_elem = ET.SubElement(actor_elem, "type")
        type_elem.text = "Actor"

    # 发布日期
    if video.release_date:
        add_text(root, "premiered", video.release_date)
        add_text(root, "releasedate", video.release_date)
        add_text(root, "release", video.release_date)

    # 运行时长 (如果有)
    # poster/fanart/thumb
    if video.poster_path:
        add_text(root, "poster", "poster.jpg")
    if video.fanart_path:
        add_text(root, "fanart", "fanart.jpg")
    if video.thumb_path:
        add_text(root, "thumb", "thumb.jpg")

    # art 标签 (Jellyfin 格式)
    if video.poster_path or video.fanart_path:
        art = ET.SubElement(root, "art")
        if video.poster_path:
            poster_elem = ET.SubElement(art, "poster")
            poster_elem.text = "poster.jpg"
        if video.fanart_path:
            fanart_elem = ET.SubElement(art, "fanart")
            fanart_elem.text = "fanart.jpg"

    # 处理 extra 字段
    extra = video.extra or {}

    # 番號 (num/catalog_number)
    catalog_number = extra.get("catalog_number") or video.catalog_number
    if catalog_number:
        add_text(root, "num", catalog_number)
        add_text(root, "sorttitle", catalog_number)

    # 片商/制作商
    if extra.get("studio"):
        add_text(root, "studio", extra["studio"])
    if extra.get("maker"):
        add_text(root, "maker", extra["maker"])

    # 系列
    if extra.get("series"):
        add_text(root, "set", extra["series"])

    # 标签
    if extra.get("label"):
        add_text(root, "label", extra["label"])

    # 年龄分级
    if extra.get("customrating"):
        add_text(root, "customrating", extra["customrating"])
        add_text(root, "mpaa", extra["customrating"])

    # 封面 URL
    if extra.get("cover"):
        add_text(root, "cover", extra["cover"])

    # 导演
    if extra.get("director"):
        add_text(root, "director", extra["director"])

    # fileinfo (可选，从视频文件读取)
    if video.video_path and os.path.exists(video.video_path):
        fileinfo = ET.SubElement(root, "fileinfo")
        streamdetails = ET.SubElement(fileinfo, "streamdetails")
        # 视频流信息可以后续通过 ffprobe 获取

    # 保存 NFO
    if media_path:
        base_name = os.path.splitext(media_path)[0]
    else:
        base_name = os.path.join(os.path.dirname(video.video_path), catalog_number) if catalog_number else ""

    nfo_path = f"{base_name}.nfo"
    tree = ET.ElementTree(root)
    tree.write(nfo_path, encoding="utf-8", xml_declaration=True)

    return nfo_path


def read_nfo(nfo_path: str) -> Dict[str, Any]:
    """读取 NFO 文件"""
    if not os.path.exists(nfo_path):
        raise FileNotFoundError(f"NFO not found: {nfo_path}")

    tree = ET.parse(nfo_path)
    root = tree.getroot()

    def get_text(tag):
        el = root.find(tag)
        return el.text if el is not None else ""

    def get_all_text(tag):
        return [el.text for el in root.findall(tag) if el.text]

    # 提取 ratings
    rating_elem = root.find(".//rating[@name='javdb']")
    rating_value = ""
    if rating_elem is not None:
        value_elem = rating_elem.find("value")
        if value_elem is not None:
            rating_value = value_elem.text or ""

    return {
        "title": get_text("title"),
        "originaltitle": get_text("originaltitle"),
        "year": get_text("year"),
        "plot": get_text("plot"),
        "rating": rating_value or get_text("rating"),
        "genre": get_all_text("genre"),
        "director": get_text("director"),
        "actors": [a.find("name").text for a in root.findall("actor") if a.find("name") is not None and a.find("name").text],
        "num": get_text("num"),
        "studio": get_text("studio"),
        "maker": get_text("maker"),
        "set": get_text("set"),
        "label": get_text("label"),
        "customrating": get_text("customrating"),
        "cover": get_text("cover"),
        "premiered": get_text("premiered"),
        "runtime": get_text("runtime"),
    }


def update_nfo(nfo_path: str, video: Video) -> str:
    """更新 NFO 文件"""
    if not os.path.exists(nfo_path):
        raise FileNotFoundError(f"NFO not found: {nfo_path}")

    return generate_nfo(video, media_path=nfo_path.replace(".nfo", ".mp4"))
```

**Step 4: Run test to verify it passes**

```bash
pytest tests/test_nfo_generator.py -v
```

**Step 5: Commit**

```bash
git add src/tools/nfo_generator.py tests/test_nfo_generator.py
git commit -m "feat: update NFO generator for Jellyfin/JAV format with extra fields"
```

---

## Phase 4: Download Manager

### Task 6: Create Download Manager with Tracker Update

**Files:**
- Modify: `src/tools/aria2_manager.py`
- Test: `tests/test_download.py`

**Step 1: Write the failing test**

```python
# tests/test_download.py
import sys
sys.path.insert(0, "src")

def test_download_manager_init():
    from tools.download import DownloadManager
    dm = DownloadManager(host="localhost", port=6800, secret="test")
    assert dm.host == "localhost"
    assert dm.port == 6800
```

**Step 2: Run test to verify it fails**

```bash
pytest tests/test_download.py -v
```

**Step 3: Write implementation**

Create `src/tools/download.py`:

```python
# src/tools/download.py
import os
import requests
import subprocess
from typing import List, Dict, Any, Optional
import aria2p

class DownloadManager:
    def __init__(self, host: str = "localhost", port: int = 6800, secret: str = ""):
        if not host.startswith("http"):
            host = f"http://{host}"
        self.host = host
        self.port = port
        self.secret = secret
        self.client = aria2p.API(
            aria2p.Client(host=host, port=port, secret=secret)
        )

    def create_download(self, uri: str, filename: str = None, dir: str = "/downloads") -> Dict[str, Any]:
        """创建下载任务"""
        options = {"dir": dir}
        if filename:
            options["out"] = filename
        download = self.client.add_uris([uri], options=options)
        return {
            "gid": download.gid,
            "name": download.name,
            "status": download.status
        }

    def list_downloads(self, status: str = None) -> List[Dict[str, Any]]:
        """列出下载任务"""
        downloads = self.client.get_downloads()
        if status:
            downloads = [d for d in downloads if d.status == status]
        return [{
            "gid": d.gid,
            "name": d.name,
            "status": d.status,
            "total_length": d.total_length,
            "completed_length": d.completed_length,
            "download_speed": d.download_speed,
            "progress": (d.completed_length / d.total_length * 100) if d.total_length > 0 else 0
        } for d in downloads]

    def pause_download(self, gid: str) -> Dict[str, str]:
        download = self.client.get_download(gid)
        download.pause()
        return {"gid": gid, "status": "paused"}

    def resume_download(self, gid: str) -> Dict[str, str]:
        download = self.client.get_download(gid)
        download.resume()
        return {"gid": gid, "status": "resume"}

    def cancel_download(self, gid: str) -> Dict[str, str]:
        download = self.client.get_download(gid)
        download.remove()
        return {"gid": gid, "status": "removed"}

    def get_download_status(self, gid: str) -> Dict[str, Any]:
        download = self.client.get_download(gid)
        return {
            "gid": download.gid,
            "name": download.name,
            "status": download.status,
            "total_length": download.total_length,
            "completed_length": download.completed_length,
            "download_speed": download.download_speed,
            "upload_speed": download.upload_speed,
            "progress": (download.completed_length / download.total_length * 100) if download.total_length > 0 else 0,
            "error_message": download.error_message
        }

    def get_bt_trackers(self) -> List[str]:
        """获取 BT tracker 列表"""
        opts = self.client.get_global_options()
        return opts.get("bt-tracker", "").split(",") if opts.get("bt-tracker") else []

    def update_bt_trackers(self, source_url: str = "https://raw.githubusercontent.com/ngosang/trackerslist/master/trackers_best.txt") -> Dict[str, Any]:
        """从 URL 获取并更新 BT tracker 列表"""
        try:
            response = requests.get(source_url, timeout=30)
            response.raise_for_status()
            trackers = [t.strip() for t in response.text.strip().split("\n") if t.strip()]
            tracker_str = ",".join(trackers)
            self.client.set_global_options({"bt-tracker": tracker_str})
            return {"trackers": trackers, "count": len(trackers)}
        except Exception as e:
            return {"error": str(e), "trackers": [], "count": 0}

    def restart_aria2(self) -> Dict[str, str]:
        """重启 aria2 服务"""
        try:
            subprocess.run(["pkill", "-HUP", "aria2c"], check=True)
            return {"status": "restarted"}
        except subprocess.CalledProcessError:
            return {"status": "failed", "error": "Failed to restart aria2"}

    def get_global_options(self) -> Dict[str, Any]:
        """获取全局配置"""
        opts = self.client.get_global_options()
        if isinstance(opts, dict):
            return opts
        return opts.get_struct() if hasattr(opts, 'get_struct') else opts._struct

    def set_speed_limit(self, download_limit: str = None, upload_limit: str = None) -> Dict[str, str]:
        """设置速度限制"""
        options = {}
        if download_limit:
            options["max-download-limit"] = download_limit
        if upload_limit:
            options["max-upload-limit"] = upload_limit
        if options:
            self.client.set_global_options(options)
        return options
```

**Step 4: Run test to verify it passes**

```bash
pytest tests/test_download.py -v
```

**Step 5: Commit**

```bash
git add src/tools/download.py tests/test_download.py
git commit -m "feat: create DownloadManager with tracker update support"
```

---

## Phase 5: MCP Tools

### Task 7: Rewrite main.py with New MCP Tools

**Files:**
- Modify: `src/main.py`

**Step 1: Write the implementation**

Rewrite `src/main.py` with new tool definitions:

```python
# src/main.py
import os
import sys
from pathlib import Path
from typing import List, Dict, Any

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import JSONResponse

sys.path.insert(0, str(Path(__file__).parent))

from mcp.server import FastMCP
from mcp.server.transport_security import TransportSecuritySettings
from config import Config
from models.library import Library
from tools.download import DownloadManager
from tools.nfo_generator import generate_nfo, read_nfo, update_nfo
from models.video import Video

config = Config()

# Token authentication middleware
class TokenAuthMiddleware(BaseHTTPMiddleware):
    def __init__(self, app, token: str = None):
        super().__init__(app)
        self.token = token

    async def dispatch(self, request: Request, call_next):
        if not self.token:
            return await call_next(request)
        auth_header = request.headers.get("Authorization", "")
        if auth_header.startswith("Bearer "):
            token = auth_header[7:]
            if token == self.token:
                return await call_next(request)
        query_token = request.query_params.get("token")
        if query_token == self.token:
            return await call_next(request)
        return JSONResponse(
            {"error": "Unauthorized", "message": "Invalid or missing token"},
            status_code=401
        )

# Initialize managers
download_manager = DownloadManager(
    host=config.aria2_rpc_host,
    port=config.aria2_rpc_port,
    secret=config.aria2_secret
)

library = Library(
    media_dir=config.media_dir,
    index_path=config.index_path
)

mcp = FastMCP(
    "media-mcp",
    host="0.0.0.0",
    transport_security=TransportSecuritySettings(
        enable_dns_rebinding_protection=False,
    ),
)

# === Download Management Tools ===

@mcp.tool()
def create_download(uri: str, filename: str = None, dir: str = None) -> Dict[str, Any]:
    """创建下载任务"""
    if dir is None:
        dir = config.download_dir
    return download_manager.create_download(uri, filename, dir)

@mcp.tool()
def list_downloads(status: str = None) -> List[Dict[str, Any]]:
    """列出下载任务"""
    return download_manager.list_downloads(status)

@mcp.tool()
def pause_download(gid: str) -> Dict[str, str]:
    """暂停下载"""
    return download_manager.pause_download(gid)

@mcp.tool()
def resume_download(gid: str) -> Dict[str, str]:
    """恢复下载"""
    return download_manager.resume_download(gid)

@mcp.tool()
def cancel_download(gid: str) -> Dict[str, str]:
    """取消下载"""
    return download_manager.cancel_download(gid)

@mcp.tool()
def get_download_status(gid: str) -> Dict[str, Any]:
    """获取下载状态"""
    return download_manager.get_download_status(gid)

@mcp.tool()
def get_bt_trackers() -> List[str]:
    """获取当前 BT tracker 列表"""
    return download_manager.get_bt_trackers()

@mcp.tool()
def update_bt_trackers(source_url: str = "https://raw.githubusercontent.com/ngosang/trackerslist/master/trackers_best.txt") -> Dict[str, Any]:
    """从 GitHub 更新 BT tracker 列表并重启 aria2"""
    result = download_manager.update_bt_trackers(source_url)
    if result.get("count", 0) > 0:
        download_manager.restart_aria2()
    return result

@mcp.tool()
def restart_aria2() -> Dict[str, str]:
    """重启 aria2 服务"""
    return download_manager.restart_aria2()

# === Library Management Tools ===

@mcp.tool()
def scan_source_dir(source_dir: str) -> List[Dict[str, Any]]:
    """扫描源目录，返回未入库的视频文件列表"""
    return library.scan_source_dir(source_dir)

@mcp.tool()
def import_video(metadata: Dict[str, Any], video_path: str = None) -> Dict[str, Any]:
    """导入影片到媒体库"""
    video = Video.from_dict(metadata)
    if not video.catalog_number:
        return {"error": "catalog_number is required"}
    imported = library.import_video(video, source_path=video_path)

    # 生成 NFO
    if imported.video_path:
        try:
            imported.nfo_path = generate_nfo(imported, imported.video_path)
        except Exception as e:
            return {"error": str(e), "catalog_number": imported.catalog_number}

    # 下载封面 (如果提供了 poster_url)
    if imported.poster_url:
        try:
            from PIL import Image
            from io import BytesIO
            import requests
            resp = requests.get(imported.poster_url, timeout=30)
            img = Image.open(BytesIO(resp.content))
            img.save(imported.poster_path)
        except Exception:
            pass  # 忽略封面下载失败

    return {
        "catalog_number": imported.catalog_number,
        "status": "imported",
        "video_path": imported.video_path,
        "nfo_path": imported.nfo_path,
    }

@mcp.tool()
def list_library_videos() -> List[Dict[str, Any]]:
    """列出库中所有影片"""
    return [v.to_dict() for v in library.list_videos()]

@mcp.tool()
def get_video(catalog_number: str) -> Dict[str, Any]:
    """获取指定影片信息"""
    video = library.get_video(catalog_number)
    if video:
        return video.to_dict()
    return {"error": "not found"}

@mcp.tool()
def search_videos(query: str) -> List[Dict[str, Any]]:
    """搜索影片"""
    return [v.to_dict() for v in library.search(query)]

@mcp.tool()
def get_library_stats() -> Dict[str, Any]:
    """获取媒体库统计信息"""
    return library.get_stats()

@mcp.tool()
def remove_video(catalog_number: str) -> Dict[str, str]:
    """从库中移除影片"""
    success = library.remove_video(catalog_number)
    if success:
        return {"catalog_number": catalog_number, "status": "removed"}
    return {"catalog_number": catalog_number, "error": "not found"}

@mcp.tool()
def update_video_metadata(catalog_number: str, metadata: Dict[str, Any]) -> Dict[str, str]:
    """更新影片元数据"""
    video = library.get_video(catalog_number)
    if not video:
        return {"error": "not found"}

    # 合并更新
    for key, value in metadata.items():
        if hasattr(video, key):
            setattr(video, key, value)
        else:
            video.extra[key] = value

    # 重新生成 NFO
    if video.nfo_path and os.path.exists(os.path.dirname(video.nfo_path)):
        update_nfo(video.nfo_path, video)

    return {"catalog_number": catalog_number, "status": "updated"}

@mcp.tool()
def download_poster(catalog_number: str, poster_url: str) -> Dict[str, str]:
    """下载封面图片"""
    video = library.get_video(catalog_number)
    if not video:
        return {"error": "not found"}

    try:
        from PIL import Image
        from io import BytesIO
        import requests
        resp = requests.get(poster_url, timeout=30)
        img = Image.open(BytesIO(resp.content))
        poster_path = os.path.join(library.media_dir, catalog_number, "poster.jpg")
        os.makedirs(os.path.dirname(poster_path), exist_ok=True)
        img.save(poster_path)
        return {"poster_path": poster_path}
    except Exception as e:
        return {"error": str(e)}

@mcp.tool()
def read_nfo_file(nfo_path: str) -> Dict[str, Any]:
    """读取 NFO 文件"""
    return read_nfo(nfo_path)

if __name__ == "__main__":
    import uvicorn

    app = mcp.streamable_http_app()

    auth_token = os.environ.get("MCP_AUTH_TOKEN", os.environ.get("ARIA2_RPC_SECRET", ""))
    if auth_token:
        app.add_middleware(TokenAuthMiddleware, token=auth_token)

    uvicorn.run(
        app,
        host=config.server_host,
        port=config.server_port
    )
```

**Step 2: Commit**

```bash
git add src/main.py
git commit -m "feat: rewrite main.py with new MCP tools"
```

---

## Phase 6: Config Updates

### Task 8: Update Config Class

**Files:**
- Modify: `src/config.py`

**Step 1: Update config.py**

Add new config properties and remove scrapers:

```python
# src/config.py
import os
import yaml
from pathlib import Path

class Config:
    def __init__(self, config_path: str = "config.yaml"):
        self.config_path = config_path
        self._config = self._load_config()

    def _load_config(self) -> dict:
        if not Path(self.config_path).exists():
            return self._default_config()
        with open(self.config_path, 'r', encoding='utf-8') as f:
            return yaml.safe_load(f)

    def _default_config(self) -> dict:
        return {
            "server": {"host": "0.0.0.0", "port": 8000},
            "aria2": {"rpc_host": "localhost", "rpc_port": 6800, "rpc_secret": ""},
            "paths": {
                "media_dir": "/media/jav/JAV_output",
                "download_dir": "/downloads",
                "source_dir": "/media/jav",
                "index_path": "/app/config/library_index.jsonl"
            },
            "bt_tracker": {
                "update_url": "https://raw.githubusercontent.com/ngosang/trackerslist/master/trackers_best.txt"
            }
        }

    @property
    def server_host(self) -> str:
        return self._config.get("server", {}).get("host", "0.0.0.0")

    @property
    def server_port(self) -> int:
        return self._config.get("server", {}).get("port", 8000)

    @property
    def media_dir(self) -> str:
        return os.environ.get("MEDIA_DIR", self._config.get("paths", {}).get("media_dir", "/media/jav/JAV_output"))

    @property
    def download_dir(self) -> str:
        return os.environ.get("DOWNLOAD_DIR", self._config.get("paths", {}).get("download_dir", "/downloads"))

    @property
    def source_dir(self) -> str:
        return os.environ.get("SOURCE_DIR", self._config.get("paths", {}).get("source_dir", "/media/jav"))

    @property
    def index_path(self) -> str:
        return os.environ.get("INDEX_PATH", self._config.get("paths", {}).get("index_path", "/app/config/library_index.jsonl"))

    @property
    def aria2_rpc_host(self) -> str:
        return os.environ.get("ARIA2_RPC_HOST", self._config.get("aria2", {}).get("rpc_host", "localhost"))

    @property
    def aria2_rpc_port(self) -> int:
        return os.environ.get("ARIA2_RPC_PORT", self._config.get("aria2", {}).get("rpc_port", 6800))

    @property
    def aria2_secret(self) -> str:
        return os.environ.get("ARIA2_RPC_SECRET", self._config.get("aria2", {}).get("rpc_secret", ""))

    @property
    def bt_tracker_url(self) -> str:
        return self._config.get("bt_tracker", {}).get("update_url",
            "https://raw.githubusercontent.com/ngosang/trackerslist/master/trackers_best.txt")
```

**Step 2: Commit**

```bash
git add src/config.py
git commit -m "feat: update Config with new paths and bt_tracker settings"
```

---

### Task 9: Update config.yaml

**Files:**
- Modify: `config.yaml`

**Step 1: Update config.yaml**

```yaml
server:
  host: "0.0.0.0"
  port: 8000

aria2:
  rpc_host: "localhost"
  rpc_port: 6800
  rpc_secret: ""

paths:
  media_dir: "/media/jav/JAV_output"
  download_dir: "/downloads"
  source_dir: "/media/jav"
  index_path: "/app/config/library_index.jsonl"

bt_tracker:
  update_url: "https://raw.githubusercontent.com/ngosang/trackerslist/master/trackers_best.txt"
```

**Step 2: Commit**

```bash
git add config.yaml
git commit -m "feat: update config.yaml with new paths and bt_tracker settings"
```

---

### Task 10: Update Dockerfile

**Files:**
- Modify: `Dockerfile`

**Step 1: Update Dockerfile**

```dockerfile
FROM python:3.11-slim

# Install aria2
RUN apt-get update && apt-get install -y aria2 && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Copy requirements first for better caching
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application
COPY src/ ./src/
COPY config.yaml .

# Create directories and config directory
RUN mkdir -p /media/jav/JAV_output /downloads /media/jav /app/config

ENV PYTHONUNBUFFERED=1
ENV ARIA2_RPC_SECRET=${ARIA2_RPC_SECRET:-}
ENV MCP_AUTH_TOKEN=${MCP_AUTH_TOKEN:-}

# Entry point: start aria2c then MCP server
CMD ["sh", "-c", "aria2c --enable-rpc --rpc-listen-all --rpc-listen-port=6800 --rpc-allow-origin-all $([ -n \"$ARIA2_RPC_SECRET\" ] && echo --rpc-secret=$ARIA2_RPC_SECRET) --quiet & python -m src.main"]
```

**Step 2: Commit**

```bash
git add Dockerfile
git commit -m "feat: update Dockerfile for new paths"
```

---

### Task 11: Update docker-compose.yaml

**Files:**
- Modify: `docker-compose.yaml`

**Step 1: Update docker-compose.yaml**

```yaml
version: '3.8'

services:
  media-mcp:
    build: .
    container_name: media-mcp
    volumes:
      - ./config:/app/config
      - media:/media/jav
      - downloads:/downloads
    ports:
      - "8000:8000"
    environment:
      - MEDIA_DIR=/media/jav
      - DOWNLOAD_DIR=/downloads
      - SOURCE_DIR=/media/jav
      - INDEX_PATH=/app/config/library_index.jsonl
      - ARIA2_RPC_SECRET=${ARIA2_RPC_SECRET:-}
      - MCP_AUTH_TOKEN=${MCP_AUTH_TOKEN:-${ARIA2_RPC_SECRET:-}}
    restart: unless-stopped

volumes:
  media:
  downloads:
```

**Step 2: Commit**

```bash
git add docker-compose.yaml
git commit -m "feat: update docker-compose for new paths"
```

---

## Phase 7: CLI

### Task 12: Create CLI Commands

**Files:**
- Create: `src/cli/commands.py`
- Create: `src/__main__.py` (entry point)

**Step 1: Write implementation**

```python
# src/cli/commands.py
import click
import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from models.library import Library
from config import Config

config = Config()
library = Library(media_dir=config.media_dir, index_path=config.index_path)


@click.group()
def cli():
    """Media MCP CLI - Media library management tool"""
    pass


@cli.command()
@click.option("--source", "-s", required=True, help="Source directory to scan")
def scan(source):
    """Scan source directory for new videos"""
    results = library.scan_source_dir(source)
    if not results:
        click.echo("No new videos found.")
        return
    click.echo(f"Found {len(results)} new videos:")
    for r in results:
        click.echo(f"  {r['filename']} ({r['catalog_number'] or 'unknown'}) - {r['size']} bytes")


@cli.command()
@click.option("--source", "-s", required=True, help="Source video path")
@click.option("--metadata", "-m", required=True, help="Metadata JSON string")
def import_video(source, metadata):
    """Import a single video with metadata"""
    import json
    from models.video import Video

    metadata_dict = json.loads(metadata)
    video = Video.from_dict(metadata_dict)

    if not video.catalog_number:
        click.echo("Error: catalog_number is required", err=True)
        return

    try:
        imported = library.import_video(video, source_path=source)
        click.echo(f"Successfully imported {video.catalog_number}")
        click.echo(f"  Video: {imported.video_path}")
        click.echo(f"  NFO: {imported.nfo_path}")
    except Exception as e:
        click.echo(f"Error: {e}", err=True)


@cli.command()
@click.option("--source", "-s", required=True, help="Source directory")
def batch_import(source):
    """Batch import all videos from source directory"""
    results = library.scan_source_dir(source)
    if not results:
        click.echo("No new videos to import.")
        return

    click.echo(f"Found {len(results)} videos. This tool only scans - use LLM Agent for metadata scraping.")


@cli.command()
def list_videos():
    """List all videos in library"""
    videos = library.list_videos()
    if not videos:
        click.echo("Library is empty.")
        return
    click.echo(f"Library has {len(videos)} videos:")
    for v in videos:
        click.echo(f"  {v.catalog_number} - {v.title}")


@cli.command()
@click.option("--media-dir", help="Media library directory")
def rebuild_index(media_dir):
    """Rebuild library index from existing files"""
    if not media_dir:
        media_dir = config.media_dir

    click.echo(f"Scanning {media_dir} for existing videos...")
    # TODO: implement index rebuild
    click.echo("Index rebuild not yet implemented.")


@cli.command()
def stats():
    """Show library statistics"""
    stats = library.get_stats()
    click.echo(f"Total videos: {stats['total']}")
    if stats['recent_imports']:
        click.echo("Recent imports:")
        for r in stats['recent_imports']:
            click.echo(f"  {r['catalog_number']} - {r['imported_at']}")


# Register all commands
cli.add_command(scan)
cli.add_command(import_video)
cli.add_command(batch_import)
cli.add_command(list_videos)
cli.add_command(rebuild_index)
cli.add_command(stats)
```

```python
# src/__main__.py
from cli.commands import cli
if __name__ == "__main__":
    cli()
```

**Step 2: Commit**

```bash
git add src/cli/commands.py src/__main__.py
git commit -m "feat: add CLI commands"
```

---

## Phase 8: Cleanup & Tests

### Task 13: Update requirements.txt

**Files:**
- Modify: `requirements.txt`

**Step 1: Update requirements.txt**

```
mcp>=1.0.0
aria2p>=0.3.0
requests>=2.31.0
python-dotenv>=1.0.0
pyyaml>=6.0
pillow>=10.0.0
click>=8.1.0
```

**Step 2: Commit**

```bash
git add requirements.txt
git commit -m "feat: update requirements - add click"
```

---

### Task 14: Final Verification

**Step 1: Run all tests**

```bash
pytest tests/ -v
```

**Step 2: Verify imports work**

```bash
python -c "from src.models.video import Video; from src.models.library import Library; print('OK')"
```

**Step 3: Commit**

```bash
git commit -m "chore: verify all imports and tests pass"
```

---

## Summary

### Task Order

1. Create Directory Structure
2. Remove Old Files
3. Create Video Dataclass
4. Create Library Class
5. Update NFO Generator
6. Create Download Manager
7. Rewrite main.py
8. Update Config
9. Update config.yaml
10. Update Dockerfile
11. Update docker-compose.yaml
12. Create CLI Commands
13. Update requirements.txt
14. Final Verification

### Post-Implementation Notes

- The JAV scraping capability (scrapling + Playwright) should be extracted into a separate MCP/Skill that runs on a machine with sufficient resources
- LLM Agent will use that skill to scrape metadata, then call the MCP tools to import into the library
- BT tracker auto-update data source: `https://raw.githubusercontent.com/ngosang/trackerslist/master/trackers_best.txt`
