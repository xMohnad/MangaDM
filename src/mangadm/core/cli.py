import json
import os
from pathlib import Path
from typing import Any, Dict

import click
from auto_click_auto import enable_click_shell_completion_option

from mangadm import MangaDM
from mangadm.components.types import FormatType


class CliUtility:
    @staticmethod
    def get_config_path() -> str:
        """
        Get the path to the configuration file.

        - On Linux: ~/.config/manga_dm/config.json
        - On Windows: %APPDATA%/manga_dm/config.json

        Creates the directory if it does not exist.

        Returns:
            str: Absolute path to the configuration file.
        """
        appdata = os.getenv("APPDATA")
        config_dir = Path(appdata) if appdata else Path.home() / ".config"
        config_dir = config_dir / "manga_dm"
        config_dir.mkdir(parents=True, exist_ok=True)
        return str(config_dir / "config.json")

    @staticmethod
    def load_stored_settings() -> Dict[str, Any]:
        """Load stored settings from the configuration file."""
        config_path = CliUtility.get_config_path()

        if not os.path.exists(config_path):
            return {}

        try:
            with open(config_path, "r", encoding="utf-8") as config_file:
                return json.load(config_file)
        except (IOError, json.JSONDecodeError) as e:
            click.echo(f"Failed to load config from {config_path}: {e}")
            return {}

    @staticmethod
    def save_stored_settings(settings: Dict[str, Any]) -> None:
        """Save settings to the configuration file."""
        config_path = CliUtility.get_config_path()

        try:
            with open(config_path, "w", encoding="utf-8") as config_file:
                json.dump(settings, config_file, ensure_ascii=False, indent=4)
        except (IOError, OSError) as e:
            click.echo(f"Failed to save config to {config_path}: {e}")

    @staticmethod
    def display_example_json():
        """Display an example JSON structure."""
        # Define common values
        image_urls = [
            "https://example.com/image1.jpg",
            "https://example.com/image2.jpg",
            "https://example.com/image3.jpg",
            "https://example.com/image4.jpg",
            "etc",
        ]

        example_json = {
            "details": {
                "source": "Example Source Name",
                "manganame": "Example Manga Name",
                "cover": "https://example.com/cover.jpg",
                "description": "Example Description",
                "genre": ["genre 1", "genre 2", "etc"],
                "author": "Akutami Gege",
                "artist": "Akutami Gege",
            },
            "chapters": [
                {
                    "title": "chapter 256 - Example Title",
                    "images": image_urls,
                },
                {
                    "title": "chapter 257 - Example Title",
                    "images": image_urls,
                },
                {
                    "title": "chapter 258 - Example Title",
                    "images": image_urls,
                },
            ],
        }

        from rich.console import Console

        console = Console()
        console.print_json(json.dumps(example_json))


def display_settings(settings):
    """Display settings in a readable format."""
    from rich.console import Console

    console = Console()
    console.print("=" * 40)
    for key, value in settings.items():
        if key == "save_defaults":
            continue
        console.print(f"{key.capitalize():<15}: {value}")
    console.print("=" * 40)


def print_version(ctx, param, value):
    if value:
        from importlib.metadata import version

        click.echo(f"Version: {version('mangadm')}")
        ctx.exit()


@click.group(
    help="A CLI tool for Download manga chapters based on the metadata specified in a JSON file.",
    context_settings={"help_option_names": ["-h", "--help"]},
)
@enable_click_shell_completion_option(program_name="mangadm")
@click.option(
    "--version",
    "-v",
    is_flag=True,
    is_eager=True,
    callback=print_version,
    help="Show the application version.",
)
def cli(version):
    pass


default_settings = CliUtility.load_stored_settings()


@cli.command()
@click.argument(
    "json_file",
    type=click.Path(exists=True, file_okay=True, dir_okay=False, readable=True),
)
@click.option(
    "--dest",
    "-p",
    default=default_settings.get("dest", "."),
    help="Destination path for downloading manga.",
)
@click.option(
    "--limit",
    "-l",
    default=default_settings.get("limit", -1),
    help="Number of chapters to download (-1 for all).",
)
@click.option(
    "--delete/--no-delete",
    "-d",
    default=default_settings.get("delete", False),
    help="Delete data after successful download.",
)
@click.option(
    "--format",
    "-f",
    type=click.Choice([ft.value for ft in FormatType], case_sensitive=False),
    default=default_settings.get("format", "cbz"),
    help="Format for downloaded manga.",
)
@click.option(
    "--update-details/--no-update-details",
    "-u",
    default=default_settings.get("update_details", False),
    help="Update `details.json` and re-download cover.",
)
def download(json_file, dest, limit, delete, format, update_details):
    """Download manga chapters based on a JSON file."""

    # Start download process
    downloader = MangaDM(
        json_file=Path(json_file),
        dest_path=dest,
        limit=limit,
        delete_on_success=delete,
        format=FormatType(format),
        update_details=update_details,
    )
    downloader.start()


@cli.command()
def configure():
    """Open configuration UI."""
    settings = [
        {
            "type": "input",
            "name": "dest",
            "message": "Destination path for downloading manga:",
            "default": str(default_settings.get("dest", ".")),
        },
        {
            "type": "input",
            "name": "limit",
            "message": "Number of chapters to download (-1 for all):",
            "default": str(default_settings.get("limit", -1)),
            "validate": lambda result: (result.isdigit() and int(result) > 0)
            or result == "-1"
            or False,
            "invalid_message": "Please enter -1 or a positive integer greater than 0.",
            "filter": lambda result: (
                int(result) if result.isdigit() or result == "-1" else -1
            ),
        },
        {
            "type": "list",
            "name": "format",
            "message": "Select the format for saving manga files:",
            "choices": [ft.value for ft in FormatType],
            "default": default_settings.get("format", "cbz"),
        },
        {
            "type": "confirm",
            "name": "delete",
            "message": "Delete chapter data from JSON after successful download?",
            "default": default_settings.get("delete", False),
        },
        {
            "type": "confirm",
            "name": "update_details",
            "message": "Update `details.json` and re-download cover.",
            "default": default_settings.get("update_details", False),
        },
        {
            "type": "confirm",
            "name": "save_defaults",
            "message": "Would you like to save these settings as the new default?",
            "default": True,
        },
    ]

    # Prompt for settings and flags
    from InquirerPy.resolver import prompt

    user_settings = prompt(settings)

    # Save defaults if requested
    if user_settings.get("save_defaults"):
        if user_settings:
            CliUtility.save_stored_settings(user_settings)  # pyright: ignore
            display_settings(user_settings)
            click.secho("Settings saved successfully.", fg="green")
        return
    else:
        click.secho("Settings were not saved as default.", fg="red")


@cli.command()
def example():
    """Display an example JSON structure."""
    CliUtility.display_example_json()


@cli.command()
def view():
    """View current settings."""
    display_settings(default_settings)


if __name__ == "__main__":
    cli()
