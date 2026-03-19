# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Media MCP Server - A Docker-based MCP server for managing multimedia libraries with metadata scraping and Aria2 download management. Exposes tools via the Model Context Protocol (MCP) for file operations, media scanning, downloads, and metadata management.

## Common Commands

### Development
```bash
# Run locally (without Docker)
python -m src.main

# Run tests
python -m pytest tests/ -v

# Run a single test file
python -m pytest tests/test_file_ops.py -v

# Run a specific test
python -m pytest tests/test_file_ops.py::test_file_operations -v
```

### Docker
```bash
# Build and start
docker-compose up -d

# View logs
docker-compose logs -f

# Stop
docker-compose down

# Rebuild
docker-compose up -d --build
```

### Environment Setup
```bash
cp .env.example .env
# Edit .env with API keys (ARIA2_RPC_SECRET, TMDB_API_KEY, TVDB_API_KEY)
```

## Architecture

### Entry Point
- `src/main.py` - FastMCP server initialization, registers all tools, uvicorn runner

### Configuration
- `src/config.py` - Config class that loads from `config.yaml` and environment variables
- `config.yaml` - Default configuration (server, aria2, paths, scrapers)

### Tools (`src/tools/`)
- `file_ops.py` - File operations: list_dir, move_file, copy_file, delete_file, create_dir, get_file_info
- `media_scanner.py` - Media library scanning with MEDIA_EXTENSIONS filter (video, poster, nfo)
- `aria2_manager.py` - Aria2 RPC client wrapper for download management
- `nfo_generator.py` - NFO file generation/read/update (Jellyfin/Plex/Emby compatible)

### Scrapers (`src/scrapers/`)
- `base.py` - MediaMetadata dataclass and BaseScraper abstract class
- `tmdb_scraper.py` - TMDb scraper implementation
- `tvdb_scraper.py` - TVDb scraper implementation
- `douban_scraper.py` - Douban scraper implementation

### Key Design Patterns
- All MCP tools are decorated with `@mcp.tool()` in main.py and delegate to functions in `src/tools/`
- Config uses both `config.yaml` and environment variables (env vars take precedence)
- Aria2 runs inside the container; the MCP server connects to it via RPC on localhost:6800
- Token authentication middleware (`TokenAuthMiddleware`) protects the HTTP endpoint when `MCP_AUTH_TOKEN` or `ARIA2_RPC_SECRET` is set

## Dependencies

- `mcp>=1.0.0` - MCP framework
- `aria2p>=0.3.0` - Aria2 RPC client
- `requests>=2.31.0` - HTTP requests
- `python-dotenv>=1.0.0` - Environment variable loading
- `pyyaml>=6.0` - YAML parsing
- `pillow>=10.0.0` - Image processing (for poster downloads)
