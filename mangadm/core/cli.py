import click
from enum import Enum
from pathlib import Path
from auto_click_auto import enable_click_shell_completion_option

from mangadm import MangaDM, __version__
from mangadm.utils import CliUtility


class FormatType(str, Enum):
    cbz = "cbz"
    epub = "epub"


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
        click.echo(f"Version: {__version__}")
        ctx.exit()


@click.group(
    help="MangaDM CLI: Download manga chapters and manage settings.",
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
    "--force/--no-force",
    "-f",
    default=default_settings.get("force", False),
    help="Re-download incomplete image.",
)
@click.option(
    "--delete/--no-delete",
    "-d",
    default=default_settings.get("delete", False),
    help="Delete data after successful download.",
)
@click.option(
    "--format",
    "-m",
    type=click.Choice([ft.value for ft in FormatType], case_sensitive=False),
    default=default_settings.get("format", "cbz"),
    help="Format for downloaded manga.",
)
@click.option(
    "--transient/--no-transient",
    "-t",
    default=default_settings.get("transient", True),
    help="Enable transient mode.",
)
@click.option(
    "--update-details/--no-update-details",
    "-u",
    default=default_settings.get("update_details", False),
    help="Update `details.json` and re-download cover.",
)
def download(json_file, dest, limit, force, delete, format, transient, update_details):
    """Download manga chapters based on a JSON file."""

    # Start download process
    downloader = MangaDM(
        json_file=Path(json_file),
        dest_path=dest,
        limit=limit,
        force_download=force,
        delete_on_success=delete,
        format=format,
        transient=transient,
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
            "name": "force",
            "message": "Re-download incomplete image?",
            "default": default_settings.get("force", False),
        },
        {
            "type": "confirm",
            "name": "delete",
            "message": "Delete chapter data from JSON after successful download?",
            "default": default_settings.get("delete", False),
        },
        {
            "type": "confirm",
            "name": "transient",
            "message": "Activate transient mode (will disappear after completion)?",
            "default": default_settings.get("transient", False),
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
    from InquirerPy import prompt

    user_settings = prompt(settings)

    # Save defaults if requested
    if user_settings.get("save_defaults"):
        if user_settings:
            CliUtility.save_stored_settings(user_settings)
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