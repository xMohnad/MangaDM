from __future__ import annotations

from dataclasses import dataclass
from enum import Enum, auto
from pathlib import Path
from typing import TYPE_CHECKING, Protocol

from mangadm.archive import FormatType

if TYPE_CHECKING:
    from mangadm.manga import Chapter

MIN_PAGE_DIGITS = 3


class DownloadError(Exception):
    """A download failed."""


class PageUnavailableError(DownloadError):
    """The server permanently refused or lost the page (HTTP 401, 403, 404 or 410)."""


class InsufficientSpaceError(DownloadError):
    """There is not enough free disk space to continue."""


class DownloadState(Enum):
    """State of a chapter download."""

    QUEUE = auto()
    DOWNLOADING = auto()
    DOWNLOADED = auto()
    ERROR = auto()


class PageState(Enum):
    """State of a page download."""

    QUEUE = auto()
    DOWNLOADING = auto()
    READY = auto()
    MISSING = auto()
    ERROR = auto()


@dataclass(slots=True)
class Page:
    """A single page image."""

    number: int
    url: str
    state: PageState = PageState.QUEUE
    path: Path | None = None
    error: str | None = None


@dataclass(slots=True)
class Download:
    """A chapter in the download queue."""

    chapter: Chapter
    dirname: str
    pages: list[Page]
    state: DownloadState = DownloadState.QUEUE
    error: str | None = None

    @classmethod
    def create(cls, chapter: Chapter, dirname: str) -> Download:
        """Create a download with pages numbered from 1."""
        pages = [Page(number, url) for number, url in enumerate(chapter.images, 1)]
        return cls(chapter, dirname, pages)

    @property
    def title(self) -> str:
        """Chapter title."""
        return self.chapter.title

    @property
    def ready_paths(self) -> list[Path]:
        """Paths of the downloaded pages, in reading order."""
        return [page.path for page in self.pages if page.state is PageState.READY and page.path]

    @property
    def failed_pages(self) -> list[Page]:
        """Pages that are missing or failed."""
        return [page for page in self.pages if page.state in {PageState.MISSING, PageState.ERROR}]

    def page_stem(self, page: Page) -> str:
        """Zero-padded file name (without extension) of a page."""
        width = max(MIN_PAGE_DIGITS, len(str(len(self.pages))))
        return f"{page.number:0{width}d}"


@dataclass(frozen=True, slots=True)
class Options:
    """Download settings."""

    dest: Path = Path()
    format: FormatType = FormatType.cbz
    limit: int = -1
    update_details: bool = False
    timeout: float = 30
    max_concurrent: int = 4
    retries: int = 3
    allow_missing: bool = False


class Fetcher(Protocol):
    """Downloads a single image."""

    async def fetch(self, url: str, directory: Path, stem: str, *, referer: str | None = None) -> Path:
        """Download `url` into `directory` as `stem.<ext>` and return the final path."""
        ...


class Notifier(Protocol):
    """Receives download progress events."""

    def on_start(self, total_chapters: int) -> None:
        """Called once with the number of queued chapters."""
        ...

    def on_chapter_start(self, download: Download) -> None:
        """Called when a chapter starts downloading."""
        ...

    def on_page_done(self, download: Download) -> None:
        """Called when a page finishes, successfully or not."""
        ...

    def on_chapter_done(self, download: Download) -> None:
        """Called when a chapter finishes, successfully or not."""
        ...
