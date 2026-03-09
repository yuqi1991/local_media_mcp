import requests
from typing import List
from .base import BaseScraper, MediaMetadata


class DoubanScraper(BaseScraper):
    """豆瓣电影/电视剧削刮器"""

    def __init__(self):
        self.base_url = "https://movie.douban.com"
        self.search_url = "https://movie.douban.com/j/search_subjects"

    def search(self, query: str, year: int = None) -> List[MediaMetadata]:
        params = {
            "type": "movie",
            "tag": "电影",
            "page_limit": 20,
            "page_start": 0,
        }

        # 尝试搜索电影
        movie_resp = requests.get(self.search_url, params={**params, "q": query})
        results = self._parse_search_results(movie_resp.json() if movie_resp.status_code == 200 else {})

        if year and results:
            results = [r for r in results if r.year == year]

        return results[:10]

    def _parse_search_results(self, data: dict) -> List[MediaMetadata]:
        results = []
        for item in data.get("subjects", []):
            # 解析年份
            year = 0
            try:
                year = int(item.get("year", "")[:4]) if item.get("year") else 0
            except (ValueError, TypeError):
                pass

            results.append(MediaMetadata(
                title=item.get("title", ""),
                original_title=item.get("title", ""),
                year=year,
                plot=item.get("intro", ""),
                rating=float(item.get("rate", 0)) if item.get("rate") else 0.0,
                poster_url=item.get("cover", ""),
            ))
        return results

    def get_details(self, media_id: str) -> MediaMetadata:
        # 豆瓣详情页需要登录或有访问限制，这里返回基本信息
        # 实际使用时可能需要其他方式获取详情
        url = f"https://movie.douban.com/subject/{media_id}/"
        resp = requests.get(url, allow_redirects=False)

        # 这里只是占位实现，实际需要更复杂的解析
        return MediaMetadata(
            title="",
            plot="获取详情需要登录或有访问限制"
        )
