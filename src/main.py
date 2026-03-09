import os
import sys
from pathlib import Path
from typing import List, Dict, Any

# Add src to path
sys.path.insert(0, str(Path(__file__).parent))

from fastmcp import FastMCP
from config import Config
from tools.file_ops import (
    list_dir as _list_dir,
    move_file as _move_file,
    copy_file as _copy_file,
    delete_file as _delete_file,
    create_dir as _create_dir,
    get_file_info as _get_file_info,
)

config = Config()

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


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        mcp.streamable_http_app(),
        host=config._config.get("server", {}).get("host", "0.0.0.0"),
        port=config._config.get("server", {}).get("port", 8000)
    )
