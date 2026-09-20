from __future__ import annotations

from typing import TYPE_CHECKING

from mangadm.download.downloader import Downloader
from mangadm.download.http import ImageFetcher, create_session
from mangadm.download.notifier import NOTIFIERS
from mangadm.download.provider import DownloadProvider

if TYPE_CHECKING:
    from mangadm.download.model import Download, Options
    from mangadm.manga import Manga


async def download_manga(manga: Manga, options: Options) -> list[Download]:
    """Download a manga according to `options` and return the queue with final states."""
    provider = DownloadProvider(options.dest, manga.details, options.format)
    with NOTIFIERS[options.progress]() as notifier:
        async with create_session(options.timeout, options.max_concurrent) as session:
            fetcher = ImageFetcher(session, retries=options.retries, listener=notifier)
            return await Downloader(manga, options, provider, fetcher, notifier).run()
