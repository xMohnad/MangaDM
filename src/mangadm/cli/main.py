from importlib.metadata import version
from pathlib import Path
from typing import Any, Dict, cast

import click
from auto_click_auto import enable_click_shell_completion_option
from InquirerPy.resolver import prompt
from trogon import tui

from mangadm import MangaDM
from mangadm.cli import CliUtility, PartialMatchGroup
from mangadm.components.types import FormatType

cli_util = CliUtility()


@tui()
@click.group(
    help="A CLI tool for downloading manga chapters based on a JSON metadata file.",
    context_settings={"help_option_names": ["-h", "--help"]},
    cls=PartialMatchGroup,
)
@enable_click_shell_completion_option(program_name="mangadm")
@click.version_option(version("mangadm"), "--version", "-V")
def cli():
    pass


@cli.command()
@click.argument("json_file", type=click.Path(exists=True, readable=True))
@click.option(
    "--dest",
    "-p",
    default=cli_util.settings.get("dest", "."),
    help="Download destination.",
)
@click.option(
    "--limit",
    "-l",
    default=cli_util.settings.get("limit", -1),
    help="Limit chapters.",
)
@click.option(
    "--delete/--no-delete",
    "-d",
    default=cli_util.settings.get("delete", False),
    help="Delete after success.",
)
@click.option(
    "--format",
    "-f",
    type=click.Choice([ft.value for ft in FormatType], case_sensitive=False),
    default=cli_util.settings.get("format", "cbz"),
    help="Download format.",
)
@click.option(
    "--update-details/--no-update-details",
    "-u",
    default=cli_util.settings.get("update_details", False),
    help="Update details file and cover.",
)
def download(json_file, dest, limit, delete, format, update_details):
    """Download manga chapters based on a JSON file."""
    MangaDM(
        json_file=Path(json_file),
        dest_path=dest,
        limit=limit,
        delete_on_success=delete,
        format=FormatType(format),
        update_details=update_details,
    ).start()


@cli.command()
def configure():
    """Open configuration UI."""
    current = cli_util.settings
    questions = [
        {
            "type": "input",
            "name": "dest",
            "message": "Download destination:",
            "default": str(current.get("dest", ".")),
        },
        {
            "type": "input",
            "name": "limit",
            "message": "Number of chapters (-1 = all):",
            "default": str(current.get("limit", -1)),
            "validate": lambda r: r == "-1" or (r.isdigit() and int(r) > 0),
            "invalid_message": "Enter -1 or a positive integer.",
            "filter": lambda r: int(r) if r == "-1" or r.isdigit() else -1,
        },
        {
            "type": "list",
            "name": "format",
            "message": "Choose format:",
            "choices": [ft.value for ft in FormatType],
            "default": current.get("format", "cbz"),
        },
        {
            "type": "confirm",
            "name": "delete",
            "message": "Delete JSON data after download?",
            "default": current.get("delete", False),
        },
        {
            "type": "confirm",
            "name": "update_details",
            "message": "Update details and re-download cover?",
            "default": current.get("update_details", False),
        },
        {
            "type": "confirm",
            "name": "save_defaults",
            "message": "Save these settings as default?",
            "default": True,
        },
    ]
    answers = prompt(questions)
    if answers.get("save_defaults"):
        assert isinstance(answers, dict), "Expected answers to be a dict"
        settings_dict = cast(Dict[str, Any], answers)
        cli_util.save(settings_dict)
        cli_util.display_settings(settings_dict)
        click.secho("Settings saved successfully.", fg="green")
    else:
        click.secho("Settings not saved.", fg="yellow")


@cli.command()
def example():
    """Display an example JSON structure."""
    cli_util.show_example()


@cli.command()
def reset():
    """Reset saved settings."""
    cli_util.reset()


@cli.command()
def view():
    """View current settings."""
    cli_util.display_settings(cli_util.settings)


if __name__ == "__main__":
    cli()
