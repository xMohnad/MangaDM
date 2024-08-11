from MangaDM import MangaDM
import click
import json
import os


@click.command()
@click.argument("json_file", type=click.Path(exists=True), required=False)
@click.option(
    "--dest", "-p", default=".", help="Destination path for downloading manga chapters."
)
@click.option(
    "--limit",
    "-l",
    default=-1,
    type=int,
    help="Number of chapters to download. If -1, download all chapters.",
)
@click.option(
    "--force", "-f", is_flag=True, help="Re-download files even if they exist."
)
@click.option(
    "--delete",
    "-d",
    is_flag=True,
    help="Delete chapter data from JSON after successful download.",
)
@click.option(
    "--example",
    "-e",
    is_flag=True,
    help="Display an example JSON structure for the input file.",
)
def cli(json_file, dest, limit, force, delete, example):
    """
    A command-line tool for downloading manga chapters based on a JSON file.
    """
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
            }
        ]
        click.echo(json.dumps(example_json, indent=4))
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
        delete_if_success=delete,
    )

    manga_downloader.start()


if __name__ == "__main__":
    cli()
