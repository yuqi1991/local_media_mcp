import click
import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from src.models.library import Library
from src.config import Config

config = Config()
library = Library(media_dir=config.media_dir, index_path=config.index_path)


@click.group()
def cli():
    """Media MCP CLI - Media library management tool"""
    pass


@cli.command()
@click.option("--source", "-s", required=True, help="Source directory to scan")
def scan(source):
    """Scan source directory for new videos"""
    results = library.scan_source_dir(source)
    if not results:
        click.echo("No new videos found.")
        return
    click.echo(f"Found {len(results)} new videos:")
    for r in results:
        click.echo(f"  {r['filename']} ({r['catalog_number'] or 'unknown'}) - {r['size']} bytes")


@cli.command()
@click.option("--source", "-s", required=True, help="Source video path")
@click.option("--metadata", "-m", required=True, help="Metadata JSON string")
def import_video(source, metadata):
    """Import a single video with metadata"""
    import json
    from src.models.video import Video

    metadata_dict = json.loads(metadata)
    video = Video.from_dict(metadata_dict)

    if not video.catalog_number:
        click.echo("Error: catalog_number is required", err=True)
        return

    try:
        imported = library.import_video(video, source_path=source)
        click.echo(f"Successfully imported {video.catalog_number}")
        click.echo(f"  Video: {imported.video_path}")
        click.echo(f"  NFO: {imported.nfo_path}")
    except Exception as e:
        click.echo(f"Error: {e}", err=True)


@cli.command()
@click.option("--source", "-s", required=True, help="Source directory")
def batch_import(source):
    """Batch import all videos from source directory"""
    results = library.scan_source_dir(source)
    if not results:
        click.echo("No new videos to import.")
        return

    click.echo(f"Found {len(results)} videos. This tool only scans - use LLM Agent for metadata scraping.")


@cli.command()
def list_videos():
    """List all videos in library"""
    videos = library.list_videos()
    if not videos:
        click.echo("Library is empty.")
        return
    click.echo(f"Library has {len(videos)} videos:")
    for v in videos:
        click.echo(f"  {v.catalog_number} - {v.title}")


@cli.command()
@click.option("--media-dir", help="Media library directory")
def rebuild_index(media_dir):
    """Rebuild library index from existing files"""
    if not media_dir:
        media_dir = config.media_dir

    click.echo(f"Scanning {media_dir} for existing videos...")
    # TODO: implement index rebuild
    click.echo("Index rebuild not yet implemented.")


@cli.command()
def stats():
    """Show library statistics"""
    stats_data = library.get_stats()
    click.echo(f"Total videos: {stats_data['total']}")
    if stats_data['recent_imports']:
        click.echo("Recent imports:")
        for r in stats_data['recent_imports']:
            click.echo(f"  {r['catalog_number']}")


# Register all commands
cli.add_command(scan)
cli.add_command(import_video)
cli.add_command(batch_import)
cli.add_command(list_videos)
cli.add_command(rebuild_index)
cli.add_command(stats)