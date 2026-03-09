# Media MCP Server 实现计划

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** 实现一个运行在 Docker 容器中的 MCP 服务器，用于管理多媒体库，支持元数据生成和 Aria2 下载管理。

**Architecture:** 基于 FastMCP 框架，使用 Streamable HTTP 协议。Aria2 内置运行在同一容器，通过 RPC 调用。保持原有文件夹结构，元数据就近生成。

**Tech Stack:** Python 3.11, FastMCP, aria2p, tmdb3api, ElementTree (NFO)

---

## 阶段 1: 项目基础架构

### Task 1: 创建项目结构和配置文件

**Files:**
- Create: `requirements.txt`
- Create: `config.yaml`
- Create: `.env.example`

**Step 1: 创建 requirements.txt**

```txt
fastmcp>=0.1.0
aria2p>=0.3.0
tmdb3api>=2.1.0
requests>=2.31.0
python-dotenv>=1.0.0
pyyaml>=6.0
pillow>=10.0.0
```

**Step 2: 创建 config.yaml**

```yaml
server:
  host: "0.0.0.0"
  port: 8000

aria2:
  rpc_host: "localhost"
  rpc_port: 6800
  rpc_secret: ""

paths:
  media_dir: "/media"
  download_dir: "/downloads"

scrapers:
  tmdb:
    api_key: ""
  tvdb:
    api_key: ""
  douban:
    enabled: false
```

**Step 3: 创建 .env.example**

```bash
ARIA2_RPC_SECRET=your_secret_here
TMDB_API_KEY=your_tmdb_key
TVDB_API_KEY=your_tvdb_key
```

**Step 4: Commit**

```bash
git add requirements.txt config.yaml .env.example
git commit -m "chore: add project configuration files"
```

---

### Task 2: 创建 MCP 主入口和基础结构

**Files:**
- Create: `src/__init__.py`
- Create: `src/main.py`
- Create: `src/config.py`

**Step 1: 创建 src/__init__.py**

```python
"""Media MCP Server - 多媒体库管理 MCP 服务"""
```

**Step 2: 创建 src/config.py**

```python
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
            "paths": {"media_dir": "/media", "download_dir": "/downloads"},
            "scrapers": {"tmdb": {"api_key": ""}, "tvdb": {"api_key": ""}, "douban": {"enabled": False}}
        }

    @property
    def media_dir(self) -> str:
        return os.environ.get("MEDIA_DIR", self._config.get("paths", {}).get("media_dir", "/media"))

    @property
    def download_dir(self) -> str:
        return os.environ.get("DOWNLOAD_DIR", self._config.get("paths", {}).get("download_dir", "/downloads"))

    @property
    def aria2_secret(self) -> str:
        return os.environ.get("ARIA2_RPC_SECRET", self._config.get("aria2", {}).get("rpc_secret", ""))

    @property
    def tmdb_api_key(self) -> str:
        return os.environ.get("TMDB_API_KEY", self._config.get("scrapers", {}).get("tmdb", {}).get("api_key", ""))
```

**Step 3: 创建 src/main.py**

```python
import os
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent))

from fastmcp import FastMCP
from config import Config

config = Config()

mcp = FastMCP("media-mcp")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        mcp.streamable_http_app(),
        host=config._config.get("server", {}).get("host", "0.0.0.0"),
        port=config._config.get("server", {}).get("port", 8000)
    )
```

**Step 4: Commit**

```bash
git add src/__init__.py src/main.py src/config.py
git commit -m "feat: create MCP main entry and config module"
```

---

## 阶段 2: 文件操作接口

### Task 3: 实现基础文件操作工具

**Files:**
- Create: `src/tools/file_ops.py`
- Test: `tests/test_file_ops.py`

**Step 1: 写测试**

```python
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
```

**Step 2: 运行测试（预期失败）**

```bash
pytest tests/test_file_ops.py -v
Expected: FAIL - module not found
```

**Step 3: 实现 src/tools/file_ops.py**

```python
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
```

**Step 4: 运行测试**

```bash
pytest tests/test_file_ops.py -v
Expected: PASS
```

**Step 5: Commit**

```bash
git add src/tools/file_ops.py tests/test_file_ops.py
git commit -m "feat: implement file operation tools"
```

---

### Task 4: 实现 MCP 文件操作接口

**Files:**
- Modify: `src/main.py`

**Step 1: 添加 MCP 接口到 main.py**

```python
from src.tools.file_ops import list_dir, move_file, copy_file, delete_file, create_dir, get_file_info

@mcp.tool()
def list_dir(path: str) -> List[Dict[str, Any]]:
    """列出目录内容"""
    return list_dir(path)

@mcp.tool()
def move_file(src: str, dst: str) -> Dict[str, str]:
    """移动/重命名文件"""
    return move_file(src, dst)

# ... add other tools similarly
```

**Step 2: Commit**

```bash
git add src/main.py
git commit -m "feat: add file operation MCP tools"
```

---

## 阶段 3: 媒体库扫描

### Task 5: 实现媒体库扫描功能

**Files:**
- Create: `src/tools/media_scanner.py`
- Test: `tests/test_media_scanner.py`

**Step 1: 写测试**

```python
import pytest
import os
import tempfile
import shutil

from src.tools.media_scanner import scan_media_library, MEDIA_EXTENSIONS

def test_scan_media_library(temp_dir):
    # Create test media files
    os.makedirs(os.path.join(temp_dir, "movie1"))
    open(os.path.join(temp_dir, "movie1", "movie1.mp4"), "w").write("video")
    open(os.path.join(temp_dir, "movie1", "poster.jpg"), "w").write("image")

    result = scan_media_library(temp_dir)
    assert len(result) >= 1
    assert any(r["name"].endswith(".mp4") for r in result)
```

**Step 2: 实现 src/tools/media_scanner.py**

```python
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
```

**Step 3: 测试并提交**

```bash
pytest tests/test_media_scanner.py -v
git add src/tools/media_scanner.py tests/test_media_scanner.py
git commit -m "feat: implement media library scanner"
```

---

## 阶段 4: Aria2 下载管理

### Task 6: 实现 Aria2 工具类

**Files:**
- Create: `src/tools/aria2_manager.py`

**Step 1: 实现 aria2_manager.py**

```python
import aria2p
from typing import List, Dict, Any, Optional
from dataclasses import dataclass

@dataclass
class DownloadInfo:
    gid: str
    name: str
    status: str
    total_length: int
    completed_length: int
    download_speed: int
    upload_speed: int
    files: List[str]

class Aria2Manager:
    def __init__(self, host: str = "localhost", port: int = 6800, secret: str = ""):
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
        """暂停下载"""
        download = self.client.get_download(gid)
        download.pause()
        return {"gid": gid, "status": "paused"}

    def resume_download(self, gid: str) -> Dict[str, str]:
        """恢复下载"""
        download = self.client.get_download(gid)
        download.resume()
        return {"gid": gid, "status": "resume"}

    def cancel_download(self, gid: str) -> Dict[str, str]:
        """取消下载"""
        download = self.client.get_download(gid)
        download.remove()
        return {"gid": gid, "status": "removed"}

    def get_download_status(self, gid: str) -> Dict[str, Any]:
        """获取下载状态"""
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

    def get_global_options(self) -> Dict[str, Any]:
        """获取全局配置"""
        return self.client.get_global_options()

    def set_global_options(self, options: Dict[str, Any]) -> Dict[str, Any]:
        """设置全局配置"""
        self.client.set_global_options(options)
        return options

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

    def get_bt_trackers(self) -> List[str]:
        """获取 BT tracker 列表"""
        opts = self.client.get_global_options()
        return opts.get("bt-tracker", "").split(",") if opts.get("bt-tracker") else []

    def update_bt_trackers(self, trackers: List[str]) -> Dict[str, Any]:
        """更新 BT tracker 列表"""
        tracker_str = ",".join(trackers)
        self.client.set_global_options({"bt-tracker": tracker_str})
        return {"trackers": trackers}
```

**Step 2: Commit**

```bash
git add src/tools/aria2_manager.py
git commit -m "feat: implement Aria2 manager"
```

---

### Task 7: 实现 MCP 下载管理接口

**Files:**
- Modify: `src/main.py`

**Step 1: 添加下载管理 MCP 接口**

```python
from src.tools.aria2_manager import Aria2Manager
from src.config import Config

config = Config()
aria2_manager = Aria2Manager(
    host="localhost",
    port=6800,
    secret=config.aria2_secret
)

@mcp.tool()
def create_download(uri: str, filename: str = None, dir: str = None) -> Dict[str, Any]:
    """创建下载任务"""
    if dir is None:
        dir = config.download_dir
    return aria2_manager.create_download(uri, filename, dir)

@mcp.tool()
def list_downloads(status: str = None) -> List[Dict[str, Any]]:
    """列出下载任务"""
    return aria2_manager.list_downloads(status)

# ... add pause, resume, cancel, get_status
```

**Step 2: Commit**

```bash
git add src/main.py
git commit -m "feat: add download management MCP tools"
```

---

## 阶段 5: 元数据管理

### Task 8: 实现削刮器

**Files:**
- Create: `src/scrapers/__init__.py`
- Create: `src/scrapers/base.py`
- Create: `src/scrapers/tmdb_scraper.py`
- Create: `src/scrapers/tvdb_scraper.py`
- Create: `src/scrapers/douban_scraper.py`

**Step 1: 创建 src/scrapers/base.py**

```python
from abc import ABC, abstractmethod
from typing import Dict, Any, List, Optional
from dataclasses import dataclass

@dataclass
class MediaMetadata:
    title: str
    original_title: str = ""
    year: int = 0
    plot: str = ""
    genre: List[str] = None
    director: str = ""
    actors: List[str] = None
    rating: float = 0.0
    poster_url: str = ""
    backdrop_url: str = ""
    imdb_id: str = ""
    tmdb_id: str = ""

    def __post_init__(self):
        if self.genre is None:
            self.genre = []
        if self.actors is None:
            self.actors = []

class BaseScraper(ABC):
    @abstractmethod
    def search(self, query: str, year: int = None) -> List[MediaMetadata]:
        """搜索媒体"""
        pass

    @abstractmethod
    def get_details(self, media_id: str) -> MediaMetadata:
        """获取详情"""
        pass
```

**Step 2: 创建 src/scrapers/tmdb_scraper.py**

```python
import requests
from typing import List, Dict, Any
from .base import BaseScraper, MediaMetadata

class TMDbScraper(BaseScraper):
    def __init__(self, api_key: str):
        self.api_key = api_key
        self.base_url = "https://api.themoviedb.org/3"

    def search(self, query: str, year: int = None) -> List[MediaMetadata]:
        params = {"api_key": self.api_key, "query": query}
        if year:
            params["primary_release_year"] = year

        resp = requests.get(f"{self.base_url}/search/movie", params=params)
        data = resp.json()

        results = []
        for item in data.get("results", [])[:10]:
            results.append(MediaMetadata(
                title=item.get("title", ""),
                original_title=item.get("original_title", ""),
                year=int(item.get("release_date", "")[:4]) if item.get("release_date") else 0,
                plot=item.get("overview", ""),
                rating=item.get("vote_average", 0.0),
                poster_url=f"https://image.tmdb.org/t/p/w500{item.get('poster_path')}" if item.get("poster_path") else "",
                backdrop_url=f"https://image.tmdb.org/t/p/w1280{item.get('backdrop_path')}" if item.get("backdrop_path") else "",
                tmdb_id=str(item.get("id", ""))
            ))
        return results

    def get_details(self, media_id: str) -> MediaMetadata:
        resp = requests.get(f"{self.base_url}/movie/{media_id}", params={"api_key": self.api_key})
        data = resp.json()

        return MediaMetadata(
            title=data.get("title", ""),
            original_title=data.get("original_title", ""),
            year=int(data.get("release_date", "")[:4]) if data.get("release_date") else 0,
            plot=data.get("overview", ""),
            genre=[g["name"] for g in data.get("genres", [])],
            director="",  # Need credits API
            rating=data.get("vote_average", 0.0),
            poster_url=f"https://image.tmdb.org/t/p/w500{data.get('poster_path')}" if data.get("poster_path") else "",
            tmdb_id=str(data.get("id", ""))
        )
```

**Step 3: 类似实现 TVDB 和豆瓣削刮器**

**Step 4: Commit**

```bash
git add src/scrapers/
git commit -m "feat: implement metadata scrapers"
```

---

### Task 9: 实现 NFO 生成器

**Files:**
- Create: `src/tools/nfo_generator.py`

**Step 1: 实现 nfo_generator.py**

```python
import os
import xml.etree.ElementTree as ET
from typing import Dict, Any
from dataclasses import dataclass, asdict
from src.scrapers.base import MediaMetadata

def generate_nfo(metadata: MediaMetadata, media_path: str, media_type: str = "movie") -> str:
    """生成 NFO 文件"""
    root = ET.Element("item")

    # 基础信息
    title = ET.SubElement(root, "title")
    title.text = metadata.title

    originaltitle = ET.SubElement(root, "originaltitle")
    originaltitle.text = metadata.original_title

    year = ET.SubElement(root, "year")
    year.text = str(metadata.year) if metadata.year else ""

    plot = ET.SubElement(root, "plot")
    plot.text = metadata.plot

    # 评分
    rating = ET.SubElement(root, "rating")
    rating.text = str(metadata.rating)

    # Genre
    for g in metadata.genre:
        genre = ET.SubElement(root, "genre")
        genre.text = g

    # 导演
    if metadata.director:
        director = ET.SubElement(root, "director")
        director.text = metadata.director

    # 演员
    for actor in metadata.actors:
        actor_elem = ET.SubElement(root, "actor")
        name = ET.SubElement(actor_elem, "name")
        name.text = actor

    # 媒体信息
    if metadata.tmdb_id:
        tmdbid = ET.SubElement(root, "tmdbid")
        tmdbid.text = metadata.tmdb_id

    if metadata.imdb_id:
        imdbid = ET.SubElement(root, "imdbid")
        imdbid.text = metadata.imdb_id

    # 保存 NFO
    base_name = os.path.splitext(media_path)[0]
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

    def get_text(element, tag):
        el = root.find(tag)
        return el.text if el is not None else ""

    def get_all_text(element, tag):
        return [el.text for el in root.findall(tag) if el.text]

    return {
        "title": get_text(root, "title"),
        "originaltitle": get_text(root, "originaltitle"),
        "year": get_text(root, "year"),
        "plot": get_text(root, "plot"),
        "rating": get_text(root, "rating"),
        "genre": get_all_text(root, "genre"),
        "director": get_text(root, "director"),
        "actors": [a.find("name").text for a in root.findall("actor") if a.find("name") is not None],
        "tmdbid": get_text(root, "tmdbid"),
        "imdbid": get_text(root, "imdbid")
    }
```

**Step 2: Commit**

```bash
git add src/tools/nfo_generator.py
git commit -m "feat: implement NFO generator"
```

---

### Task 10: 实现 MCP 元数据接口

**Files:**
- Modify: `src/main.py`

**Step 1: 添加元数据 MCP 接口**

```python
from src.scrapers.tmdb_scraper import TMDbScraper
from src.tools.nfo_generator import generate_nfo, read_nfo

config = Config()
tmdb_scraper = TMDbScraper(config.tmdb_api_key)

@mcp.tool()
def scrape_metadata(filename: str, source: str = "tmdb", year: int = None) -> List[Dict[str, Any]]:
    """在线削刮元数据"""
    query = os.path.splitext(os.path.basename(filename))[0]

    if source == "tmdb":
        return [asdict(m) for m in tmdb_scraper.search(query, year)]
    # ... other scrapers

@mcp.tool()
def manual_metadata(media_path: str, metadata: Dict[str, Any]) -> str:
    """手动填写元数据并写入 nfo"""
    meta = MediaMetadata(**metadata)
    return generate_nfo(meta, media_path)

@mcp.tool()
def download_poster(poster_url: str, media_path: str) -> str:
    """下载封面图片"""
    import requests
    from PIL import Image
    from io import BytesIO

    resp = requests.get(poster_url)
    img = Image.open(BytesIO(resp.content))

    base_name = os.path.splitext(media_path)[0]
    poster_path = f"{base_name}-poster.jpg"

    img.save(poster_path)
    return poster_path

@mcp.tool()
def read_nfo_file(nfo_path: str) -> Dict[str, Any]:
    """读取 NFO 文件"""
    return read_nfo(nfo_path)

@mcp.tool()
def update_nfo(nfo_path: str, metadata: Dict[str, Any]) -> str:
    """更新 NFO 文件"""
    meta = MediaMetadata(**metadata)
    # 读取原 NFO，更新后重新写入
    return generate_nfo(meta, nfo_path.replace(".nfo", ".mkv"))  # 根据实际情况调整
```

**Step 2: Commit**

```bash
git add src/main.py
git commit -m "feat: add metadata MCP tools"
```

---

## 阶段 6: Docker 配置

### Task 11: 创建 Docker 配置

**Files:**
- Create: `Dockerfile`
- Create: `docker-compose.yaml`

**Step 1: 创建 Dockerfile**

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

# Create directories
RUN mkdir -p /media /downloads

ENV PYTHONUNBUFFERED=1

# Entry point: start aria2c then MCP server
CMD ["sh", "-c", "aria2c --enable-rpc --rpc-listen-all --rpc-listen-port=6800 --rpc-allow-origin-all --quiet & python -m src.main"]
```

**Step 2: 创建 docker-compose.yaml**

```yaml
version: '3.8'

services:
  media-mcp:
    build: .
    container_name: media-mcp
    volumes:
      - ./config:/app/config
      - media:/media
      - downloads:/downloads
    ports:
      - "8000:8000"
    environment:
      - MEDIA_DIR=/media
      - DOWNLOAD_DIR=/downloads
      - ARIA2_RPC_SECRET=${ARIA2_RPC_SECRET:-}
      - TMDB_API_KEY=${TMDB_API_KEY:-}
      - TVDB_API_KEY=${TVDB_API_KEY:-}
    restart: unless-stopped
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8000/health"]
      interval: 30s
      timeout: 10s
      retries: 3

volumes:
  media:
  downloads:
```

**Step 3: 创建 .dockerignore**

```
__pycache__
*.pyc
*.pyo
*.pyd
.Python
*.so
*.egg
*.egg-info
dist
build
.git
.gitignore
.env
venv
.venv
*.md
tests/
```

**Step 4: Commit**

```bash
git add Dockerfile docker-compose.yaml .dockerignore
git commit -m "feat: add Docker configuration"
```

---

## 阶段 7: 集成测试

### Task 12: 集成测试

**Files:**
- Create: `tests/test_integration.py`

**Step 1: 写集成测试**

```python
import pytest
import os
import sys

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

def test_config_loading():
    from src.config import Config
    config = Config()
    assert config.media_dir == "/media"
    assert config.download_dir == "/downloads"

def test_file_operations():
    from src.tools.file_ops import create_dir, list_dir, delete_file
    import tempfile, shutil

    tmp = tempfile.mkdtemp()
    try:
        create_dir(os.path.join(tmp, "test"))
        result = list_dir(tmp)
        assert any(r["name"] == "test" for r in result)
    finally:
        shutil.rmtree(tmp)

def test_media_scanner():
    from src.tools.media_scanner import scan_media_library, MEDIA_EXTENSIONS
    assert ".mp4" in MEDIA_EXTENSIONS["video"]
    assert ".mkv" in MEDIA_EXTENSIONS["video"]
```

**Step 2: 运行测试**

```bash
pytest tests/ -v
```

**Step 3: Commit**

```bash
git add tests/test_integration.py
git commit -m "test: add integration tests"
```

---

## 实现完成

**下一步:**
- 运行完整测试
- 验证 Docker 构建
- 测试 MCP 接口

---

**Plan complete and saved to `docs/plans/2026-03-09-media-mcp-impl-plan.md`.**

Two execution options:

1. **Subagent-Driven (this session)** - I dispatch fresh subagent per task, review between tasks, fast iteration

2. **Parallel Session (separate)** - Open new session with executing-plans, batch execution with checkpoints

Which approach?
