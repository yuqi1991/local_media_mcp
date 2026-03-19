# jav-scraper

当用户需要搜索 JAV 番号、获取磁力链接或影片元数据时使用此 skill。

## 使用前提

1. 安装依赖:
   ```bash
   cd skills/jav-scraper
   uv venv
   source .venv/bin/activate
   uv sync
   playwright install chromium
   ```

2. 配置代理（如需要）:
   - 设置 `JAV_HTTP_PROXY` 环境变量（如 `socks5h://127.0.0.1:1080`）

## 使用方式

### 搜索番号

```bash
cd skills/jav-scraper
source .venv/bin/activate
python -m src.scraper search <catalog_number>
```

**示例:**
```bash
python -m src.scraper search ABC-123
```

## 输出格式

返回 JSON 格式：
- `success`: 是否成功
- `catalog_number`: 番號
- `magnet_links`: 磁力链接列表（含 title, uri, size, date, tags）
- `metadata`: 元数据（title, plot, genres, actors, rating, poster_url 等）

## 示例输出

```json
{
  "success": true,
  "catalog_number": "ABC-123",
  "magnet_links": [
    {
      "title": "ABC-123.mp4 2.1GB",
      "uri": "magnet:?xt=urn:btih:...",
      "size": "2.1GB",
      "date": "2024-01-15",
      "tags": ["高清", "字幕"]
    }
  ],
  "metadata": {
    "title": "标题",
    "plot": "剧情",
    "genres": ["类型"],
    "actors": ["演员"],
    "rating": 8.5,
    "poster_url": "https://..."
  }
}
```

## 注意事项

- 此工具需要在有网络的机器上运行
- 如果访问 JavDB 困难，请设置代理
- 磁力链接由 JavDB 网友共享，质量参差不齐
