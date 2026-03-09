# Media MCP Server

一个运行在 Docker 容器中的 MCP 服务器，用于管理多媒体库，支持元数据生成和 Aria2 下载管理。

## 功能特性

### 文件操作
- `list_dir` - 列出目录内容
- `move_file` - 移动/重命名文件
- `copy_file` - 复制文件
- `delete_file` - 删除文件
- `create_dir` - 创建目录
- `get_file_info` - 获取文件信息

### 媒体库扫描
- `scan_media_library` - 扫描指定目录，返回所有媒体文件（视频+封面+nfo）

### 下载管理
- `create_download` - 创建下载任务
- `list_downloads` - 列出下载任务
- `pause_download` - 暂停下载
- `resume_download` - 恢复下载
- `cancel_download` - 取消下载
- `get_download_status` - 获取下载状态

### 下载配置
- `get_aria2_config` - 获取当前 Aria2 配置
- `set_aria2_speed_limit` - 设置下载/上传速度限制
- `get_bt_trackers` - 获取 BT tracker 列表
- `update_bt_tracker` - 更新 BT tracker 列表

### 元数据管理
- `scrape_metadata` - 在线削刮元数据（支持 TMDB/TVDB/豆瓣）
- `manual_metadata` - 手动填写元数据并写入 nfo
- `download_poster` - 下载/更新封面图片
- `read_nfo` - 读取 NFO 文件
- `update_nfo` - 更新 NFO 文件

## 技术栈

- Python 3.11
- FastMCP (MCP 框架)
- Aria2 (下载器)
- ElementTree (NFO 生成)

## Docker 镜像

镜像已自动构建并推送到 GitHub Container Registry。

### 使用预构建镜像

```bash
# 拉取镜像
docker pull ghcr.io/yuqi1991/local_media_mcp:latest

# 运行
docker run -d \
  --name media-mcp \
  -v /path/to/media:/media \
  -v /path/to/downloads:/downloads \
  -p 8000:8000 \
  -e ARIA2_RPC_SECRET=your_secret \
  -e TMDB_API_KEY=your_key \
  ghcr.io/yuqi1991/local_media_mcp:latest
```

### 版本标签

- `latest` - 最新稳定版
- `v1.0.0` - 语义化版本
- `sha-xxxxxxx` - 指定提交

## 快速开始

### 1. 配置环境变量

```bash
cp .env.example .env
```

编辑 `.env` 文件，填写必要的 API keys：

```bash
ARIA2_RPC_SECRET=your_secret_here
TMDB_API_KEY=your_tmdb_key
TVDB_API_KEY=your_tvdb_key
```

### 2. Docker 部署

```bash
# 构建并启动
docker-compose up -d

# 查看日志
docker-compose logs -f

# 停止
docker-compose down
```

### 3. 配置媒体目录

在 `docker-compose.yaml` 中修改媒体库挂载路径：

```yaml
volumes:
  - ./config:/app/config
  - /path/to/your/media:/media   # 修改为你的媒体目录
  - ./downloads:/downloads
```

## MCP 客户端配置

### Streamable HTTP

```
http://localhost:8000/mcp
```

### 使用示例

```python
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

# 连接 MCP 服务
params = StdioServerParameters(
    command="docker",
    args=["exec", "-i", "media-mcp", "python", "-m", "src.main"]
)

async with stdio_client(params) as (read, write):
    async with ClientSession(read, write) as session:
        await session.initialize()

        # 列出目录
        result = await session.call_tool("list_dir", {"path": "/media"})

        # 创建下载
        result = await session.call_tool("create_download", {
            "uri": "magnet:?xt=urn:btih:...",
            "filename": "movie.mp4"
        })
```

## 目录结构

```
media-mcp/
├── src/
│   ├── main.py              # MCP 入口
│   ├── config.py            # 配置管理
│   ├── tools/
│   │   ├── file_ops.py      # 文件操作
│   │   ├── media_scanner.py # 媒体扫描
│   │   ├── aria2_manager.py # Aria2 管理
│   │   └── nfo_generator.py # NFO 生成
│   └── scrapers/
│       ├── base.py          # 基础类
│       ├── tmdb_scraper.py  # TMDB 削刮
│       ├── tvdb_scraper.py  # TVDB 削刮
│       └── douban_scraper.py # 豆瓣削刮
├── tests/                   # 测试
├── config.yaml              # 配置文件
├── Dockerfile              # Docker 镜像
├── docker-compose.yaml     # 部署配置
└── requirements.txt        # Python 依赖
```

## NFO 格式

生成的 NFO 文件兼容 Jellyfin/Plex/Emby，结构如下：

```xml
<?xml version="1.0" ?>
<item>
  <title>电影标题</title>
  <originaltitle>原始标题</originaltitle>
  <year>2024</year>
  <plot>剧情简介</plot>
  <rating>8.5</rating>
  <genre>动作</genre>
  <genre>科幻</genre>
  <director>导演</director>
  <actor>
    <name>演员1</name>
  </actor>
  <tmdbid>12345</tmdbid>
</item>
```

## License

MIT
