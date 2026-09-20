from __future__ import annotations

import asyncio
import logging
import tomllib
from pathlib import Path
from typing import Annotated

import typer
from rich import get_console
from rich.logging import RichHandler

from mangadm import __version__
from mangadm.archive import FormatType
from mangadm.config import CONFIG_PATH, load_config
from mangadm.download.model import DownloadState, Options, ProgressStyle
from mangadm.manga import Manga

app: typer.Typer = typer.Typer(
    help="A tool for downloading manga.",
    rich_markup_mode="rich",
    no_args_is_help=True,
    pretty_exceptions_show_locals=False,
)


def _version_callback(value: bool) -> None:
    if value:
        typer.echo(f"mangadm, version {__version__}")
        raise typer.Exit


def _setup_logging(verbose: bool) -> None:
    logger = logging.getLogger("mangadm")
    logger.setLevel(logging.DEBUG if verbose else logging.WARNING)
    logger.addHandler(RichHandler(show_time=False, show_path=False))


@app.callback(context_settings={"help_option_names": ["-h", "--help"]})
def common(
    ctx: typer.Context,
    _: Annotated[
        bool,
        typer.Option(
            "--version",
            "-V",
            help="Show the [bold cyan]version[/] and exit.",
            is_eager=True,
            callback=_version_callback,
        ),
    ] = False,
    verbose: Annotated[
        bool,
        typer.Option("--verbose", "-v", help="Use [bold cyan]verbose[/] output"),
    ] = False,
) -> None:
    """Configure logging and load the config file as defaults for `download`."""
    _setup_logging(verbose)
    try:
        ctx.default_map = load_config()
    except tomllib.TOMLDecodeError as e:
        raise typer.BadParameter(f"{CONFIG_PATH}: {e}") from e


@app.command()
def download(
    json_file: Annotated[
        Path,
        typer.Argument(dir_okay=False, exists=True, help="Path to manga [bold cyan]JSON[/]"),
    ],
    dest: Annotated[
        Path,
        typer.Option("--dest", "-p", help="[bold cyan]dest[/]ination folder.", file_okay=False, writable=True),
    ] = Path(),
    limit: Annotated[
        int,
        typer.Option(
            "--limit",
            "-l",
            help="Maximum number of new chapters to download. Use -1 for no [bold cyan]limit[/].",
            min=-1,
        ),
    ] = -1,
    format: Annotated[
        FormatType,
        typer.Option("--format", "-f", help="Archive [bold cyan]format[/]."),
    ] = FormatType.cbz,
    update: Annotated[
        bool,
        typer.Option("--update/--no-update", "-u", help="[bold cyan]Update[/] details and cover before downloading."),
    ] = False,
    timeout: Annotated[
        int,
        typer.Option("--timeout", "-t", help="Seconds without network activity before a request fails.", min=1),
    ] = 30,
    max_concurrent: Annotated[
        int,
        typer.Option("--max-concurrent", "-m", help="Maximum [bold cyan]concurrent[/] page downloads.", min=1),
    ] = 4,
    retries: Annotated[
        int,
        typer.Option("--retries", "-r", help="Number of [bold cyan]retries[/] for a failed page.", min=0),
    ] = 3,
    progress: Annotated[
        ProgressStyle,
        typer.Option(
            "--progress",
            "-P",
            help="[bold cyan]Progress[/] display: compact, or detailed with a bar for each downloading page.",
        ),
    ] = ProgressStyle.compact,
    allow_missing: Annotated[
        bool,
        typer.Option(
            "--allow-missing/--no-allow-missing",
            help="Archive chapters even if some pages are [bold cyan]missing[/] (HTTP 401/403/404/410).",
        ),
    ] = False,
) -> None:
    """[bold cyan]Download[/] manga from a given JSON metadata file."""
    from mangadm.download.api import download_manga
    from mangadm.download.notifier import print_summary

    try:
        manga = Manga.from_json_file(json_file)
    except ValueError as e:
        typer.secho(str(e), fg=typer.colors.RED, err=True)
        raise typer.Exit(2) from e

    options = Options(
        dest=dest,
        format=format,
        limit=limit,
        update_details=update,
        timeout=timeout,
        max_concurrent=max_concurrent,
        retries=retries,
        allow_missing=allow_missing,
        progress=progress,
    )
    downloads = asyncio.run(download_manga(manga, options))
    print_summary(downloads)
    if any(d.state is not DownloadState.DOWNLOADED for d in downloads):
        raise typer.Exit(1)


@app.command()
def show_config(
    path_only: Annotated[
        bool,
        typer.Option("--path", "-p", help="Show only the config file [bold cyan]path[/]"),
    ] = False,
) -> None:
    """[bold cyan]Show[/] the current [yellow]config[/]uration.

    The config file is TOML. Keys are the `download` option names:

    * format = "epub"

    * max_concurrent = 6
    """
    console = get_console()

    if path_only:
        console.print(CONFIG_PATH)
    elif CONFIG_PATH.is_file():
        console.print(CONFIG_PATH.read_text(encoding="utf-8"))
    else:
        console.print(f"No config file found. You can create one at:\n{CONFIG_PATH}")


if __name__ == "__main__":
    app()
