import os
import xml.etree.ElementTree as ET
from typing import Dict, Any
from dataclasses import asdict
from scrapers.base import MediaMetadata


def generate_nfo(metadata: MediaMetadata, media_path: str, media_type: str = "movie") -> str:
    """生成 NFO 文件"""
    root = ET.Element("item")

    # 基础信息
    title = ET.SubElement(root, "title")
    title.text = metadata.title

    originaltitle = ET.SubElement(root, "originaltitle")
    originaltitle.text = metadata.original_title

    year = ET.SubElement(root, "year")
    year.text = str(metadata.year) if metadata.year else ""

    plot = ET.SubElement(root, "plot")
    plot.text = metadata.plot

    # 评分
    rating = ET.SubElement(root, "rating")
    rating.text = str(metadata.rating)

    # Genre
    for g in metadata.genre:
        genre = ET.SubElement(root, "genre")
        genre.text = g

    # 导演
    if metadata.director:
        director = ET.SubElement(root, "director")
        director.text = metadata.director

    # 演员
    for actor in metadata.actors:
        actor_elem = ET.SubElement(root, "actor")
        name = ET.SubElement(actor_elem, "name")
        name.text = actor

    # 媒体信息
    if metadata.tmdb_id:
        tmdbid = ET.SubElement(root, "tmdbid")
        tmdbid.text = metadata.tmdb_id

    if metadata.imdb_id:
        imdbid = ET.SubElement(root, "imdbid")
        imdbid.text = metadata.imdb_id

    if metadata.tvdb_id:
        tvdbid = ET.SubElement(root, "tvdbid")
        tvdbid.text = metadata.tvdb_id

    # 保存 NFO
    base_name = os.path.splitext(media_path)[0]
    nfo_path = f"{base_name}.nfo"

    tree = ET.ElementTree(root)
    tree.write(nfo_path, encoding="utf-8", xml_declaration=True)

    return nfo_path


def read_nfo(nfo_path: str) -> Dict[str, Any]:
    """读取 NFO 文件"""
    if not os.path.exists(nfo_path):
        raise FileNotFoundError(f"NFO not found: {nfo_path}")

    tree = ET.parse(nfo_path)
    root = tree.getroot()

    def get_text(tag):
        el = root.find(tag)
        return el.text if el is not None else ""

    def get_all_text(tag):
        return [el.text for el in root.findall(tag) if el.text]

    return {
        "title": get_text("title"),
        "originaltitle": get_text("originaltitle"),
        "year": get_text("year"),
        "plot": get_text("plot"),
        "rating": get_text("rating"),
        "genre": get_all_text("genre"),
        "director": get_text("director"),
        "actors": [a.find("name").text for a in root.findall("actor") if a.find("name") is not None and a.find("name").text],
        "tmdbid": get_text("tmdbid"),
        "imdbid": get_text("imdbid"),
        "tvdbid": get_text("tvdbid")
    }


def update_nfo(nfo_path: str, metadata: MediaMetadata) -> str:
    """更新 NFO 文件"""
    # 根据 nfo 路径反推媒体文件路径
    if nfo_path.endswith(".nfo"):
        base_path = nfo_path[:-4]  # 移除 .nfo 后缀
    else:
        base_path = nfo_path

    # 查找对应的媒体文件
    media_extensions = [".mp4", ".mkv", ".avi", ".mov", ".wmv", ".flv", ".webm", ".m4v"]
    media_path = None

    for ext in media_extensions:
        if os.path.exists(base_path + ext):
            media_path = base_path + ext
            break

    if not media_path:
        # 如果找不到媒体文件，使用 nfo 路径作为基准
        media_path = base_path + ".mp4"

    return generate_nfo(metadata, media_path)
