import os
import xml.etree.ElementTree as ET
from typing import Dict, Any, List
from src.models.video import Video

def generate_nfo(video: Video, media_path: str = None, media_type: str = "movie") -> str:
    """生成 Jellyfin 兼容的 NFO 文件"""
    root = ET.Element("movie")

    def add_text(parent, tag, text):
        if text:
            elem = ET.SubElement(parent, tag)
            elem.text = str(text)
            return elem
        return None

    # 基础信息
    add_text(root, "title", video.title)
    add_text(root, "originaltitle", video.original_title)
    add_text(root, "year", str(video.year) if video.year else "")
    add_text(root, "plot", video.plot)
    add_text(root, "director", video.director)

    # 评分
    if video.rating:
        add_text(root, "rating", str(video.rating))
        ratings = ET.SubElement(root, "ratings")
        rating_elem = ET.SubElement(ratings, "rating")
        rating_elem.set("name", "javdb")
        rating_elem.set("max", "5")
        rating_elem.set("default", "true")
        value_elem = ET.SubElement(rating_elem, "value")
        value_elem.text = str(video.rating)

    # Genre
    for g in video.genres:
        add_text(root, "genre", g)

    # Tag (additional categorization)
    for g in video.genres:
        add_text(root, "tag", g)

    # 演员
    for actor_name in video.actors:
        actor_elem = ET.SubElement(root, "actor")
        name_elem = ET.SubElement(actor_elem, "name")
        name_elem.text = actor_name
        type_elem = ET.SubElement(actor_elem, "type")
        type_elem.text = "Actor"

    # 发布日期
    if video.release_date:
        add_text(root, "premiered", video.release_date)
        add_text(root, "releasedate", video.release_date)
        add_text(root, "release", video.release_date)

    # 处理 extra 字段
    extra = video.extra or {}

    # 番號
    catalog_number = extra.get("catalog_number") or video.catalog_number
    if catalog_number:
        add_text(root, "num", catalog_number)
        add_text(root, "sorttitle", catalog_number)

    # 片商/制作商
    if extra.get("studio"):
        add_text(root, "studio", extra["studio"])
    if extra.get("maker"):
        add_text(root, "maker", extra["maker"])

    # 系列
    if extra.get("series"):
        add_text(root, "set", extra["series"])

    # 标签
    if extra.get("label"):
        add_text(root, "label", extra["label"])

    # 年龄分级
    if extra.get("customrating"):
        add_text(root, "customrating", extra["customrating"])
        add_text(root, "mpaa", extra["customrating"])

    # 封面 URL
    if extra.get("cover"):
        add_text(root, "cover", extra["cover"])

    # 保存 NFO
    if media_path:
        base_name = os.path.splitext(media_path)[0]
    else:
        base_name = os.path.join(os.path.dirname(video.video_path), catalog_number) if catalog_number else ""

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

    # 提取 ratings
    rating_elem = root.find(".//rating[@name='javdb']")
    rating_value = ""
    if rating_elem is not None:
        value_elem = rating_elem.find("value")
        if value_elem is not None:
            rating_value = value_elem.text or ""

    return {
        "title": get_text("title"),
        "originaltitle": get_text("originaltitle"),
        "year": get_text("year"),
        "plot": get_text("plot"),
        "rating": rating_value or get_text("rating"),
        "genre": get_all_text("genre"),
        "director": get_text("director"),
        "actors": [a.find("name").text for a in root.findall("actor") if a.find("name") is not None and a.find("name").text],
        "num": get_text("num"),
        "studio": get_text("studio"),
        "maker": get_text("maker"),
        "set": get_text("set"),
        "label": get_text("label"),
        "customrating": get_text("customrating"),
        "cover": get_text("cover"),
        "premiered": get_text("premiered"),
        "runtime": get_text("runtime"),
    }


def update_nfo(nfo_path: str, video: Video) -> str:
    """更新 NFO 文件"""
    if not os.path.exists(nfo_path):
        raise FileNotFoundError(f"NFO not found: {nfo_path}")

    return generate_nfo(video, media_path=nfo_path.replace(".nfo", ".mp4"))