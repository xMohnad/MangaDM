from __future__ import annotations

import asyncio
import logging
import shutil
from typing import TYPE_CHECKING, Final

from mangadm.archive import create_archive
from mangadm.download.model import (
    Download,
    DownloadError,
    DownloadState,
    InsufficientSpaceError,
    PageState,
    PageUnavailableError,
)

if TYPE_CHECKING:
    from pathlib import Path

    from mangadm.download.model import Fetcher, Notifier, Options, Page
    from mangadm.download.provider import DownloadProvider
    from mangadm.manga import Manga

logger = logging.getLogger(__name__)

COVER_STEM: Final = "cover"


class Downloader:
    """Downloads the chapters of a manga one at a time, fetching pages concurrently."""

    def __init__(
        self,
        manga: Manga,
        options: Options,
        provider: DownloadProvider,
        fetcher: Fetcher,
        notifier: Notifier,
    ) -> None:
        """Initialize the downloader."""
        self._manga = manga
        self._options = options
        self._provider = provider
        self._fetcher = fetcher
        self._notifier = notifier
        self._semaphore = asyncio.Semaphore(options.max_concurrent)

    def queue_chapters(self) -> list[Download]:
        """Create downloads for chapters that are not archived yet, up to the limit."""
        chapters = self._manga.chapters
        queue: list[Download] = []
        for chapter, dirname in zip(chapters, self._provider.chapter_dirnames(chapters), strict=True):
            if not chapter.images:
                logger.warning("Chapter %r has no images.", chapter.title)
            elif self._provider.is_downloaded(dirname):
                logger.debug("Skipping %r: already downloaded.", chapter.title)
            else:
                queue.append(Download.create(chapter, dirname))

        limit = self._options.limit
        return queue[:limit] if limit > 0 else queue

    async def run(self) -> list[Download]:
        """Download every queued chapter and return the queue with final states."""
        await self._save_details()
        queue = self.queue_chapters()
        self._notifier.on_start(len(queue))

        for download in queue:
            try:
                await self._download_chapter(download)
            except InsufficientSpaceError as e:
                download.state, download.error = DownloadState.ERROR, str(e)
                logger.error("Stopping: %s", e)
                break
            finally:
                self._notifier.on_chapter_done(download)

        return queue

    async def _save_details(self) -> None:
        """Save details.json and the cover image."""
        details = self._manga.details
        provider = self._provider
        update = self._options.update_details

        if update or not provider.details_path.exists():
            details.to_json(provider.details_path)

        old_cover = provider.existing_images(provider.manga_dir).get(COVER_STEM)
        if not details.cover or (old_cover and not update):
            return

        try:
            cover = await self._fetcher.fetch(details.cover, provider.manga_dir, COVER_STEM)
        except (DownloadError, OSError) as e:
            logger.warning("Cover download failed: %s", e)
            return

        if old_cover and old_cover != cover:
            old_cover.unlink(missing_ok=True)

    async def _download_chapter(self, download: Download) -> None:
        """Download the pages of a chapter, then archive it."""
        if not self._provider.has_enough_space():
            raise InsufficientSpaceError("not enough free disk space")

        tmp_dir = self._provider.tmp_dir(download.dirname)
        tmp_dir.mkdir(exist_ok=True)
        existing = self._provider.existing_images(tmp_dir)

        download.state = DownloadState.DOWNLOADING
        self._notifier.on_chapter_start(download)

        async with asyncio.TaskGroup() as group:
            for page in download.pages:
                group.create_task(self._get_or_download_image(download, page, tmp_dir, existing))

        if not self._is_download_successful(download):
            download.state = DownloadState.ERROR
            download.error = self._failure_reason(download)
            return

        if download.failed_pages:
            logger.warning("Archiving %r without %d missing pages.", download.title, len(download.failed_pages))

        try:
            await asyncio.to_thread(self._archive_chapter, download, tmp_dir)
        except OSError as e:
            download.state, download.error = DownloadState.ERROR, f"archiving failed: {e}"
            logger.exception("Archiving %r failed.", download.title)
            return

        download.state = DownloadState.DOWNLOADED

    async def _get_or_download_image(
        self,
        download: Download,
        page: Page,
        tmp_dir: Path,
        existing: dict[str, Path],
    ) -> None:
        """Use the image already on disk or download it, and record the result on the page."""
        stem = download.page_stem(page)
        try:
            path = existing.get(stem)
            if path is None:
                async with self._semaphore:
                    page.state = PageState.DOWNLOADING
                    referer = download.chapter.document_location
                    path = await self._fetcher.fetch(page.url, tmp_dir, stem, referer=referer)
            page.path, page.state = path, PageState.READY
        except PageUnavailableError as e:
            page.state, page.error = PageState.MISSING, str(e)
            logger.error("Page %d of %r is unavailable: %s", page.number, download.title, e)
        except (DownloadError, OSError) as e:
            page.state, page.error = PageState.ERROR, str(e)
            logger.error("Page %d of %r failed: %s", page.number, download.title, e)

        self._notifier.on_page_done(download)

    def _is_download_successful(self, download: Download) -> bool:
        """Whether the chapter has every page it needs on disk."""
        missing_allowed = self._options.allow_missing
        for page in download.pages:
            if page.state is PageState.ERROR or (page.state is PageState.MISSING and not missing_allowed):
                return False
        paths = download.ready_paths
        return bool(paths) and all(path.is_file() for path in paths)

    @staticmethod
    def _failure_reason(download: Download) -> str:
        failed = download.failed_pages
        if not failed:
            return "no pages downloaded"
        return f"{len(failed)}/{len(download.pages)} pages failed ({failed[0].error})"

    def _archive_chapter(self, download: Download, tmp_dir: Path) -> None:
        """Archive the downloaded pages and remove the temporary folder."""
        create_archive(
            self._options.format,
            self._provider.archive_path(download.dirname),
            download.ready_paths,
            self._manga.details,
            download.chapter,
        )
        shutil.rmtree(tmp_dir)
