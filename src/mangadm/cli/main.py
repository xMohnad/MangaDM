from pathlib import Path
from typing import Any, Dict, Optional, cast

import click

from mangadm.cli import CliUtility, PartialMatchGroup

cli_util = CliUtility()


@click.group(
    help="A CLI tool for downloading manga chapters based on a JSON metadata file.",
    context_settings={"help_option_names": ["-h", "--help"]},
    cls=PartialMatchGroup,
)
@click.version_option(cli_util.version, "--version", "-V")
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
    type=click.Choice(cli_util.formats, case_sensitive=False),
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
    from mangadm import FormatType, MangaDM

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

    from InquirerPy.resolver import prompt
    from prompt_toolkit.completion import PathCompleter

    current = cli_util.settings
    style = {
        "completion-menu.completion": "bg:#444444 #ffffff",
        "completion-menu.completion.current": "bg:#00afff #ffffff",
        "scrollbar.background": "bg:#333333",
        "scrollbar.button": "bg:#888888",
    }
    questions = [
        {
            "type": "input",
            "name": "dest",
            "message": "Download destination:",
            "completer": PathCompleter(only_directories=True, expanduser=True),
            "validate": lambda val: len(val.strip()) > 0,
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
            "choices": cli_util.formats,
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
    answers = prompt(questions, style=style, style_override=False)
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


@cli.command(name="tui", help="Open interactive TUI.")
def run_tui():
    from trogon import tui

    tui()(cli)()


@cli.group(cls=PartialMatchGroup)
def completion() -> None:
    """Manage shell completion scripts for this CLI tool."""
    pass


@completion.command(name="install")
@click.argument(
    "shell",
    required=False,
    metavar="<shell>",
    type=click.Choice(cli_util.shells),
)
def install_script(shell: Optional[str]) -> None:
    """Install shell autocompletion script."""
    from click_completion import install

    selected_shell = cli_util.validate_shell(shell)
    shell, path = install(selected_shell)
    click.secho(f"{shell} completion installed in {path}", fg="green")


@completion.command()
@click.argument(
    "shell",
    required=False,
    metavar="<shell>",
    type=click.Choice(cli_util.shells),
)
def show(shell: Optional[str]) -> None:
    """Show the autocompletion script for inspection."""
    from click_completion import get_code

    selected_shell = cli_util.validate_shell(shell)
    click.echo(get_code(selected_shell))


@completion.command()
def shells():
    """List all supported shell types for completion."""
    click.echo("Supported shell types:")
    from click_completion import shells

    for shell, doc in shells.items():
        click.echo(f"  - {shell}: {doc}")


if __name__ == "__main__":
    cli()
