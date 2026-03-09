from abc import ABC, abstractmethod
from typing import Dict, Any, List, Optional
from dataclasses import dataclass, field


@dataclass
class MediaMetadata:
    title: str
    original_title: str = ""
    year: int = 0
    plot: str = ""
    genre: List[str] = field(default_factory=list)
    director: str = ""
    actors: List[str] = field(default_factory=list)
    rating: float = 0.0
    poster_url: str = ""
    backdrop_url: str = ""
    imdb_id: str = ""
    tmdb_id: str = ""
    tvdb_id: str = ""


class BaseScraper(ABC):
    @abstractmethod
    def search(self, query: str, year: int = None) -> List[MediaMetadata]:
        """搜索媒体"""
        pass

    @abstractmethod
    def get_details(self, media_id: str) -> MediaMetadata:
        """获取详情"""
        pass
