from typing import List, Optional
import requests
import os
from rich.progress import Progress
from manga_dm.utils import Utility, Logger, StatsManager


class Downloader:
    """Manages the downloading of files, supporting resume capability and displaying progress."""

    def __init__(
        self,
        dest_path: str = ".",
        force_download: bool = False,
        name: Optional[str] = None,
        session: Optional[requests.Session] = None,
        stats_manager: Optional[StatsManager] = None,
    ):
        self.session = session or requests.Session()
        self.download_path = dest_path
        self.force_download = force_download
        self.name = name
        self.stats_manager = stats_manager or StatsManager()

        self.total_chapters = self.stats_manager.get_statistics()["total_chapters"]

    def download(
        self,
        url: str,
        progress: Progress,
        img_count: Optional[int] = None,
        chapters_count: Optional[int] = None,
    ) -> bool:
        local_filename = self.name or Utility.get_filename_from_url(url)
        temp_filename = f"{local_filename}_temp"
        full_temp_path = os.path.join(self.download_path, temp_filename)
        full_path = os.path.join(self.download_path, local_filename)

        os.makedirs(self.download_path, exist_ok=True)

        if not self.force_download and os.path.exists(full_path):
            self.stats_manager.update_skipped()
            return True

        all_stats = self.stats_manager.get_statistics()
        if all_stats["skipped"] or all_stats["skipped_chapters"]:
            self.stats_manager.skip_msg()
            self.stats_manager.print_skip_msg = False

        if self.force_download and os.path.exists(full_path):
            os.remove(full_path)

        completed = Utility.get_size(full_temp_path)
        headers = {"Range": f"bytes={completed}-"}

        try:
            with progress:
                with self.session.get(url, headers=headers, stream=True) as response:
                    response.raise_for_status()
                    Tsize = int(response.headers.get("content-length", 0)) + completed
                    with open(full_temp_path, "ab") as file:
                        task = progress.add_task("", total=Tsize, completed=completed)
                        for chunk in response.iter_content(chunk_size=1024):
                            if chunk:
                                file.write(chunk)
                                progress.update(
                                    task,
                                    advance=len(chunk),
                                    count_chapters=chapters_count,
                                    completed_imgs=img_count,
                                )

            os.rename(full_temp_path, full_path)
            self.stats_manager.update_success()
            return True

        except requests.RequestException as e:
            Logger.error(f"Error downloading {local_filename}: {e}")
        except IOError as e:
            Logger.error(f"File error for {local_filename}: {e}")
        except Exception as e:
            Logger.error(f"An unexpected error occurred: {e}")

        self.stats_manager.update_failure()
        return False

    def download_files(
        self, urls: List[str], chapters_count: Optional[int] = None
    ) -> None:
        """Downloads files from the given URLs."""
        for img_count, url in enumerate(urls):
            progress = Utility.create_custom_progress_bar(
                len(urls), self.total_chapters
            )
            self.download(url, progress, img_count, chapters_count)

    def download_file(self, url: str):
        """Downloads a single file from the given URL."""
        progress = Utility.create_custom_progress_bar()
        if self.download(url, progress):
            return True
        return False
