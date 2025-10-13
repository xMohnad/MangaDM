from __future__ import annotations

import asyncio
import logging
import random
from collections.abc import Awaitable, Coroutine
from contextlib import AsyncExitStack, suppress
from functools import cached_property, wraps
from pathlib import Path
from typing import Callable, Final, TypeVar

import aiohttp
from aiohttp import ClientSession, ClientTimeout
from rich.filesize import decimal
from rich.logging import RichHandler
from rich.progress import (
    BarColumn,
    DownloadColumn,
    MofNCompleteColumn,
    Progress,
    SpinnerColumn,
    TaskID,
    TaskProgressColumn,
    TextColumn,
    TimeElapsedColumn,
    TransferSpeedColumn,
)

from mangadm.archiver import MangaArchiver
from mangadm.schema.formats import FormatType
from mangadm.schema.manga import Chapter, Manga

TRANSLATION_TABLE: Final[dict[int, str]] = str.maketrans(
    {
        "/": "_",
        "\\": "_",
        '"': "_",
        "'": "_",
        "?": "",
        "*": " ",
        "%": " ",
        "$": "_",
        "#": "_",
        "@": "_",
        "~": "_",
        "}": "-",
        "{": "-",
        "|": "_",
        ":": "_",
        "+": "_",
        "=": "_",
        "[": "-",
        "]": "-",
        "&": "-",
    }
)

TEMP_EXT: Final[str] = "_tmp"

RETRY_EXCEPTIONS: Final[tuple[type[Exception], ...]] = (
    aiohttp.ServerTimeoutError,
    aiohttp.ClientConnectionError,
    asyncio.TimeoutError,
    aiohttp.ClientResponseError,
)

T = TypeVar("T")


def temp_path(path: Path) -> Path:
    """Return a temporary path derived from the given file or folder path."""
    return path.with_name(path.name + TEMP_EXT)


def get_size(local_filename: Path) -> int:
    """Get the size of a file if it exists, otherwise return 0."""
    return local_filename.stat().st_size if local_filename.exists() else 0


def retry_delay(
    attempt: int,
    base: float = 2.5,
    factor: float = 2.5,
    max_delay: float = 30.0,
    jitter: float = 0.5,
) -> float:
    """Compute exponential backoff delay with optional jitter."""
    delay = min(base * factor ** (attempt - 1), max_delay)
    return max(0, delay * (1 + random.uniform(-jitter, jitter)))


def run_async(
    func: Callable[..., Coroutine[None, None, T]],
) -> Callable[..., T | asyncio.Task[T]]:
    """
    Decorator to allow calling an async function directly.

    - If called inside a running event loop, returns asyncio.Task[T].
    - If called outside an event loop, returns T (result of asyncio.run).
    """

    @wraps(func)
    def wrapper(*args: object, **kwargs: object) -> T | asyncio.Task[T]:
        try:
            loop = asyncio.get_running_loop()
        except RuntimeError:
            loop = None

        if loop and loop.is_running():
            return asyncio.create_task(func(*args, **kwargs))
        else:
            return asyncio.run(func(*args, **kwargs))

    return wrapper


class MangaDM:
    """Manage the full manga download and archiving workflow.

    The class automates downloading manga chapters from URLs listed in a JSON file
    or Manga object.


    Attributes:
        manga (Manga): Parsed manga metadata.
        dest_path (Path): Output directory for downloads.
        limit (int): Maximum chapters to process (-1 means all).
        format (FormatType): Output archive format
        update_details (bool): Whether to re-download metadata and cover image.
        chunk_size (int): Download chunk size in bytes.
        archive_existing (bool): Whether to archive existing complete chapters.
        retry_server_errors (bool): Whether to retry on 5xx HTTP responses.
        retries (int): Maximum number of retry attempts per request.
        manga_folder (Path): Directory containing all manga chapters and files.
        details_path (Path): Path to stored manga metadata JSON file.
        cover_path (Path): Path to the downloaded cover image.
        _progress (Progress): Progress bar for per-file downloads.
        _spinner (Progress): Spinner display for chapter-level status.
        _semaphore (asyncio.Semaphore): Concurrency limiter for download tasks.
        _timeout (ClientTimeout): Global network timeout configuration.
        _archiver (MangaArchiver): Utility for creating archive.
        logger (logging.Logger): Logger configured with RichHandler.
    """

    def __init__(
        self,
        json: Path | Manga,
        *,
        dest_path: Path | None = None,
        limit: int = -1,
        format: FormatType = FormatType.cbz,
        update_details: bool = False,
        timeout: int = 30,
        chunk_size: int = 1024,
        max_concurrent: int = 4,
        retries: int = 3,
        archive_existing: bool = True,
        retry_server_errors: bool = True,
    ) -> None:
        """Initialize MangaDM instance with configuration.

        Args:
            json (Path | Manga): Manga JSON path or Manga object.
            dest_path (Path | None, optional): Destination directory. Defaults to current path.
            limit (int, optional): Maximum chapters to download. -1 means no limit.
            format (FormatType, optional): Archive format (cbz or epub). Defaults to cbz.
            update_details (bool, optional): If True, re-download manga metadata. Defaults to False.
            timeout (int, optional): Network timeout in seconds. Defaults to 30.
            chunk_size (int, optional): Download chunk size in bytes. Defaults to 1024.
            max_concurrent (int, optional): Maximum concurrent downloads. Defaults to 4.
            retries (int, optional): Maximum retry attempts per file. Defaults to 3.
            archive_existing (bool, optional): If True, archive completed chapters automatically. Defaults to True.
            retry_server_errors (bool, optional): Retry on server errors (5xx). Defaults to True.
        """
        self.manga: Manga = json if isinstance(json, Manga) else Manga.from_json_file(json)
        self.dest_path: Path = dest_path or Path(".")
        self.limit: int = limit
        self.format: FormatType = format
        self.update_details: bool = update_details
        self.chunk_size: int = chunk_size
        self.archive_existing: bool = archive_existing

        # retry options
        self.retry_server_errors: bool = retry_server_errors
        self.retries: int = retries

        details = self.manga.details
        manga_name = details.title.translate(TRANSLATION_TABLE)

        # paths
        self.manga_folder: Path = self.dest_path / f"{manga_name} ({details.source})"
        self.details_path: Path = self.manga_folder / "details.json"
        self.cover_path: Path = self.manga_folder / "cover.png"

        self._progress: Progress = Progress(
            TextColumn("[bold blue]{task.description}", justify="right"),
            BarColumn(),
            TransferSpeedColumn(),
            DownloadColumn(),
            TaskProgressColumn(),
            transient=True,
        )
        self._spinner: Progress = Progress(
            SpinnerColumn(),
            TextColumn("[bold green]{task.description}[/]"),
            TextColumn("• [bold blue]Chapter {task.fields[chapter]}/{task.fields[chapters]}[/] •"),
            MofNCompleteColumn(),
            BarColumn(),
            TaskProgressColumn(),
            TimeElapsedColumn(),
            transient=True,
        )

        self._semaphore: asyncio.Semaphore = asyncio.Semaphore(max_concurrent)
        self._timeout: ClientTimeout = ClientTimeout(timeout)
        self._archiver: MangaArchiver = MangaArchiver()

        self.logger: logging.Logger = logging.getLogger("mangadm")
        self.logger.addHandler(RichHandler(show_time=False, show_path=False))

    @cached_property
    def _spinner_task(self) -> TaskID:
        """Initialize spinner task for chapter-level progress."""
        return self._spinner.add_task(
            "",
            total=0,
            chapter=0,
            chapters=len(self.manga.chapters),
        )

    async def _handle_http_error(self, e: aiohttp.ClientResponseError, temp: Path, image_path: Path) -> bool:
        """Handle specific HTTP errors and decide whether to retry.

        Args:
            e (aiohttp.ClientResponseError): The raised HTTP exception.
            temp (Path): Temporary download file path.
            image_path (Path): Target image path.

        Returns:
            bool: True if retry should occur, False otherwise.
        """
        if e.status in (401, 403, 404):
            from mangadm.assets import placeholder_image

            image_path.write_bytes(placeholder_image())
            self.logger.error("Replaced %s with placeholder (HTTP %d).", image_path.name, e.status)
            return False

        if e.status == 416:
            size = e.headers.get("Content-Range", "") if e.headers else ""
            size = int(size.split("/")[-1]) if "/" in size else 0
            self.logger.warning(
                "416 Range error for %s (server=%s, local=%s). Restarting.",
                temp,
                decimal(size) if size else "unknown",
                decimal(get_size(temp)),
            )
            with suppress(Exception):
                temp.unlink()
            return True

        if e.status == 429:
            retry_after = e.headers.get("Retry-After") if e.headers else None
            msg = f"Retry after {retry_after}" if retry_after else "Please retry later"
            self.logger.warning("Too many requests. %s", msg)
            raise e

        if e.status < 500 and not self.retry_server_errors:
            self.logger.warning(
                "HTTP %d received. Retry disabled by configuration (retry_server_errors=False).", e.status
            )
            return False

        return True

    async def download(self, url: str, session: ClientSession, path: Path) -> None:
        """Save manga metadata and cover image before downloading chapters.

        Writes details JSON and downloads the cover image if missing or outdated.

        Args:
            session (ClientSession): Active aiohttp client session.
        """
        temp = temp_path(path)

        for attempt in range(1, self.retries + 1):
            task_id: None | TaskID = None
            local_size = get_size(temp)
            headers = {"Range": f"bytes={local_size}-"} if local_size else {}
            try:
                async with session.get(url, timeout=self._timeout, headers=headers) as resp:
                    # Reset if server does not support ranges
                    if resp.status != 206 and "Accept-Ranges" not in resp.headers:
                        local_size, headers = 0, {}

                    total = int(resp.headers.get("content-length", 0)) + local_size or None
                    task_id = self._progress.add_task(path.name, total=total, completed=local_size)

                    resp.raise_for_status()
                    with temp.open("ab" if local_size else "wb") as f:
                        async for chunk in resp.content.iter_chunked(self.chunk_size):
                            f.write(chunk)
                            self._progress.update(task_id, advance=len(chunk))

                    temp.rename(path)
                    return self._progress.remove_task(task_id)

            except Exception as e:
                if task_id:
                    self._progress.remove_task(task_id)

                if attempt == self.retries:
                    self.logger.exception("Final attempt #%d failed: %s", attempt, path.name)
                    raise

                if isinstance(e, aiohttp.ClientResponseError):
                    if not await self._handle_http_error(e, temp, path):
                        raise

                elif not isinstance(e, RETRY_EXCEPTIONS):
                    self.logger.exception("Non-retryable exception on attempt #%d for %s", attempt, path)
                    raise

                delay = retry_delay(attempt)
                self.logger.warning("Attempt %d on %s failed (%r). Retrying in %.2f", attempt, path.name, e, delay)
                await asyncio.sleep(delay)

    async def _prepare_details(self, session: ClientSession) -> None:
        """Save manga metadata and cover image before downloading chapters.

        Writes details JSON and downloads the cover image if missing or outdated.

        Args:
            session (ClientSession): Active aiohttp client session.
        """
        if not self.details_path.exists() or self.update_details:
            self.manga.details.to_json(self.details_path)

        cover = self.manga.details.cover
        cover_path = self.cover_path.with_suffix(Path(cover).suffix)
        if not cover_path.exists() or self.update_details:
            await self.download(cover, session, cover_path)

    async def _task(self, url: str, image_path: Path, session: ClientSession) -> None:
        """Wrapper around download with semaphore limiting concurrency.

        Args:
            url (str): Image URL.
            image_path (Path): Output file path.
            session (ClientSession): Active aiohttp client session.
        """
        async with self._semaphore:
            await self.download(url, session, image_path)
            self._spinner.update(self._spinner_task, advance=1)

    def _skip_chapter(self, path: Path, chapter: Chapter) -> bool:
        """Determine if a chapter should be skipped.

        Args:
            path (Path): Chapter folder path.
            chapter (Chapter): Chapter metadata.

        Returns:
            bool: True if chapter should be skipped.
        """
        if not chapter.images:
            self.logger.warning(f"Chapter '{chapter.title}' has no images.")
            return True

        archive_file = path.with_suffix(f".{self.format.value}")
        if archive_file.is_file():
            self.logger.info("Skipping %s: %s already exists.", path.name, archive_file.name)
            return True

        if path.exists() and len(chapter.images) == len(list(path.iterdir())):
            if self.archive_existing:
                self.logger.info("Chapter '%s' exists, will attempt archiving.", path.name)
                self._archiver.create_archive(path, self.format, chapter.title)
            return True

        return False

    @run_async
    async def start(self) -> None:
        """Start the manga download process."""
        self.manga_folder.mkdir(parents=True, exist_ok=True)
        async with AsyncExitStack() as stack:
            stack.enter_context(self._progress)
            stack.enter_context(self._spinner)
            session = await stack.enter_async_context(ClientSession())
            await self._prepare_details(session)
            for idx, chapter in enumerate(self.manga.chapters, 1):
                title = chapter.title.translate(TRANSLATION_TABLE)
                chapter_path = self.manga_folder / title
                temp = temp_path(chapter_path)
                temp.mkdir(exist_ok=True)

                if self.limit > 0 and idx > self.limit:
                    self.logger.warning("Limit %d reached at '%s'", self.limit, chapter.title)
                    break

                if self._skip_chapter(chapter_path, chapter):
                    continue

                self._spinner.update(
                    self._spinner_task,
                    total=len(chapter.images),
                    completed=0,
                    description=chapter.title,
                    chapter=idx,
                )

                tasks: set[Awaitable[None]] = set()
                for i, url in enumerate(chapter.images, 1):
                    image_path = temp / f"{i:02d}{Path(url).suffix}"
                    if image_path.exists():
                        self.logger.debug("Image '%s' in %s already exists. Skipping.", image_path.name, chapter.title)
                        self._spinner.update(self._spinner_task, advance=1)
                        continue

                    tasks.add(self._task(url, image_path, session))

                if skipped := len(chapter.images) - len(tasks):
                    self.logger.debug("Total skipped %d existing images in chapter '%s'", skipped, chapter.title)

                errs = await asyncio.gather(*tasks, return_exceptions=True)
                if any([isinstance(err, BaseException) for err in errs]):
                    self.logger.warning(f"Chapter '{chapter.title}' has errors. Skipping.")
                    continue

                temp.rename(chapter_path)
                self._archiver.create_archive(chapter_path, self.format, chapter.title)
