# Media MCP Server 设计文档

**日期**: 2026-03-09

## 1. 概述

一个运行在 Docker 容器中的 MCP 服务器，用于管理挂载的多媒体文件夹（电影/电视剧），支持元数据生成和 Aria2 下载管理。

## 2. 系统架构

```
┌─────────────────────────────────────────────────────┐
│                   Docker 容器                        │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐  │
│  │  MCP Server │  │    Aria2    │  │  临时目录   │  │
│  │   (Python)  │  │   (RPC)     │  │  /downloads │  │
│  └──────┬──────┘  └──────┬──────┘  └─────────────┘  │
│         │                │                          │
│         └────────────────┴──────────┬──────────────┤
│                           挂载: /media               │
└──────────────────────────────────────┴───────────────┘
```

## 3. 接口清单 (18个)

### 3.1 文件操作

| 接口 | 功能 |
|------|------|
| `list_dir` | 列出目录内容 |
| `move_file` | 移动/重命名文件 |
| `copy_file` | 复制文件 |
| `delete_file` | 删除文件 |
| `create_dir` | 创建目录 |
| `get_file_info` | 获取文件信息 |

### 3.2 媒体库扫描

| 接口 | 功能 |
|------|------|
| `scan_media_library` | 扫描指定目录，返回所有媒体文件（视频+封面+nfo） |

### 3.3 下载管理

| 接口 | 功能 |
|------|------|
| `create_download` | 创建下载任务 |
| `list_downloads` | 列出下载任务 |
| `pause_download` | 暂停下载 |
| `resume_download` | 恢复下载 |
| `cancel_download` | 取消下载 |
| `get_download_status` | 获取下载状态 |

### 3.4 下载配置

| 接口 | 功能 |
|------|------|
| `get_aria2_config` | 获取当前 Aria2 配置 |
| `set_aria2_speed_limit` | 设置下载/上传速度限制 |
| `update_bt_tracker` | 更新 BT tracker 列表 |
| `get_bt_trackers` | 获取当前 BT tracker 列表 |

### 3.5 元数据

| 接口 | 功能 |
|------|------|
| `scrape_metadata` | 在线削刮元数据（TMDB/TVDB/豆瓣） |
| `manual_metadata` | 手动填写元数据并写入 nfo |
| `download_poster` | 下载/更新封面图片 |

### 3.6 NFO 操作

| 接口 | 功能 |
|------|------|
| `read_nfo` | 读取现有 NFO 文件 |
| `update_nfo` | 修改 NFO 文件 |

## 4. 技术选型

- **MCP 框架**: `mcp[everything]` 或 `fastmcp`
- **MCP 协议**: Streamable HTTP
- **Aria2**: `aria2p` (Python RPC 客户端)
- **削刮器**:
  - TMDB: `tmdb3api` 或直接 HTTP API
  - TVDB: `tvdb-api`
  - 豆瓣: 第三方库或直接 HTTP API
- **NFO 格式**: `ElementTree` 生成 Jellyfin/Plex 兼容 XML
- **编码**: UTF-8 全编码支持

## 5. 数据流

```
LLM -> MCP: create_download(url, filename)
        -> Aria2: 开始下载到 /downloads
        -> MCP: 返回 task_id

[下载完成]
LLM -> MCP: list_downloads (轮询状态)
        -> MCP: 返回 completed

LLM -> MCP: scrape_metadata(filename) 或 manual_metadata()
        -> MCP: 生成 xxx.nfo + poster.jpg
        -> MCP: move_file(到媒体库目录)

LLM -> MCP: scan_media_library(媒体库目录)
        -> MCP: 返回所有媒体文件列表
        -> Jellyfin/Plex 扫描并识别
```

## 6. Docker 部署

### Dockerfile

```dockerfile
FROM python:3.11-slim

RUN apt-get update && apt-get install -y aria2 && rm -rf /var/lib/apt/lists/*

WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt

COPY config.yaml .

CMD ["sh", "-c", "aria2c --enable-rpc --rpc-listen-all & python main.py"]
```

### docker-compose.yaml

```yaml
version: '3.8'

services:
  media-mcp:
    build: .
    container_name: media-mcp
    volumes:
      - ./config:/app/config
      - /path/to/media:/media
      - ./downloads:/downloads
    ports:
      - "8000:8000"
    environment:
      - MEDIA_DIR=/media
      - DOWNLOAD_DIR=/downloads
      - ARIA2_RPC_SECRET=your_secret
    restart: unless-stopped
```

## 7. 特性

- UTF-8 全编码支持（中文文件名、多语言）
- 保持原有文件夹结构，元数据就近生成
- 多削刮器支持（TMDB/TVDB/豆瓣）+ 手动填写
- Aria2 内置式运行（同一容器）
