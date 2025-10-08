from __future__ import annotations

import logging
from pathlib import Path
from typing import Annotated

import typer

from mangadm import __config__, __version__
from mangadm.schema.formats import FormatType

app: typer.Typer = typer.Typer(help="A tool for downloading manga.", rich_markup_mode="rich")


def version_callback(value: bool) -> None:
    if value:
        typer.echo(f"mangadm, version {__version__}")
        raise typer.Exit()


@app.callback(context_settings=dict(help_option_names=["-h", "--help"]))
def common(
    ctx: typer.Context,
    _: Annotated[
        bool,
        typer.Option(
            "--version",
            "-V",
            help="Show the [bold cyan]version[/] and exit.",
            is_eager=True,
            is_flag=True,
            callback=version_callback,
        ),
    ] = False,
    verbose: Annotated[
        bool,
        typer.Option(
            "--verbose",
            "-v",
            help="Use [bold cyan]verbose[/] output",
            is_flag=True,
        ),
    ] = False,
) -> None:
    # Set logging level
    logger = logging.getLogger("mangadm")
    logger.setLevel(logging.DEBUG if verbose else logging.WARNING)

    import yaml

    if __config__.exists():
        with __config__.open() as f:
            ctx.default_map = yaml.safe_load(f)


@app.command()
def download(
    json_file: Annotated[
        Path, typer.Argument(..., dir_okay=False, exists=True, help="Path to manga [bold cyan]JSON[/]")
    ],
    dest: Annotated[
        str,
        typer.Option("--dest", "-p", help="[bold cyan]dest[/]ination folder.", file_okay=False, writable=True),
    ] = ".",
    limit: Annotated[
        int,
        typer.Option(
            "--limit", "-l", help="Maximum number of chapters to download. Use -1 for no [bold cyan]limit[/].", min=-1
        ),
    ] = -1,
    format: Annotated[
        FormatType,
        typer.Option("--format", "-f", help="Archive [bold cyan]format[/]."),
    ] = FormatType.cbz,
    update: Annotated[
        bool,
        typer.Option(
            "--update/--no-update", "-u", help="[bold cyan]Update[/] manga details and cover before downloading."
        ),
    ] = False,
    timeout: Annotated[
        int,
        typer.Option("--timeout", "-t", help="HTTP request [bold cyan]timeout[/] in seconds."),
    ] = 30,
    chunk_size: Annotated[
        int,
        typer.Option("--chunk-size", "-c", help="[bold cyan]Chunk size[/] for each download (in bytes)."),
    ] = 1024,
    max_concurrent: Annotated[
        int,
        typer.Option("--max-concurrent", "-m", help="Maximum number of [bold cyan]concurrent[/] downloads."),
    ] = 4,
    retries: Annotated[
        int, typer.Option("--retries", "-r", help="Number of [bold cyan]retries[/] for failed downloads")
    ] = 3,
    archive_existing: Annotated[
        bool,
        typer.Option("--archive-existing/--no-archive-existing", help="[bold cyan]Archive existing[/] chapters"),
    ] = False,
    retry_server_errors: Annotated[
        bool,
        typer.Option(
            "--retry-server-errors/--no-retry-server-errors",
            help="[bold cyan]Retry[/] downloads automatically when a [yellow]server error (5xx)[/] occurs.",
        ),
    ] = True,
) -> None:
    """[bold cyan]Download[/] manga from a given JSON metadata file."""

    from mangadm.core import MangaDM

    MangaDM(
        json_file,
        dest_path=Path(dest),
        limit=limit,
        format=format,
        update_details=update,
        timeout=timeout,
        chunk_size=chunk_size,
        max_concurrent=max_concurrent,
        retries=retries,
        archive_existing=archive_existing,
        retry_server_errors=retry_server_errors,
    ).start()


@app.command()
def show_config(
    path_only: Annotated[
        bool, typer.Option("--path", "-p", help="Show only the config file [bold cyan]path[/]")
    ] = False,
) -> None:
    """
    [bold cyan]Show[/] the current [yellow]config[/]uration.

    Options are mapped directly to YAML keys:
    • --format -> [green]format[/green]
    • --archive-existing -> [green]archive_existing[/green]
    """
    if path_only:
        typer.echo(__config__)
        raise typer.Exit()

    import yaml

    if __config__.exists():
        with __config__.open() as f:
            typer.echo(yaml.dump(yaml.safe_load(f), sort_keys=False))
    else:
        typer.echo("No config file found. You can create one at:")
        typer.echo(__config__)


if __name__ == "__main__":
    app()
