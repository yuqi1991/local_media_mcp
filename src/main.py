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
            import requests as req
            resp = req.get(imported.poster_url, timeout=30)
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
        import requests as req
        resp = req.get(poster_url, timeout=30)
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
