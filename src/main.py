import os
import sys
from pathlib import Path
from typing import List, Dict, Any
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import JSONResponse

# Add src to path
sys.path.insert(0, str(Path(__file__).parent))

from mcp.server import FastMCP
from config import Config
from tools.file_ops import (
    list_dir as _list_dir,
    move_file as _move_file,
    copy_file as _copy_file,
    delete_file as _delete_file,
    create_dir as _create_dir,
    get_file_info as _get_file_info,
)
from tools.media_scanner import scan_media_library as _scan_media_library
from tools.aria2_manager import Aria2Manager
from tools.nfo_generator import generate_nfo as _generate_nfo, read_nfo as _read_nfo, update_nfo as _update_nfo
from scrapers.tmdb_scraper import TMDbScraper
from scrapers.tvdb_scraper import TVDbScraper
from scrapers.douban_scraper import DoubanScraper
from scrapers.base import MediaMetadata

config = Config()

# Token authentication middleware
class TokenAuthMiddleware(BaseHTTPMiddleware):
    def __init__(self, app, token: str = None):
        super().__init__(app)
        self.token = token

    async def dispatch(self, request: Request, call_next):
        # Skip auth if no token configured
        if not self.token:
            return await call_next(request)

        # Check token from header
        auth_header = request.headers.get("Authorization", "")
        if auth_header.startswith("Bearer "):
            token = auth_header[7:]
            if token == self.token:
                return await call_next(request)

        # Also check query parameter for SSE connections
        query_token = request.query_params.get("token")
        if query_token == self.token:
            return await call_next(request)

        return JSONResponse(
            {"error": "Unauthorized", "message": "Invalid or missing token"},
            status_code=401
        )


# Initialize Aria2 manager
aria2_manager = Aria2Manager(
    host="localhost",
    port=6800,
    secret=config.aria2_secret
)

mcp = FastMCP("media-mcp")


@mcp.tool()
def list_dir(path: str) -> List[Dict[str, Any]]:
    """列出目录内容"""
    return _list_dir(path)


@mcp.tool()
def move_file(src: str, dst: str) -> Dict[str, str]:
    """移动/重命名文件"""
    return _move_file(src, dst)


@mcp.tool()
def copy_file(src: str, dst: str) -> Dict[str, str]:
    """复制文件"""
    return _copy_file(src, dst)


@mcp.tool()
def delete_file(path: str) -> Dict[str, str]:
    """删除文件或目录"""
    return _delete_file(path)


@mcp.tool()
def create_dir(path: str) -> Dict[str, str]:
    """创建目录"""
    return _create_dir(path)


@mcp.tool()
def get_file_info(path: str) -> Dict[str, Any]:
    """获取文件信息"""
    return _get_file_info(path)


# Media library scanning
@mcp.tool()
def scan_media_library(path: str, recursive: bool = True) -> List[Dict[str, Any]]:
    """扫描媒体库，返回所有媒体文件（视频+封面+nfo）"""
    return _scan_media_library(path, recursive)


# Download management
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


@mcp.tool()
def pause_download(gid: str) -> Dict[str, str]:
    """暂停下载"""
    return aria2_manager.pause_download(gid)


@mcp.tool()
def resume_download(gid: str) -> Dict[str, str]:
    """恢复下载"""
    return aria2_manager.resume_download(gid)


@mcp.tool()
def cancel_download(gid: str) -> Dict[str, str]:
    """取消下载"""
    return aria2_manager.cancel_download(gid)


@mcp.tool()
def get_download_status(gid: str) -> Dict[str, Any]:
    """获取下载状态"""
    return aria2_manager.get_download_status(gid)


# Download configuration
@mcp.tool()
def get_aria2_config() -> Dict[str, Any]:
    """获取当前 Aria2 配置"""
    return aria2_manager.get_global_options()


@mcp.tool()
def set_aria2_speed_limit(download_limit: str = None, upload_limit: str = None) -> Dict[str, str]:
    """设置下载/上传速度限制"""
    return aria2_manager.set_speed_limit(download_limit, upload_limit)


@mcp.tool()
def get_bt_trackers() -> List[str]:
    """获取当前 BT tracker 列表"""
    return aria2_manager.get_bt_trackers()


@mcp.tool()
def update_bt_tracker(trackers: List[str]) -> Dict[str, Any]:
    """更新 BT tracker 列表"""
    return aria2_manager.update_bt_trackers(trackers)


# Metadata scraping
@mcp.tool()
def scrape_metadata(filename: str, source: str = "tmdb", year: int = None) -> List[Dict[str, Any]]:
    """在线削刮元数据（TMDB/TVDB/豆瓣）"""
    from dataclasses import asdict
    query = os.path.splitext(os.path.basename(filename))[0]

    if source == "tmdb":
        scraper = TMDbScraper(config.tmdb_api_key)
        return [asdict(m) for m in scraper.search(query, year)]
    elif source == "tvdb":
        scraper = TVDbScraper(config.tvdb_api_key)
        return [asdict(m) for m in scraper.search(query, year)]
    elif source == "douban":
        scraper = DoubanScraper()
        return [asdict(m) for m in scraper.search(query, year)]
    else:
        raise ValueError(f"Unknown source: {source}")


@mcp.tool()
def manual_metadata(media_path: str, metadata: Dict[str, Any]) -> str:
    """手动填写元数据并写入 nfo"""
    meta = MediaMetadata(**metadata)
    return _generate_nfo(meta, media_path)


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
    return _read_nfo(nfo_path)


@mcp.tool()
def update_nfo(nfo_path: str, metadata: Dict[str, Any]) -> str:
    """更新 NFO 文件"""
    meta = MediaMetadata(**metadata)
    return _update_nfo(nfo_path, meta)


if __name__ == "__main__":
    import uvicorn

    app = mcp.streamable_http_app()

    # Add token auth middleware if configured
    auth_token = os.environ.get("MCP_AUTH_TOKEN", os.environ.get("ARIA2_RPC_SECRET", ""))
    if auth_token:
        app.add_middleware(TokenAuthMiddleware, token=auth_token)

    # 直接使用 uvicorn.run 简化
    uvicorn.run(
        app,
        host=config._config.get("server", {}).get("host", "0.0.0.0"),
        port=config._config.get("server", {}).get("port", 8000)
    )
