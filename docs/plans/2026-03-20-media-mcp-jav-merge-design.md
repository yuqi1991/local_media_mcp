# Media MCP + JAV Archive 合并设计

## 概述

将 `jav_archive` 的 JAV 影片管理能力合并到 `media_mcp`，形成一个统一的 MCP 服务，部署在 NAS 上管理 Jellyfin 影片库。

核心设计：MCP 服务端只负责存储和文件操作，削刮能力由 LLM Agent 通过独立 Skill 在性能充足的机器上执行后，将结构化数据发给 MCP。

---

## 架构

### 三层架构

```
上层 (MCP / CLI)
    │
    ▼
中层 (Video 类、Library 类)
    │
    ▼
底层 (基础文件操作)
```

### 目录结构

```
media-mcp/
├── src/
│   ├── main.py              # MCP 入口
│   ├── config.py            # 配置管理
│   ├── models/
│   │   ├── __init__.py
│   │   ├── video.py         # Video 类
│   │   └── library.py       # Library 类
│   ├── tools/
│   │   ├── __init__.py
│   │   ├── download.py      # 下载管理
│   │   ├── library.py       # 媒体库操作
│   │   └── nfo_generator.py # NFO 生成
│   └── cli/
│       ├── __init__.py
│       └── commands.py      # CLI 命令
├── config.yaml
├── docker-compose.yaml
├── Dockerfile
└── requirements.txt
```

---

## 中层设计

### Video 类

```python
@dataclass
class Video:
    # 通用字段（对应 Jellyfin NFO）
    title: str
    original_title: str = ""
    year: int = 0
    plot: str = ""
    genres: List[str] = field(default_factory=list)
    director: str = ""
    actors: List[str] = field(default_factory=list)
    rating: float = 0.0
    poster_url: str = ""
    backdrop_url: str = ""
    release_date: str = ""  # YYYY-MM-DD

    # 文件路径
    video_path: str = ""
    nfo_path: str = ""

    # 扩展字段（Jellyfin NFO 支持的额外字段）
    extra: Dict[str, Any] = field(default_factory=dict)

    # 封面本地路径
    poster_path: str = ""
    fanart_path: str = ""
    thumb_path: str = ""
    extrafanart_dir: str = ""
```

**关于 extra 字段**

Jellyfin NFO 支持的 JAV 专用字段通过 `extra` 传递：
- `catalog_number` - 番號
- `studio` - 片商
- `maker` - 制作商
- `series` - 系列
- `label` - 标签
- `cover` - 封面 URL
- `num` - 番號（同 catalog_number）
- `customrating` - 年龄分级

### Library 类

```python
class Library:
    def __init__(self, media_dir: str, index_path: str):
        self.media_dir = media_dir
        self.index_path = index_path  # jsonl 文件路径

    def scan(self) -> List[Video]:
        """扫描源目录，返回未入库的视频"""

    def import_video(self, video: Video) -> Video:
        """导入影片：移动文件到媒体库，生成 NFO 和封面"""

    def remove_video(self, catalog_number: str) -> None:
        """从库中移除影片"""

    def get_video(self, catalog_number: str) -> Optional[Video]:
        """获取指定影片信息"""

    def list_videos(self) -> List[Video]:
        """列出库中所有影片"""

    def search(self, query: str) -> List[Video]:
        """搜索影片"""
```

### 索引文件格式 (jsonl)

每行一个 JSON：
```json
{"catalog_number": "ABF-061", "video_path": "/media/jav/JAV_output/ABF-061/ABF-061.mp4", "imported_at": "2025-01-08T00:00:00"}
```

---

## 上层设计

### MCP 工具

#### 下载管理
- `create_download(uri: str, filename: str = None, dir: str = None)` → `{"gid": "...", "name": "...", "status": "..."}`
- `list_downloads(status: str = None)` → `[{"gid": "...", "name": "...", "progress": 50.5}, ...]`
- `pause_download(gid: str)` → `{"gid": "...", "status": "paused"}`
- `resume_download(gid: str)` → `{"gid": "...", "status": "resume"}`
- `cancel_download(gid: str)` → `{"gid": "...", "status": "removed"}`
- `get_download_status(gid: str)` → `{...}`
- `get_bt_trackers()` → `["tracker1", "tracker2", ...]`
- `update_bt_trackers(source_url: str)` → `{"trackers": [...], "count": N}`
- `restart_aria2()` → `{"status": "restarted"}`

#### 影片入库
- `import_video(metadata: dict, video_path: str)` → `{"catalog_number": "...", "status": "imported"}`
  - 接收 LLM Agent 爬取的结构化数据
  - 下载 poster/fanart/thumb
  - 整理入库到媒体库目录
  - 更新索引文件

#### 媒体库查询
- `scan_source_dir(source_dir: str)` → `[{"filename": "...", "path": "...", "size": ...}, ...]`
  - 扫描源目录，返回未处理的视频文件列表
- `list_library_videos()` → `[Video, ...]`
- `get_video(catalog_number: str)` → `Video`
- `search_videos(query: str)` → `[Video, ...]`
- `get_library_stats()` → `{"total": N, "recent_imports": [...]}`

#### 元数据更新
- `update_video_metadata(catalog_number: str, metadata: dict)` → `{"status": "updated"}`
- `download_poster(catalog_number: str, poster_url: str)` → `{"poster_path": "..."}`

### CLI 命令

用于批量操作和定时任务：

```bash
# 批量导入
jav-importer batch-import --source /path/to/downloads

# 定时任务：自动扫描源目录并导入
jav-importer auto-import --source /path/to/downloads --interval 60

# 索引重建
jav-importer rebuild-index --media-dir /path/to/library
```

---

## 配置

### config.yaml

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

### 环境变量

```
ARIA2_RPC_SECRET=xxx
MCP_AUTH_TOKEN=xxx
```

---

## 部署

### Dockerfile

- Python 3.11-slim
- 安装 aria2
- 安装项目依赖
- 容器启动时运行 aria2c 守护进程 + MCP 服务

### docker-compose.yaml

- media-mcp 服务
- volume 挂载媒体目录、下载目录、配置目录

---

## 移除内容

- `src/tools/file_ops.py` - 移除单文件操作
- `src/tools/media_scanner.py` - 移除（功能合并到 Library 类）
- `src/scrapers/` 目录 - 移除所有削刮器
- `config.yaml` 中的 `scrapers` 部分 - 移除
- TMDB/TVDB/Douban MCP 工具 - 移除

---

## 数据流

### 影片入库流程

```
1. LLM Agent 扫描源目录 → 发现新视频
2. LLM Agent 用 Playwright Skill 爬取元数据（远程执行）
3. LLM Agent 调用 MCP import_video(metadata, video_path)
4. MCP:
   a. Library.import_video() 接收 Video 对象
   b. 下载 poster/fanart/thumb 到临时目录
   c. 创建影片子目录
   d. 移动视频文件
   e. 写入 NFO
   f. 移动封面文件
   g. 更新索引文件 (jsonl)
5. 返回导入结果给 LLM Agent
```

### BT Tracker 更新流程

```
1. LLM Agent 调用 update_bt_trackers(source_url)
2. MCP:
   a. 从指定 URL 获取 tracker 列表
   b. 更新 aria2 全局配置
   c. 调用 restart_aria2() 重启 aria2 服务
3. 返回更新结果
```
