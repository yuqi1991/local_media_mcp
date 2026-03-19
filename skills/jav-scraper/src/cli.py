"""CLI module - Click CLI entry point for JAV scraper."""

import sys
import os
import json
import click
from dotenv import load_dotenv

from .scraper import JavDbScraper

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
            "director": "",
            "actors": metadata.actors,
            "rating": metadata.rating,
            "poster_url": metadata.cover_url,
            "release_date": metadata.release_date,
            "extra": {
                "studio": metadata.studio,
                "maker": metadata.maker,
                "customrating": ""
            }
        }
    }

    click.echo(json.dumps(result, ensure_ascii=False, indent=2))


def main():
    """Main entry point."""
    search()


if __name__ == '__main__':
    main()
