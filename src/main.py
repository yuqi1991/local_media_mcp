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
