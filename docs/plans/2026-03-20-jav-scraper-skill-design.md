# JAV Scraper Skill 设计

## 概述

将 JAV 影片削刮能力封装为一个 Claude Code Skill，供 LLM Agent 在性能充足的机器上调用，爬取 JavDB 上的磁力链接和元数据。

核心设计：scraper 作为独立 CLI 工具，LLM Agent 通过 subprocess 调用，返回 JSON 给 agent 处理后调用 media_mcp 接口。

---

## 架构

### 目录结构

```
skills/jav-scraper/
├── pyproject.toml           # 依赖管理 (scrapling, playwright)
├── src/
│   └── __init__.py
│   └── scraper.py          # 核心爬虫逻辑
├── cli.py                   # CLI 入口
├── README.md                # 安装和使用说明
└── SKILL.md                 # Claude Code Skill 定义
```

### 技术选型

- **爬虫框架**: scrapling[playwright] - 支持 Cloudflare 绕过和 headless Chromium 渲染
- **HTTP 客户端**: curl-cffi - 高速 HTTP 请求
- **浏览器自动化**: playwright - 处理 JavaScript 渲染
- **Python 版本**: >= 3.10

---

## CLI 接口

### search 命令

```bash
python -m jav_scraper search <catalog_number>
```

**输入:**
- catalog_number: 影片番号，如 ABC-123

**输出 (JSON):**
```json
{
  "catalog_number": "ABC-123",
  "success": true,
  "magnet_links": [
    {
      "title": "ABC-123.mp4 2.1GB",
      "uri": "magnet:?xt=urn:btih:...",
      "size": "2.1GB",
      "quality": "1080p"
    }
  ],
  "metadata": {
    "title": "完整标题",
    "original_title": "原始标题",
    "plot": "剧情简介",
    "genres": ["类型1", "类型2"],
    "director": "导演",
    "actors": ["演员1", "演员2"],
    "rating": 8.5,
    "poster_url": "https://pics.dmm.co.jp/...",
    "release_date": "2024-01-01",
    "extra": {
      "studio": "片商",
      "maker": "制作商",
      "customrating": "JP-18+"
    }
  }
}
```

**错误输出:**
```json
{
  "success": false,
  "error": "番号未找到",
  "catalog_number": "XXX-999"
}
```

---

## SKILL.md

```markdown
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
   - 设置 `JAV_HTTP_PROXY` 环境变量

## 使用方式

### 搜索番号

```bash
python -m jav_scraper search <catalog_number>
```

**示例:**
```bash
python -m jav_scraper search ABC-123
```

## 输出格式

返回 JSON 格式，包含:
- `catalog_number`: 番號
- `magnet_links`: 磁力链接列表
- `metadata`: 元数据（标题、演员、封面 URL 等）

## 注意事项

- 此工具需要在有网络的机器上运行
- 如果访问 JavDB 困难，请设置代理
- 磁力链接由 JavDB 网友共享，质量参差不齐
```

---

## 安装说明 (README.md)

```markdown
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
python -m jav_scraper search ABC-123
```

## 配置

环境变量:
- `JAV_HTTP_PROXY`: HTTP/SOCKS5 代理地址
```

---

## 数据流

### 完整使用流程

```
1. 用户/Agent 调用 skill
   python -m jav_scraper search ABC-123

2. Scraper 返回 JSON
   {
     "magnet_links": [...],
     "metadata": {...}
   }

3. Agent 处理 JSON，提取磁力链接
   - 展示给用户选择

4. 用户选择下载链接，确定开始下载

5. Agent 调用 media_mcp
   create_download(uri="magnet:?...")

6. OpenClaw cron 轮询下载状态

7. 下载完成，用户要求入库

8. 用户指定文件路径

9. Agent 调用 media_mcp
   import_video(metadata={...}, video_path="/path/to/file.mp4")

10. media_mcp 生成 NFO，入库
```

---

## 依赖

```
scrapling[playwright]>=0.4.2
playwright>=1.58.0
beautifulsoup4>=4.12.0
lxml>=4.9.0
curl-cffi>=0.14.0
browserforge>=1.2.4
opencc-python-reimplemented>=0.1.7
python-dotenv>=1.2.2
```

---

## 暂不实现

- 封面图片下载（由 media_mcp 负责下载）
- BT tracker 更新提醒
- 其他通知机制
