# Media MCP Server

一个运行在 Docker 容器中的 MCP 服务器，用于管理多媒体库，支持影片入库和 Aria2 下载管理。

## 功能特性

### 下载管理
- `create_download` - 创建下载任务
- `list_downloads` - 列出下载任务
- `pause_download` - 暂停下载
- `resume_download` - 恢复下载
- `cancel_download` - 取消下载
- `get_download_status` - 获取下载状态
- `get_bt_trackers` - 获取 BT tracker 列表
- `update_bt_trackers` - 从 GitHub 更新 BT tracker 列表
- `restart_aria2` - 重启 Aria2 服务

### 影片入库
- `scan_source_dir` - 扫描源目录，返回未入库的视频文件
- `import_video` - 导入影片到媒体库（生成 NFO、封面）
- `list_library_videos` - 列出库中所有影片
- `get_video` - 获取指定影片信息
- `search_videos` - 搜索影片
- `get_library_stats` - 获取媒体库统计信息
- `remove_video` - 从库中移除影片

### 元数据管理
- `update_video_metadata` - 更新影片元数据
- `download_poster` - 下载封面图片
- `read_nfo_file` - 读取 NFO 文件

### CLI 命令
```bash
python -m src scan --source /path/to/downloads
python -m src import-video --source /path/to/video.mp4 --metadata '{"title":"...", "extra":{"catalog_number":"ABC-123"}}'
python -m src list-videos
python -m src stats
```

## 架构

```
三层架构：
上层 (MCP / CLI)
    ↓
中层 (Video 类、Library 类)
    ↓
底层 (基础文件操作)
```

削刮能力由 LLM Agent 通过独立 Skill 在性能充足的机器上执行后，将结构化数据发给 MCP。

## 技术栈

- Python 3.11
- FastMCP (MCP 框架)
- Aria2 (下载器)
- Pillow (图片处理)

## Docker 部署

```bash
# 构建并启动
docker-compose up -d

# 查看日志
docker-compose logs -f

# 停止
docker-compose down
```

### 环境变量

```bash
ARIA2_RPC_SECRET=your_secret    # Aria2 RPC 密钥
MCP_AUTH_TOKEN=your_token       # MCP 认证令牌
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

params = StdioServerParameters(
    command="docker",
    args=["exec", "-i", "media-mcp", "python", "-m", "src.main"]
)

async with stdio_client(params) as (read, write):
    async with ClientSession(read, write) as session:
        await session.initialize()

        # 扫描源目录
        result = await session.call_tool("scan_source_dir", {"source_dir": "/media/jav"})

        # 导入影片
        result = await session.call_tool("import_video", {
            "metadata": {
                "title": "影片标题",
                "extra": {"catalog_number": "ABC-123", "studio": "片商"}
            },
            "video_path": "/media/jav/ABC-123.mp4"
        })

        # 查看下载状态
        result = await session.call_tool("list_downloads")
```

## 目录结构

```
media-mcp/
├── src/
│   ├── main.py              # MCP 入口
│   ├── config.py            # 配置管理
│   ├── __main__.py         # CLI 入口
│   ├── models/
│   │   ├── video.py        # Video 数据类
│   │   └── library.py      # Library 类
│   ├── tools/
│   │   ├── download.py     # 下载管理
│   │   └── nfo_generator.py # NFO 生成
│   └── cli/
│       └── commands.py     # CLI 命令
├── tests/                   # 测试
├── config.yaml              # 配置文件
├── Dockerfile              # Docker 镜像
├── docker-compose.yaml     # 部署配置
└── requirements.txt        # Python 依赖
```

## 配置 (config.yaml)

```yaml
server:
  host: "0.0.0.0"
  port: 8000

aria2:
  rpc_host: "localhost"
  rpc_port: 6800
  rpc_secret: ""

paths:
  media_dir: "/media/jav/JAV_output"  # 媒体库目录
  download_dir: "/downloads"          # 下载目录
  source_dir: "/media/jav"            # 源目录
  index_path: "/app/config/library_index.jsonl"  # 索引文件

bt_tracker:
  update_url: "https://raw.githubusercontent.com/ngosang/trackerslist/master/trackers_best.txt"
```

## NFO 格式

生成的 NFO 文件兼容 Jellyfin/Emby，支持 JAV 专用字段：

```xml
<?xml version="1.0" encoding="utf-8" standalone="yes"?>
<movie>
  <title>影片标题</title>
  <originaltitle>原始标题</originaltitle>
  <year>2024</year>
  <plot>剧情简介</plot>
  <rating>8.5</rating>
  <genre>类型</genre>
  <director>导演</director>
  <actor><name>演员</name></actor>
  <num>ABC-123</num>
  <studio>片商</studio>
  <maker>制作商</maker>
  <set>系列</set>
  <customrating>JP-18+</customrating>
  <cover>封面URL</cover>
</movie>
```

## License

MIT
