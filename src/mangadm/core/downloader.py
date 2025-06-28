from typing import List, Optional
from rich.progress import Progress
import time, random, os
from contextlib import suppress
import requests
from requests.exceptions import ChunkedEncodingError
from pathlib import Path

from mangadm.utils import Utility
from mangadm.components import (
    Logger,
    StatsManager,
    SignalHandler,
    create_custom_progress_bar,
)


class Downloader:
    """Manages the downloading of files, supporting resume capability and displaying progress."""

    def __init__(
        self,
        stats_manager: Optional[StatsManager],
        force_download: bool = False,
        transient: bool = False,
        session: Optional[requests.Session] = None,
    ) -> None:

        self.stats_manager = stats_manager
        self.transient = transient
        self.force_download = force_download
        self.session = session or requests.Session()
        self.total_chapters = self.stats_manager.total_chapters

    def delay(self, attempt, max_delay=30, base=2):
        delay = min(base**attempt, max_delay)
        jitter = random.uniform(0, 0.5 * delay)
        delay = delay + jitter
        Logger.info(f"Retrying in {delay:.2f} seconds...")
        time.sleep(delay)

    def save_image_error(self, save_path):
        from mangadm.assets import image_error

        with open(save_path, "wb") as f:
            f.write(image_error())

    def _check_existing_file(self, full_path: str) -> bool:
        if os.path.exists(full_path):
            if not self.force_download:
                self.stats_manager.update_stat(skipped=True)
                return True
            if self.force_download:
                os.remove(full_path)
        if self.stats_manager.skipped_count or self.stats_manager.skipped_chapters:
            self.stats_manager.skip_msg()
            self.stats_manager.print_skip_msg = False
        return False

    def _handle_request_exception(
        self, e, attempt: int, max_retries: int, url: str, image_path: str
    ) -> bool:
        Logger.error(
            f"Attempt {attempt}/{max_retries} failed for {url} due to network issue: {e}",
            enhanced=False,
            count=False,
        )
        if isinstance(e, requests.HTTPError):
            if e.response.status_code in [401, 403, 404]:
                Logger.error(
                    f"Unrecoverable error ({e.response.status_code} {e.response.reason}) for {url}."
                )

                self.save_image_error(image_path)
                Logger.warning("The damaged image is replaced.")
                return "damaged"
            if e.response.status_code >= 500:
                Logger.error(
                    f"Server error ({e.response.status_code} {e.response.reason}) for {url}."
                )
                return False

        if attempt == max_retries:
            Logger.error(f"All {max_retries} attempts failed for {url}. Giving up.")
            return False
        self.delay(attempt)
        return True

    def _attempt_download(
        self,
        url: str,
        full_temp_path: Path ,
        full_path: Path,
        progress: Progress,
        img_count: Optional[int],
        chapters_count: Optional[int],
        max_retries: int,
    ):
        attempt = 1
        while attempt <= max_retries:
            try:
                SignalHandler.update_progress(progress)
                return self._download_content(
                    url, full_temp_path, full_path, progress, img_count, chapters_count
                )
            except ChunkedEncodingError:
                Logger.warning(
                    f"ChunkedEncodingError encountered on attempt {attempt} for {url}. Retrying without reducing the attempt count.",
                    enhanced=True,
                )
                self.delay(attempt)
                continue
            except (
                requests.ConnectionError,
                requests.Timeout,
                requests.HTTPError,
                requests.RequestException,
            ) as e:
                stats = self._handle_request_exception(
                    e, attempt, max_retries, url, full_path
                )
                if stats == "damaged":
                    return stats
                if not stats:
                    break
                attempt += 1
            except IOError as e:
                Logger.error(f"File error: {e}")
                with suppress(Exception):
                    full_temp_path.unlink()
                break
            except Exception as e:
                Logger.error(f"An unexpected error occurred: {e}")
                break

        self.stats_manager.update_stat(failure=True)
        self.stats_manager.all_images_downloaded = False
        return False

    def _download_content(
        self,
        url,
        full_temp_path,
        full_path,
        progress: Progress,
        img_count,
        chapters_count,
        chunk_size=1024,
        timeout=10
    ) -> bool:

        completed = Utility.get_size(full_temp_path)
        headers = {"Range": f"bytes={completed}-"} if completed else {}

        with progress, self.session.get(
            url, headers=headers, stream=True, timeout=timeout
        ) as response:
            response.raise_for_status()
            if response.status_code != 206 and "Accept-Ranges" not in response.headers:
                completed = 0
                headers.pop("Range", None)

            content_length = response.headers.get("content-length")
            Tsize = int(content_length) + completed if content_length else None

            task = progress.add_task("", total=Tsize, completed=completed)
            progress.update(
                task,
                count_chapters=chapters_count,
                completed_imgs=img_count
            )

            with open(full_temp_path, "ab" if completed > 0 else "wb") as file:
                for chunk in response.iter_content(chunk_size=chunk_size):
                    if chunk:
                        file.write(chunk)
                        progress.update(task, advance=len(chunk))

        Utility.rename(full_temp_path, full_path)
        self.stats_manager.update_stat(success=True)
        return True

    def download(
        self,
        url: str,
        dest_path: Path,
        progress: Progress,
        img_count: Optional[int] = None,
        chapters_count: Optional[int] = None,
        name: Optional[str] = None,
        max_retries: int = 3,
    ) -> bool:
        ext = Utility.get_ext_from_url(url)
        local_filename = name or f"{img_count:03}.{ext}"
        full_path = dest_path / local_filename
        full_temp_path = dest_path / f"{local_filename}_tmp"

        if self._check_existing_file(full_path):
            return True

        return self._attempt_download(
            url,
            full_temp_path,
            full_path,
            progress,
            img_count,
            chapters_count,
            max_retries,
        )

    def download_files(
        self,
        urls: List[str],
        dest_path: Path = ".",
        chapters_count: Optional[int] = None,
    ) -> None:
        dest_path.mkdir(parents=True ,exist_ok=True)
        for img_count, url in enumerate(urls, start=1):
            progress = create_custom_progress_bar(
                len(urls), self.total_chapters, transient=self.transient
            )
            self.download(url, dest_path, progress, img_count, chapters_count)

    def download_file(
        self, url: str, dest_path: Path = ".", name: Optional[str] = None
    ) -> bool:
        dest_path.mkdir(parents=True ,exist_ok=True)
        progress = create_custom_progress_bar(transient=False)
        return self.download(url, dest_path, progress, name=name)
