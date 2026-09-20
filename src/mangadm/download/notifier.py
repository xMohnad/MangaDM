from __future__ import annotations

from collections import Counter
from typing import TYPE_CHECKING

from rich import get_console
from rich.console import Group
from rich.filesize import decimal
from rich.live import Live
from rich.markup import escape
from rich.progress import (
    BarColumn,
    MofNCompleteColumn,
    Progress,
    ProgressColumn,
    TextColumn,
    TimeElapsedColumn,
    TransferSpeedColumn,
)
from rich.text import Text

from mangadm.download.model import DownloadState

if TYPE_CHECKING:
    from collections.abc import Sequence
    from types import TracebackType

    from rich.console import Console
    from rich.progress import Task

    from mangadm.download.model import Download


class _BytesColumn(ProgressColumn):
    """Shows the number of bytes downloaded."""

    def render(self, task: Task) -> Text:
        return Text(decimal(int(task.completed)), style="progress.filesize")


class RichNotifier:
    """Shows chapter progress and transfer speed in the terminal."""

    def __init__(self, console: Console | None = None) -> None:
        """Initialize the progress display."""
        console = console or get_console()
        self._chapters = Progress(
            TextColumn("[bold green]{task.description}"),
            BarColumn(),
            MofNCompleteColumn(),
            TimeElapsedColumn(),
            console=console,
        )
        self._traffic = Progress(
            TextColumn("[bold blue]Downloaded"),
            _BytesColumn(),
            TransferSpeedColumn(),
            console=console,
        )
        self._live = Live(Group(self._chapters, self._traffic), console=console, transient=True)
        self._overall = self._chapters.add_task("Chapters", total=0)
        self._current = self._chapters.add_task("", total=0, visible=False)
        self._bytes = self._traffic.add_task("", total=None)

    def __enter__(self) -> RichNotifier:
        """Start the live display."""
        self._live.start()
        return self

    def __exit__(
        self,
        exc_type: type[BaseException] | None,
        exc: BaseException | None,
        tb: TracebackType | None,
    ) -> None:
        """Stop the live display."""
        self._live.stop()

    def on_start(self, total_chapters: int) -> None:
        """Set the number of queued chapters."""
        self._chapters.update(self._overall, total=total_chapters)

    def on_chapter_start(self, download: Download) -> None:
        """Show the chapter that is now downloading."""
        description = escape(download.title)
        self._chapters.reset(self._current, total=len(download.pages), description=description, visible=True)

    def on_page_done(self, download: Download) -> None:
        """Advance the current chapter bar."""
        self._chapters.advance(self._current)

    def on_chapter_done(self, download: Download) -> None:
        """Advance the overall bar."""
        self._chapters.advance(self._overall)

    def on_bytes(self, count: int) -> None:
        """Add downloaded bytes to the transfer counter."""
        self._traffic.advance(self._bytes, count)


def print_summary(downloads: Sequence[Download], console: Console | None = None) -> None:
    """Print how many chapters were downloaded and why the others failed."""
    console = console or get_console()
    if not downloads:
        console.print("Nothing to download.")
        return

    counts = Counter(d.state for d in downloads)
    parts = [f"[green]{counts[DownloadState.DOWNLOADED]} downloaded[/]"]
    if failed := counts[DownloadState.ERROR]:
        parts.append(f"[red]{failed} failed[/]")
    if pending := counts[DownloadState.QUEUE] + counts[DownloadState.DOWNLOADING]:
        parts.append(f"[yellow]{pending} not started[/]")
    console.print(" | ".join(parts))

    for download in downloads:
        if download.state is DownloadState.ERROR:
            console.print(f"  [red]x[/] {escape(download.title)}: {escape(download.error or 'unknown error')}")
    if failed:
        console.print("Partial downloads were kept. Run the same command again to resume.")
