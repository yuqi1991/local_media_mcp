import requests
from typing import List
from .base import BaseScraper, MediaMetadata


class TMDbScraper(BaseScraper):
    def __init__(self, api_key: str):
        self.api_key = api_key
        self.base_url = "https://api.themoviedb.org/3"

    def search(self, query: str, year: int = None) -> List[MediaMetadata]:
        params = {"api_key": self.api_key, "query": query}
        if year:
            params["primary_release_year"] = year

        resp = requests.get(f"{self.base_url}/search/movie", params=params)
        data = resp.json()

        results = []
        for item in data.get("results", [])[:10]:
            results.append(MediaMetadata(
                title=item.get("title", ""),
                original_title=item.get("original_title", ""),
                year=int(item.get("release_date", "")[:4]) if item.get("release_date") else 0,
                plot=item.get("overview", ""),
                rating=item.get("vote_average", 0.0),
                poster_url=f"https://image.tmdb.org/t/p/w500{item.get('poster_path')}" if item.get("poster_path") else "",
                backdrop_url=f"https://image.tmdb.org/t/p/w1280{item.get('backdrop_path')}" if item.get("backdrop_path") else "",
                tmdb_id=str(item.get("id", ""))
            ))
        return results

    def get_details(self, media_id: str) -> MediaMetadata:
        # Get movie details
        resp = requests.get(f"{self.base_url}/movie/{media_id}", params={"api_key": self.api_key})
        data = resp.json()

        # Get credits for director and actors
        credits_resp = requests.get(
            f"{self.base_url}/movie/{media_id}/credits",
            params={"api_key": self.api_key}
        )
        credits_data = credits_resp.json() if credits_resp.status_code == 200 else {}

        # Find director
        director = ""
        for crew in credits_data.get("crew", []):
            if crew.get("job") == "Director":
                director = crew.get("name", "")
                break

        # Get actors
        actors = [a.get("name", "") for a in credits_data.get("cast", [])[:10]]

        return MediaMetadata(
            title=data.get("title", ""),
            original_title=data.get("original_title", ""),
            year=int(data.get("release_date", "")[:4]) if data.get("release_date") else 0,
            plot=data.get("overview", ""),
            genre=[g["name"] for g in data.get("genres", [])],
            director=director,
            actors=actors,
            rating=data.get("vote_average", 0.0),
            poster_url=f"https://image.tmdb.org/t/p/w500{data.get('poster_path')}" if data.get("poster_path") else "",
            backdrop_url=f"https://image.tmdb.org/t/p/w1280{data.get('backdrop_path')}" if data.get("backdrop_path") else "",
            tmdb_id=str(data.get("id", ""))
        )
