import requests
from typing import List
from .base import BaseScraper, MediaMetadata


class TVDbScraper(BaseScraper):
    def __init__(self, api_key: str):
        self.api_key = api_key
        self.base_url = "https://api.thetvdb.com"
        self._token = None

    def _get_token(self) -> str:
        """Get or refresh TVDB token"""
        if self._token:
            return self._token

        resp = requests.post(
            f"{self.base_url}/login",
            json={"api_key": self.api_key}
        )
        data = resp.json()
        self._token = data.get("token")
        return self._token

    def _headers(self) -> dict:
        return {"Authorization": f"Bearer {self._get_token()}"}

    def search(self, query: str, year: int = None) -> List[MediaMetadata]:
        params = {"query": query}
        resp = requests.get(f"{self.base_url}/search/series", params=params, headers=self._headers())
        data = resp.json()

        results = []
        for item in data.get("data", [])[:10]:
            results.append(MediaMetadata(
                title=item.get("seriesName", ""),
                original_title=item.get("alias", ""),
                year=int(item.get("firstAired", "")[:4]) if item.get("firstAired") else 0,
                plot=item.get("overview", ""),
                rating=item.get("siteRating", 0.0),
                poster_url=f"https://www.thetvdb.org/banners/{item.get('poster')}" if item.get("poster") else "",
                tvdb_id=str(item.get("tvdb_id", ""))
            ))
        return results

    def get_details(self, media_id: str) -> MediaMetadata:
        resp = requests.get(f"{self.base_url}/series/{media_id}", headers=self._headers())
        data = resp.json()

        series_data = data.get("data", {})

        # Get actors
        actors_resp = requests.get(
            f"{self.base_url}/series/{media_id}/actors",
            headers=self._headers()
        )
        actors_data = actors_resp.json().get("data", []) if actors_resp.status_code == 200 else []
        actors = [a.get("name", "") for a in actors_data[:10]]

        return MediaMetadata(
            title=series_data.get("seriesName", ""),
            original_title=series_data.get("alias", ""),
            year=int(series_data.get("firstAired", "")[:4]) if series_data.get("firstAired") else 0,
            plot=series_data.get("overview", ""),
            rating=series_data.get("siteRating", 0.0),
            poster_url=f"https://www.thetvdb.org/banners/{series_data.get('poster')}" if series_data.get("poster") else "",
            tvdb_id=str(series_data.get("tvdbId", "")),
            actors=actors
        )
