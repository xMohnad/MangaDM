from __future__ import annotations

import asyncio
import logging
import random
from typing import TYPE_CHECKING, Final

import aiohttp

from mangadm.download.model import DownloadError, NullTransferListener, PageUnavailableError
from mangadm.download.provider import TMP_FILE_SUFFIX
from mangadm.images import HEAD_SIZE, detect_extension

if TYPE_CHECKING:
    from pathlib import Path

    from mangadm.download.model import TransferListener

logger = logging.getLogger(__name__)

CHUNK_SIZE: Final = 64 * 1024
MAX_RETRY_DELAY: Final = 60.0


UNAVAILABLE_STATUS: Final = frozenset({401, 403, 404, 410})
RETRYABLE_STATUS: Final = frozenset({408, 416, 425, 429})
RETRYABLE_ERRORS: Final = (aiohttp.ClientConnectionError, aiohttp.ClientPayloadError, TimeoutError)


def create_session(timeout: float, connections: int) -> aiohttp.ClientSession:
    """Create a session with an idle-socket timeout and a bounded connection pool."""
    return aiohttp.ClientSession(
        timeout=aiohttp.ClientTimeout(total=None, sock_connect=timeout, sock_read=timeout),
        connector=aiohttp.TCPConnector(limit=connections),
        raise_for_status=True,
        trust_env=True,
    )


def retry_delay(attempt: int, retry_after: float | None = None) -> float:
    """Seconds to wait before retry number `attempt + 1`: 2, 4, 8... with jitter."""
    if retry_after is not None:
        return min(retry_after, MAX_RETRY_DELAY)
    return min(2 << attempt, MAX_RETRY_DELAY) * random.uniform(0.75, 1.25)


def _is_retryable(error: Exception) -> bool:
    if isinstance(error, aiohttp.ClientResponseError):
        return error.status >= 500 or error.status in RETRYABLE_STATUS
    return isinstance(error, RETRYABLE_ERRORS)


def _retry_after(error: Exception) -> float | None:
    if isinstance(error, aiohttp.ClientResponseError) and error.headers:
        value = error.headers.get("Retry-After", "")
        return float(value) if value.isdigit() else None
    return None


def _describe(error: Exception) -> str:
    if isinstance(error, aiohttp.ClientResponseError):
        return f"HTTP {error.status}"
    if isinstance(error, TimeoutError):
        return "timed out"
    return str(error) or type(error).__name__


class ImageFetcher:
    """Downloads images with resume support and retries."""

    def __init__(
        self,
        session: aiohttp.ClientSession,
        *,
        retries: int = 3,
        listener: TransferListener | None = None,
    ) -> None:
        """Initialize the fetcher."""
        self._session = session
        self._retries = retries
        self._listener = listener or NullTransferListener()

    async def fetch(self, url: str, directory: Path, stem: str, *, referer: str | None = None) -> Path:
        """Download `url` into `directory` as `stem.<ext>` and return the final path.

        Raises:
            PageUnavailableError: If the server answers 401, 403, 404 or 410.
            DownloadError: If the download fails after all retries.
        """
        tmp = directory / f"{stem}{TMP_FILE_SUFFIX}"
        attempt = 0
        while True:
            try:
                content_type = await self._download(url, tmp, referer)
                return self._finalize(tmp, directory / stem, content_type)
            except (aiohttp.ClientError, TimeoutError) as e:
                status = e.status if isinstance(e, aiohttp.ClientResponseError) else None
                if status in UNAVAILABLE_STATUS:
                    raise PageUnavailableError(f"HTTP {status}") from e
                if status == 416:
                    tmp.unlink(missing_ok=True)
                if attempt >= self._retries or not _is_retryable(e):
                    raise DownloadError(_describe(e)) from e
                delay = retry_delay(attempt, _retry_after(e))
                logger.warning("%s: %s, retry %d/%d in %.1fs", url, _describe(e), attempt + 1, self._retries, delay)
                await asyncio.sleep(delay)
                attempt += 1

    async def _download(self, url: str, tmp: Path, referer: str | None) -> str:
        """Stream the response into `tmp`, resuming a partial file, and return the content type."""
        headers: dict[str, str] = {}
        if referer:
            headers["Referer"] = referer
        offset = tmp.stat().st_size if tmp.exists() else 0
        if offset:
            headers["Range"] = f"bytes={offset}-"

        async with self._session.get(url, headers=headers) as response:
            append = response.status == 206
            completed = offset if append else 0
            length = response.content_length
            total = None if length is None else completed + length

            transfer = self._listener.on_transfer_start(tmp.stem, total, completed)
            try:
                with tmp.open("ab" if append else "wb") as f:
                    async for chunk in response.content.iter_chunked(CHUNK_SIZE):
                        f.write(chunk)
                        self._listener.on_transfer_advance(transfer, len(chunk))
            finally:
                self._listener.on_transfer_end(transfer)

            if tmp.stat().st_size == 0:
                raise aiohttp.ClientPayloadError("empty response body")
            return response.content_type

    @staticmethod
    def _finalize(tmp: Path, target: Path, content_type: str) -> Path:
        """Rename the finished download using its detected image extension."""
        with tmp.open("rb") as f:
            head = f.read(HEAD_SIZE)
        dest = target.with_name(f"{target.name}.{detect_extension(head, content_type)}")
        tmp.replace(dest)
        return dest
