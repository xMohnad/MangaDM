from __future__ import annotations

from collections import Counter
from typing import TYPE_CHECKING, Final, Self

from rich import get_console
from rich.console import Group
from rich.filesize import decimal
from rich.live import Live
from rich.markup import escape
from rich.progress import (
    BarColumn,
    DownloadColumn,
    MofNCompleteColumn,
    Progress,
    ProgressColumn,
    SpinnerColumn,
    TaskID,
    TaskProgressColumn,
    TextColumn,
    TimeElapsedColumn,
    TransferSpeedColumn,
)
from rich.text import Text

from mangadm.download.model import DownloadState, ProgressStyle

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


class _LiveNotifier:
    """Owns the live terminal display made of the given progress bars."""

    def __init__(self, console: Console | None, *bars: Progress) -> None:
        """Initialize the live display."""
        self._live = Live(Group(*bars), console=console or get_console(), transient=True)

    def __enter__(self) -> Self:
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


class CompactNotifier(_LiveNotifier):
    """Shows an overall bar, the current chapter bar and the total transfer speed."""

    def __init__(self, console: Console | None = None) -> None:
        """Initialize the progress bars."""
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
        super().__init__(console, self._chapters, self._traffic)
        self._overall = self._chapters.add_task("Chapters", total=0)
        self._current = self._chapters.add_task("", total=0, visible=False)
        self._bytes = self._traffic.add_task("", total=None)

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

    def on_transfer_start(self, name: str, total: int | None, completed: int) -> int:
        """Nothing to show per file."""
        return 0

    def on_transfer_advance(self, transfer: int, count: int) -> None:
        """Add downloaded bytes to the transfer counter."""
        self._traffic.advance(self._bytes, count)

    def on_transfer_end(self, transfer: int) -> None:
        """Nothing to show per file."""


class DetailedNotifier(_LiveNotifier):
    """Shows one bar per downloading file above a bar for the current chapter."""

    def __init__(self, console: Console | None = None) -> None:
        """Initialize the progress bars."""
        console = console or get_console()
        self._files = Progress(
            TextColumn("[bold blue]{task.description}", justify="right"),
            BarColumn(),
            TransferSpeedColumn(),
            DownloadColumn(),
            TaskProgressColumn(),
            console=console,
        )
        self._chapters = Progress(
            SpinnerColumn(),
            TextColumn("[bold green]{task.description}[/]"),
            TextColumn("• [bold blue]Chapter {task.fields[chapter]}/{task.fields[chapters]}[/] •"),
            MofNCompleteColumn(),
            BarColumn(),
            TaskProgressColumn(),
            TimeElapsedColumn(),
            console=console,
        )
        super().__init__(console, self._files, self._chapters)
        self._chapter = self._chapters.add_task("", total=0, chapter=0, chapters=0)
        self._started = 0
        self._total_chapters = 0

    def on_start(self, total_chapters: int) -> None:
        """Set the number of queued chapters."""
        self._total_chapters = total_chapters
        self._chapters.update(self._chapter, chapters=total_chapters)

    def on_chapter_start(self, download: Download) -> None:
        """Show the chapter that is now downloading."""
        self._started += 1
        self._chapters.reset(
            self._chapter,
            total=len(download.pages),
            description=escape(download.title),
            chapter=self._started,
            chapters=self._total_chapters,
        )

    def on_page_done(self, download: Download) -> None:
        """Advance the chapter bar."""
        self._chapters.advance(self._chapter)

    def on_chapter_done(self, download: Download) -> None:
        """Nothing to update: the chapter bar already shows the position."""

    def on_transfer_start(self, name: str, total: int | None, completed: int) -> int:
        """Add a bar for the file."""
        return self._files.add_task(escape(name), total=total, completed=completed)

    def on_transfer_advance(self, transfer: int, count: int) -> None:
        """Advance the bar of the file."""
        self._files.advance(TaskID(transfer), count)

    def on_transfer_end(self, transfer: int) -> None:
        """Remove the bar of the file."""
        self._files.remove_task(TaskID(transfer))


NOTIFIERS: Final = {
    ProgressStyle.compact: CompactNotifier,
    ProgressStyle.detailed: DetailedNotifier,
}


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
