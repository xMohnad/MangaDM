import asyncio
from contextlib import asynccontextmanager
from functools import cached_property
from pathlib import Path
from typing import Dict, List, Optional, Union

import aiohttp
from aiohttp.client import ClientSession
from rich.progress import (
    BarColumn,
    DownloadColumn,
    Progress,
    SpinnerColumn,
    TextColumn,
    TransferSpeedColumn,
)

from mangadm.components.types import DownloadResult, DownloadStatus, Status


class SlideLoader(Status):
    """Asynchronous image downloader with progress tracking."""

    def __init__(
        self,
        urls: Optional[List[str]] = None,
        save_dir: Union[Path, str] = Path("chapter"),
        max_concurrent: int = 4,
        chunk_size: int = 1024,
        timeout: int = 30,
    ):
        """
        Initialize the SlideLoader.

        Args:
            urls: List of image URLs to download
            save_dir: Directory to save downloaded images
            max_concurrent: Maximum concurrent downloads
            chunk_size: Size of chunks for downloading files
            timeout: Timeout for HTTP requests in seconds
        """
        self._urls = urls or []
        self.max_concurrent = max_concurrent
        self.chunk_size = chunk_size
        self.timeout = timeout
        self.save_dir = save_dir

        self._current_tasks: Dict[asyncio.Task, str] = {}  # Task -> URL mapping
        self._results: List[DownloadResult] = []

        self.progress = self._progress
        self.spinner = self._spinner_progress
        self.temp_ext = "_tmp"

    @cached_property
    def spinner_task(self):
        return self.spinner.add_task(
            "",
            total=len(self.urls),
            chapter=0,
            total_chapters=0,
        )

    def get_size(self, local_filename: Path) -> int:
        """Get the size of a file if it exists, otherwise return 0."""
        return local_filename.stat().st_size if local_filename.exists() else 0

    def save_image_error(self, save_path):
        from mangadm.assets import image_error

        with open(save_path, "wb") as f:
            f.write(image_error())

    @property
    def save_dir(self) -> Path:
        """Get the current save directory."""
        return self._save_dir

    @save_dir.setter
    def save_dir(self, save_dir: Union[Path, str]):
        """Set a new save directory."""
        if not isinstance(save_dir, Path):
            save_dir = Path(save_dir)
        save_dir.mkdir(exist_ok=True, parents=True)
        self._save_dir = save_dir

    @property
    def urls(self) -> List[str]:
        """Get the current list of URLs."""
        return self._urls

    @urls.setter
    def urls(self, urls: List[str]):
        """Set a new list of URLs and cancel any ongoing downloads."""
        for task in self._current_tasks:
            task.cancel()
        self._urls = urls

    @property
    def _spinner_progress(self) -> Progress:
        return Progress(
            SpinnerColumn(),
            TextColumn(
                "[bold blue]Chapter {task.fields[chapter]}/{task.fields[total_chapters]}"
            ),
            TextColumn("• Page {task.completed}/{task.total}"),
            BarColumn(),
            TextColumn("[progress.percentage]{task.percentage:>3.0f}%"),
            expand=True,
        )

    @property
    def _progress(self) -> Progress:
        """Create a new progress bar instance."""
        return Progress(
            TextColumn("[bold blue]{task.description}", justify="right"),
            BarColumn(),
            TransferSpeedColumn(),
            DownloadColumn(),
            transient=True,
            expand=True,
        )

    @property
    def totel(self):
        return self._totel

    @totel.setter
    def totel(self, value: tuple[int, int, int]):
        self._totel = value

    def _make_name(
        self,
        url: str,
        filename: Optional[Union[Path, str]] = None,
        index: Optional[int] = None,
    ) -> Path:
        """Generate a filename from URL and options."""
        suffix = Path(url).suffix
        if index is not None:
            return Path(f"{index:02d}{suffix}")
        if filename and not isinstance(filename, Path):
            filename = Path(filename)
        if filename:
            return filename.with_suffix(suffix)

        raise ValueError("Either 'filename' or 'index' must be provided.")

    @asynccontextmanager
    async def get_session(self):
        async with aiohttp.ClientSession() as session:
            yield session

    async def download(
        self,
        url: str,
        session: ClientSession,
        filename: Path,
        final_filepath: Path,
    ) -> DownloadResult:
        """Download a single file."""
        temp_filepath = self.save_dir / f"{filename.name}{self.temp_ext}"
        completed = self.get_size(temp_filepath)
        headers = {"Range": f"bytes={completed}-"} if completed else {}
        timeout = aiohttp.ClientTimeout(total=self.timeout)
        id = None
        try:
            async with session.get(url, timeout=timeout, headers=headers) as response:
                response.raise_for_status()
                if response.status != 206 and "Accept-Ranges" not in response.headers:
                    completed = 0
                    headers.pop("Range", None)

                content_length = response.headers.get("content-length")
                total_size = int(content_length) + completed if content_length else None
                task_id = self.progress.add_task(
                    str(filename), total=total_size, completed=completed
                )
                id = task_id
                with open(temp_filepath, "ab" if completed > 0 else "wb") as f:
                    async for chunk in response.content.iter_chunked(self.chunk_size):
                        f.write(chunk)
                        self.progress.update(task_id, advance=len(chunk))

                # Rename temp file to final filename after successful download
                temp_filepath.rename(final_filepath)
                self.progress.remove_task(task_id)
                return DownloadResult(DownloadStatus.SUCCESS, final_filepath, url=url)

        except aiohttp.ClientResponseError as e:
            result = DownloadResult(DownloadStatus.REPLACED, temp_filepath, e, url=url)
            if e.status in [401, 403, 404]:
                self.save_image_error(final_filepath)

            if id is not None:
                self.progress.remove_task(id)
            self.progress.log(result)
            return result

        except Exception as e:
            result = DownloadResult(DownloadStatus.FAILED, temp_filepath, e, url=url)
            if id is not None:
                self.progress.remove_task(id)
                self.progress.log(result)
            return result

    async def download_all(self) -> None:
        """Download all images concurrently with a limit on simultaneous downloads."""
        semaphore = asyncio.Semaphore(self.max_concurrent)
        chapters, skipped_count, count = self.totel
        self.spinner.update(
            self.spinner_task,
            total=len(self.urls),
            chapter=skipped_count + count,
            total_chapters=chapters,
        )

        async with self.get_session() as session:

            async def _download_task(index: int, url: str):
                filename = self._make_name(url, index=index)
                final_path = self.save_dir / filename

                async with semaphore:
                    result = await self.download(url, session, filename, final_path)
                    self.spinner.update(self.spinner_task, advance=1)
                    self._results.append(result)

            tasks = []
            for i, url in enumerate(self.urls, 1):
                filename = self._make_name(url, index=i)
                final_path = self.save_dir / filename
                if final_path.exists():
                    self._results.append(
                        DownloadResult(
                            DownloadStatus.SKIPPED,
                            path=final_path,
                            url=url,
                        )
                    )
                    continue
                tasks.append(asyncio.create_task(_download_task(i, url)))
                self.spinner.update(
                    self.spinner_task, completed=len(self.urls) - len(tasks)
                )

            await asyncio.gather(*tasks, return_exceptions=True)

    def all(self) -> List[DownloadResult]:
        """Synchronously download all images."""
        asyncio.run(self.download_all())
        return self._results.copy()

    async def _one(self, url: str, filename: Path) -> DownloadResult:
        """Download a single file."""
        final_filepath = self.save_dir / self._make_name(url, filename)
        async with self.get_session() as session:
            return await self.download(url, session, filename, final_filepath)

    def one(self, url: str, filename: Path) -> bool:
        """Download a single file synchronously."""
        result = asyncio.run(self._one(url, filename))
        return (
            isinstance(result, DownloadResult)
            and result.status == DownloadStatus.SUCCESS
        )
