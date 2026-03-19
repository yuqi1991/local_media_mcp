# JAV Scraper Skill Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Create a JAV scraper CLI skill at `skills/jav-scraper/` that outputs JSON for LLM agent consumption.

**Architecture:** Extract search functionality from jav_archive's JavDbScraper, create new CLI focused on JSON output, and wrap in Claude Code Skill format.

**Tech Stack:** scrapling[playwright], click, python-dotenv

---

## Task 1: Create Directory Structure

**Files:**
- Create: `skills/jav-scraper/pyproject.toml`
- Create: `skills/jav-scraper/src/__init__.py`
- Create: `skills/jav-scraper/src/scraper.py`
- Create: `skills/jav-scraper/src/cli.py`
- Create: `skills/jav-scraper/README.md`
- Create: `skills/jav-scraper/SKILL.md`

**Step 1: Create directories**

```bash
mkdir -p skills/jav-scraper/src
```

**Step 2: Create pyproject.toml**

```toml
[project]
name = "jav-scraper"
version = "0.1.0"
description = "JAV scraper CLI for JavDB"
requires-python = ">=3.10"
dependencies = [
    "scrapling[playwright]>=0.4.2",
    "playwright>=1.58.0",
    "beautifulsoup4>=4.12.0",
    "lxml>=4.9.0",
    "curl-cffi>=0.14.0",
    "browserforge>=1.2.4",
    "opencc-python-reimplemented>=0.1.7",
    "python-dotenv>=1.2.2",
    "click>=8.1.0",
]

[project.scripts]
jav-scraper = "src.cli:main"

[tool.uv]
dev-dependencies = []
```

**Step 3: Create src/__init__.py**

```python
"""JAV Scraper - Search JAV videos on JavDB."""
```

**Step 4: Commit**

```bash
git add skills/
git commit -m "feat: create skills/jav-scraper directory structure"
```

---

## Task 2: Create Scraper Module

**Files:**
- Create: `skills/jav-scraper/src/scraper.py`

**Step 1: Create src/scraper.py based on jav_archive's scraper**

```python
"""Scraper module - scrape metadata from JavDB using Scrapling."""

import re
import json
from dataclasses import dataclass, asdict
from typing import Optional, List

from scrapling import DynamicFetcher
from opencc import OpenCC


_converter = OpenCC('t2s')


def _to_simplified(text: str) -> str:
    """Convert Traditional Chinese to Simplified Chinese."""
    if not text:
        return ""
    return _converter.convert(text)


def _to_simplified_list(items: List[str]) -> List[str]:
    """Convert a list of strings to Simplified Chinese."""
    return [_to_simplified(item) for item in items if item]


@dataclass
class JAVMetadata:
    """JAV video metadata."""
    car_number: str
    title: str
    original_title: str
    rating: float
    release_date: str
    runtime: int
    genres: List[str]
    studio: str
    maker: str
    cover_url: str
    fanart_urls: List[str]
    actors: List[str]
    magnet_links: List[dict]
    plot: str
    website: str


def _first(selectors):
    """Safely get first element from a Selectors collection, or None."""
    try:
        if selectors and len(selectors) > 0:
            return selectors[0]
    except (IndexError, TypeError):
        pass
    return None


def _text(elem) -> str:
    """Get all nested text from an element (deep)."""
    if elem is None:
        return ""
    try:
        t = elem.get_all_text()
        return t.strip() if t else ""
    except Exception:
        t = elem.text
        return t.strip() if t else ""


class JavDbScraper:
    """JavDB scraper using Scrapling DynamicFetcher."""

    BASE_URL = "https://javdb.com"
    SEARCH_URL = "https://javdb.com/search"

    def __init__(self, proxy: Optional[str] = None, timeout: int = 30):
        self.proxy = proxy
        self.timeout = timeout * 1000

    def _fetcher_kwargs(self) -> dict:
        """Build common kwargs for DynamicFetcher.fetch()."""
        kwargs = {
            'headless': True,
            'network_idle': True,
            'timeout': self.timeout,
            'locale': 'zh-TW',
        }
        if self.proxy:
            kwargs['proxy'] = {'server': self.proxy}
        return kwargs

    def search(self, car_number: str) -> Optional[JAVMetadata]:
        """Search for a car number and return metadata."""
        car_number = car_number.upper().strip()

        # Step 1: Accept age verification
        try:
            DynamicFetcher.fetch(
                f"{self.BASE_URL}/over18?respond=1",
                **self._fetcher_kwargs(),
            )
        except Exception:
            pass

        # Step 2: Search page
        search_url = f"{self.SEARCH_URL}?q={car_number}&search_type=number"
        try:
            page = DynamicFetcher.fetch(
                search_url,
                wait_selector='a.box',
                wait_selector_state='attached',
                **self._fetcher_kwargs(),
            )
        except Exception as e:
            return None

        # Find the matching result link
        detail_url = self._find_detail_url(page, car_number)
        if not detail_url:
            return None

        # Step 3: Fetch the detail page
        try:
            detail_page = DynamicFetcher.fetch(
                detail_url,
                wait_selector='h2.title',
                wait_selector_state='attached',
                **self._fetcher_kwargs(),
            )
        except Exception:
            return None

        return self._parse_page(detail_page, car_number, detail_url)

    def _find_detail_url(self, page, car_number: str) -> Optional[str]:
        """Find the detail page URL from search results."""
        items = page.css('a.box')
        if not items or len(items) == 0:
            return None

        for item in items:
            uid_elem = _first(item.css('.uid'))
            if uid_elem:
                uid_text = _text(uid_elem).upper()
                if car_number in uid_text:
                    href = item.attrib.get('href', '')
                    if href:
                        return self.BASE_URL + href if href.startswith('/') else href

        href = items[0].attrib.get('href', '')
        if href:
            return self.BASE_URL + href if href.startswith('/') else href
        return None

    def _parse_page(self, page, car_number: str, url: str) -> Optional[JAVMetadata]:
        """Parse JavDB detail page to extract metadata."""
        try:
            title_elem = _first(page.css('h2.title.is-4'))
            if not title_elem:
                title_elem = _first(page.css('h2.title'))
            title = _text(title_elem) if title_elem else car_number
            original_title = title

            release_date = ""
            runtime = 0
            studio = ""
            maker = ""
            genres = []
            actors = []
            rating = 0.0

            panel_blocks = page.css('div.panel-block')
            for block in panel_blocks:
                strong = _first(block.css('strong'))
                label = _text(strong).lower()

                if '日期' in label or 'release' in label or 'date' in label:
                    if 'id' in label:
                        continue
                    value_span = _first(block.css('span.value'))
                    if value_span:
                        val = _text(value_span)
                        if re.search(r'\d{4}', val):
                            release_date = val

                elif '時長' in label or 'duration' in label:
                    value_span = _first(block.css('span.value'))
                    if value_span:
                        rt_text = _text(value_span)
                        match = re.search(r'(\d+)', rt_text)
                        if match:
                            runtime = int(match.group(1))

                elif '片商' in label or ('maker' in label and 'movie' not in label):
                    value_span = _first(block.css('span.value'))
                    if value_span:
                        link = _first(value_span.css('a'))
                        studio = _text(link) if link else _text(value_span)

                elif '發行' in label or 'publisher' in label or 'label' in label:
                    value_span = _first(block.css('span.value'))
                    if value_span:
                        link = _first(value_span.css('a'))
                        maker = _text(link) if link else _text(value_span)

                elif '評分' in label or 'rating' in label:
                    value_span = _first(block.css('span.value'))
                    if value_span:
                        rating_text = _text(value_span)
                        match = re.search(r'([\d.]+)', rating_text)
                        if match:
                            try:
                                rating = float(match.group(1))
                            except ValueError:
                                pass

                elif '類別' in label or 'genre' in label or 'tag' in label:
                    value_span = _first(block.css('span.value'))
                    if value_span:
                        genre_links = value_span.css('a')
                        for g in genre_links:
                            gt = _text(g)
                            if gt:
                                genres.append(gt)

                elif '演員' in label or 'actor' in label:
                    value_span = _first(block.css('span.value'))
                    if value_span:
                        actor_links = value_span.css('a')
                        for a in actor_links:
                            name = _text(a)
                            name = name.replace('♀', '').replace('♂', '').strip()
                            if name:
                                actors.append(name)

            if not maker:
                maker = studio

            cover_url = ""
            cover_elem = _first(page.css('a.cover-container img'))
            if cover_elem:
                cover_url = cover_elem.attrib.get('src', '') or cover_elem.attrib.get('data-src', '')
                if cover_url and not cover_url.startswith('http'):
                    cover_url = self.BASE_URL + cover_url

            fanart_urls = []
            for tile in page.css('a.tile-item'):
                href = tile.attrib.get('href', '')
                if href:
                    img_url = href if href.startswith('http') else self.BASE_URL + href
                    fanart_urls.append(img_url)
                else:
                    img = _first(tile.css('img'))
                    if img:
                        src = img.attrib.get('src', '') or img.attrib.get('data-src', '')
                        if src:
                            fanart_urls.append(src if src.startswith('http') else self.BASE_URL + src)

            plot = ""
            plot_elem = _first(page.css('div.description'))
            if plot_elem:
                plot = _text(plot_elem)

            magnet_links = []
            items = page.css('div.item')
            for item in items:
                magnet_elem = _first(item.css('a[href^="magnet:"]'))
                if not magnet_elem:
                    continue

                href = magnet_elem.attrib.get('href', '')
                if not href:
                    continue

                title_elem = _first(item.css('span.name'))
                m_title = _text(title_elem)

                tags = []
                for tag_elem in item.css('.tag'):
                    t = _text(tag_elem)
                    if t:
                        tags.append(t)

                date_elem = _first(item.css('.time'))
                m_date = _text(date_elem)

                size_elem = _first(item.css('.meta'))
                m_size = _text(size_elem)

                magnet_links.append({
                    'title': m_title,
                    'size': m_size,
                    'date': m_date,
                    'tags': tags,
                    'url': href
                })

            website = url

            title = _to_simplified(title)
            original_title = _to_simplified(original_title)
            studio = _to_simplified(studio)
            maker = _to_simplified(maker)
            plot = _to_simplified(plot)
            genres = _to_simplified_list(genres)
            actors = _to_simplified_list(actors)

            return JAVMetadata(
                car_number=car_number,
                title=title,
                original_title=original_title,
                rating=rating,
                release_date=release_date,
                runtime=runtime,
                genres=genres,
                studio=studio,
                maker=maker,
                cover_url=cover_url,
                fanart_urls=fanart_urls,
                actors=actors,
                magnet_links=magnet_links,
                plot=plot,
                website=website,
            )
        except Exception:
            return None


def scrape_javdb(car_number: str, proxy: Optional[str] = None) -> Optional[JAVMetadata]:
    """Synchronous wrapper for scraping."""
    scraper = JavDbScraper(proxy=proxy)
    return scraper.search(car_number)
```

**Step 2: Commit**

```bash
git add skills/jav-scraper/src/scraper.py
git commit -m "feat: add JavDbScraper from jav_archive"
```

---

## Task 3: Create CLI Module

**Files:**
- Create: `skills/jav-scraper/src/cli.py`

**Step 1: Create CLI that outputs JSON**

```python
"""CLI module - Click CLI entry point for JAV scraper."""

import sys
import os
import json
from pathlib import Path

import click
from dotenv import load_dotenv

from .scraper import JavDbScraper, JAVMetadata

load_dotenv()


def _get_proxy() -> str:
    """Get proxy from environment."""
    return os.getenv('JAV_HTTP_PROXY') or os.getenv('HTTP_PROXY') or ""


@click.command()
@click.argument('catalog_number')
@click.option('--proxy', '-p', type=str, default=None, help='Proxy URL')
def search(catalog_number: str, proxy: str):
    """Search JAV video and output JSON.

    Example:
        python -m src.scraper search ABC-123
    """
    proxy = proxy or _get_proxy()

    scraper = JavDbScraper(proxy=proxy if proxy else None)
    metadata = scraper.search(catalog_number)

    if not metadata:
        result = {
            "success": False,
            "error": f"番号未找到: {catalog_number}",
            "catalog_number": catalog_number
        }
        click.echo(json.dumps(result, ensure_ascii=False, indent=2))
        sys.exit(1)

    result = {
        "success": True,
        "catalog_number": metadata.car_number,
        "magnet_links": [
            {
                "title": m['title'],
                "uri": m['url'],
                "size": m['size'],
                "date": m['date'],
                "tags": m['tags']
            }
            for m in metadata.magnet_links
        ],
        "metadata": {
            "title": metadata.title,
            "original_title": metadata.original_title,
            "plot": metadata.plot,
            "genres": metadata.genres,
            "director": "",  # Not scraped
            "actors": metadata.actors,
            "rating": metadata.rating,
            "poster_url": metadata.cover_url,
            "release_date": metadata.release_date,
            "extra": {
                "studio": metadata.studio,
                "maker": metadata.maker,
                "customrating": ""  # Not scraped
            }
        }
    }

    click.echo(json.dumps(result, ensure_ascii=False, indent=2))


def main():
    """Main entry point."""
    search()


if __name__ == '__main__':
    main()
```

**Step 2: Commit**

```bash
git add skills/jav-scraper/src/cli.py
git commit -m "feat: add CLI with JSON output"
```

---

## Task 4: Create SKILL.md

**Files:**
- Create: `skills/jav-scraper/SKILL.md`

**Step 1: Create SKILL.md**

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
```

**Step 2: Commit**

```bash
git add skills/jav-scraper/SKILL.md
git commit -m "feat: add SKILL.md for Claude Code"
```

---

## Task 5: Create README.md

**Files:**
- Create: `skills/jav-scraper/README.md`

**Step 1: Create README.md**

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
python -m src.scraper search ABC-123
```

## 配置

环境变量:
- `JAV_HTTP_PROXY`: HTTP/SOCKS5 代理地址
```

**Step 2: Commit**

```bash
git add skills/jav-scraper/README.md
git commit -m "feat: add README.md"
```

---

## Task 6: Verify Installation

**Step 1: Test installation**

```bash
cd skills/jav-scraper
uv venv
source .venv/bin/activate
uv sync
playwright install chromium
```

**Step 2: Verify CLI works**

```bash
# This will fail without network but should not have import errors
python -m src.scraper search TEST-001 2>&1 || true
```

**Step 3: Commit**

```bash
git add -A
git commit -m "chore: complete jav-scraper skill" || true
```
