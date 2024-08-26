from manga_dm import MangaDM
import click
import json
import os
from manga_dm.utils import Utility


@click.command()
@click.argument("json_file", type=click.Path(exists=True), required=False)
@click.option(
    "--dest",
    "-p",
    default=None,
    help="Destination path for downloading manga chapters.",
)
@click.option(
    "--limit",
    "-l",
    default=None,
    type=int,
    help="Number of chapters to download. If -1, download all chapters.",
)
@click.option(
    "--force",
    "-f",
    is_flag=True,
    help="Re-download files even if they exist.",
)
@click.option(
    "--delete",
    "-d",
    is_flag=True,
    help="Delete chapter data from JSON after successful download.",
)
@click.option(
    "--cbz",
    "-z",
    is_flag=True,
    help="Save the chapter as CBZ.",
)
@click.option(
    "--example",
    "-e",
    is_flag=True,
    help="Display an example JSON structure for the input file.",
)
@click.option(
    "--set-defaults",
    "-s",
    is_flag=True,
    help="Save the current settings as default.",
)
@click.help_option("--help", "-h")
def cli(json_file, dest, limit, force, delete, cbz, example, set_defaults):
    """A command-line tool for downloading manga chapters based on a JSON file."""

    # Load existing default settings
    default_settings = Utility.load_default_settings()

    # Merge CLI options with default settings
    dest = dest or default_settings.get("dest", ".")
    limit = limit if limit is not None else default_settings.get("limit", -1)
    force = force or default_settings.get("force", False)
    delete = delete or default_settings.get("delete", False)
    cbz = cbz or default_settings.get("cbz", False)

    # Display example JSON
    if example:
        example_json = [
            {
                "manganame": "Jujutsu Kaisen",
                "cover": "https://example.com/cover.jpg",
                "title": "Jujutsu Kaisen - 256",
                "images": [
                    "https://example.com/image1.jpg",
                    "https://example.com/image2.jpg",
                    "https://example.com/image3.jpg",
                ],
            },
            {
                "manganame": "Boruto",
                "cover": "https://example.com/cover.jpg",
                "title": "Boruto - 7",
                "images": [
                    "https://example.com/image1.jpg",
                    "https://example.com/image2.jpg",
                    "https://example.com/image3.jpg",
                ],
            },
        ]
        click.echo(json.dumps(example_json, indent=4))
        return

    # Save settings as defaults if requested
    if set_defaults:
        new_defaults = {
            "dest": dest,
            "limit": limit,
            "force": force,
            "delete": delete,
            "cbz": cbz,
        }
        Utility.save_default_settings(new_defaults)
        click.echo("Default settings saved.")
        return

    if not json_file:
        click.echo("Error: Missing argument 'JSON_FILE'.")
        click.echo("For help, try 'manga-dm --help'.")
        return

    if not os.path.exists(dest):
        click.echo(f"Destination path '{dest}' does not exist. Creating it...")
        os.makedirs(dest)

    manga_downloader = MangaDM(
        json_file=json_file,
        dest_path=dest,
        chapters_limit=limit,
        force_download=force,
        delete_on_success=delete,
        save_as_CBZ=cbz,
    )

    manga_downloader.start()


if __name__ == "__main__":
    cli()
