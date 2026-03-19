"""Scraper module - scrape metadata from JavDB using Scrapling."""

import re
from dataclasses import dataclass
from typing import Optional, List

from scrapling import DynamicFetcher
from opencc import OpenCC


# Initialize OpenCC for Traditional Chinese to Simplified Chinese
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
    runtime: int  # minutes
    genres: List[str]
    studio: str
    maker: str
    cover_url: str
    fanart_urls: List[str]
    actors: List[str]
    magnet_links: List[dict]  # List of dicts with title, size, date, tags, url
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
        self.timeout = timeout * 1000  # Convert to milliseconds

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
            print(f"Search page fetch error: {e}")
            return None

        # Find the matching result link
        detail_url = self._find_detail_url(page, car_number)
        if not detail_url:
            print(f"No search results found for {car_number}")
            return None

        # Step 3: Fetch the detail page
        try:
            detail_page = DynamicFetcher.fetch(
                detail_url,
                wait_selector='h2.title',
                wait_selector_state='attached',
                **self._fetcher_kwargs(),
            )
        except Exception as e:
            print(f"Detail page fetch error: {e}")
            return None

        return self._parse_page(detail_page, car_number, detail_url)

    def _find_detail_url(self, page, car_number: str) -> Optional[str]:
        """Find the detail page URL from search results."""
        items = page.css('a.box')
        if not items or len(items) == 0:
            return None

        # Try to find exact match
        for item in items:
            uid_elem = _first(item.css('.uid'))
            if uid_elem:
                uid_text = _text(uid_elem).upper()
                if car_number in uid_text:
                    href = item.attrib.get('href', '')
                    if href:
                        return self.BASE_URL + href if href.startswith('/') else href

        # Fallback: use first result
        href = items[0].attrib.get('href', '')
        if href:
            return self.BASE_URL + href if href.startswith('/') else href
        return None

    def _parse_page(self, page, car_number: str, url: str) -> Optional[JAVMetadata]:
        """Parse JavDB detail page to extract metadata."""
        try:
            # Title
            title_elem = _first(page.css('h2.title.is-4'))
            if not title_elem:
                title_elem = _first(page.css('h2.title'))
            title = _text(title_elem) if title_elem else car_number
            original_title = title

            # Parse panel-block metadata fields
            # Labels can be English OR Chinese depending on locale
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

                # Release date: "日期" or "Released Date:"
                if '日期' in label or 'release' in label or 'date' in label:
                    # Skip if it's also "ID" block
                    if 'id' in label:
                        continue
                    value_span = _first(block.css('span.value'))
                    if value_span:
                        val = _text(value_span)
                        # Validate it looks like a date
                        if re.search(r'\d{4}', val):
                            release_date = val

                # Runtime: "時長" or "Duration:"
                elif '時長' in label or 'duration' in label:
                    value_span = _first(block.css('span.value'))
                    if value_span:
                        rt_text = _text(value_span)
                        match = re.search(r'(\d+)', rt_text)
                        if match:
                            runtime = int(match.group(1))

                # Studio: "片商" or "Maker:"
                elif '片商' in label or ('maker' in label and 'movie' not in label):
                    value_span = _first(block.css('span.value'))
                    if value_span:
                        link = _first(value_span.css('a'))
                        studio = _text(link) if link else _text(value_span)

                # Publisher/Label: "發行" or "Publisher:"
                elif '發行' in label or 'publisher' in label or 'label' in label:
                    value_span = _first(block.css('span.value'))
                    if value_span:
                        link = _first(value_span.css('a'))
                        maker = _text(link) if link else _text(value_span)

                # Rating: "評分" or "Rating:"
                elif '評分' in label or 'rating' in label:
                    value_span = _first(block.css('span.value'))
                    if value_span:
                        rating_text = _text(value_span)
                        # Match patterns: "4.5分" or "4.5"
                        match = re.search(r'([\d.]+)', rating_text)
                        if match:
                            try:
                                rating = float(match.group(1))
                            except ValueError:
                                pass

                # Genres: "類別" or "Genre(s):" or "Tags:"
                elif '類別' in label or 'genre' in label or 'tag' in label:
                    value_span = _first(block.css('span.value'))
                    if value_span:
                        genre_links = value_span.css('a')
                        for g in genre_links:
                            gt = _text(g)
                            if gt:
                                genres.append(gt)

                # Actors: "演員" or "Actor(s):"
                elif '演員' in label or 'actor' in label:
                    value_span = _first(block.css('span.value'))
                    if value_span:
                        actor_links = value_span.css('a')
                        for a in actor_links:
                            name = _text(a)
                            name = name.replace('♀', '').replace('♂', '').strip()
                            if name:
                                actors.append(name)

                # Director: "導演" or "Director:"
                elif '導演' in label or 'director' in label:
                    pass  # Not needed in metadata

            if not maker:
                maker = studio

            # Cover URL
            cover_url = ""
            cover_elem = _first(page.css('a.cover-container img'))
            if cover_elem:
                cover_url = cover_elem.attrib.get('src', '') or cover_elem.attrib.get('data-src', '')
                if cover_url and not cover_url.startswith('http'):
                    cover_url = self.BASE_URL + cover_url

            # Fanart/Sample images
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

            # Plot
            plot = ""
            plot_elem = _first(page.css('div.description'))
            if plot_elem:
                plot = _text(plot_elem)

            # Magnet Links
            magnet_links = []
            items = page.css('div.item')
            print(f"DEBUG: Found {len(items)} div.item elements")
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

            print(f"DEBUG: Extracted {len(magnet_links)} magnet links")

            website = url

            # Convert to Simplified Chinese
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
        except Exception as e:
            print(f"Parse error: {e}")
            import traceback
            traceback.print_exc()
            return None


def scrape_javdb(car_number: str, proxy: Optional[str] = None) -> Optional[JAVMetadata]:
    """Synchronous wrapper for scraping."""
    scraper = JavDbScraper(proxy=proxy)
    return scraper.search(car_number)
