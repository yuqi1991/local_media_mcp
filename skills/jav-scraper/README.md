# JAV Scraper

JAV 影片削刮 CLI 工具，用于从 JavDB 爬取磁力链接和元数据。

## 安装

```bash
cd skills/jav-scraper
uv venv
source .venv/bin/activate
uv sync
playwright install chromium
```

## 使用

```bash
# 搜索番号
source .venv/bin/activate
python -m src.scraper search ABC-123
```

## 配置

环境变量:
- `JAV_HTTP_PROXY`: HTTP/SOCKS5 代理地址
