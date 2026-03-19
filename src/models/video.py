from dataclasses import dataclass, field
from typing import List, Dict, Any

@dataclass
class Video:
    # 通用字段
    title: str = ""
    original_title: str = ""
    year: int = 0
    plot: str = ""
    genres: List[str] = field(default_factory=list)
    director: str = ""
    actors: List[str] = field(default_factory=list)
    rating: float = 0.0
    poster_url: str = ""
    backdrop_url: str = ""
    release_date: str = ""

    # 文件路径
    video_path: str = ""
    nfo_path: str = ""

    # 封面本地路径
    poster_path: str = ""
    fanart_path: str = ""
    thumb_path: str = ""
    extrafanart_dir: str = ""

    # JAV专用字段 (作为init参数，会存入extra)
    catalog_number: str = ""
    studio: str = ""
    maker: str = ""

    # 扩展字段 (Jellyfin NFO 支持的其他 JAV 专用字段)
    extra: Dict[str, Any] = field(default_factory=dict)

    def __post_init__(self):
        # JAV专用字段存入extra
        if self.catalog_number:
            self.extra["catalog_number"] = self.catalog_number
        if self.studio:
            self.extra["studio"] = self.studio
        if self.maker:
            self.extra["maker"] = self.maker

    def to_dict(self) -> Dict[str, Any]:
        d = {
            "title": self.title,
            "original_title": self.original_title,
            "year": self.year,
            "plot": self.plot,
            "genres": self.genres,
            "director": self.director,
            "actors": self.actors,
            "rating": self.rating,
            "poster_url": self.poster_url,
            "backdrop_url": self.backdrop_url,
            "release_date": self.release_date,
            "video_path": self.video_path,
            "nfo_path": self.nfo_path,
            "poster_path": self.poster_path,
            "fanart_path": self.fanart_path,
            "thumb_path": self.thumb_path,
            "extrafanart_dir": self.extrafanart_dir,
            "extra": self.extra,
        }
        # JAV专用字段也放入顶层
        d["catalog_number"] = self.extra.get("catalog_number", "")
        d["studio"] = self.extra.get("studio", "")
        d["maker"] = self.extra.get("maker", "")
        return d

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Video":
        extra = data.get("extra", {})
        # JAV专用字段从顶层移入extra
        if "catalog_number" in data:
            extra["catalog_number"] = data["catalog_number"]
        if "studio" in data:
            extra["studio"] = data["studio"]
        if "maker" in data:
            extra["maker"] = data["maker"]

        return cls(
            title=data.get("title", ""),
            original_title=data.get("original_title", ""),
            year=data.get("year", 0),
            plot=data.get("plot", ""),
            genres=data.get("genres", []),
            director=data.get("director", ""),
            actors=data.get("actors", []),
            rating=data.get("rating", 0.0),
            poster_url=data.get("poster_url", ""),
            backdrop_url=data.get("backdrop_url", ""),
            release_date=data.get("release_date", ""),
            video_path=data.get("video_path", ""),
            nfo_path=data.get("nfo_path", ""),
            poster_path=data.get("poster_path", ""),
            fanart_path=data.get("fanart_path", ""),
            thumb_path=data.get("thumb_path", ""),
            extrafanart_dir=data.get("extrafanart_dir", ""),
            catalog_number=data.get("catalog_number", ""),
            studio=data.get("studio", ""),
            maker=data.get("maker", ""),
            extra=extra,
        )