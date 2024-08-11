import signal
import sys
import os
from typing import Any, Optional
from MangaDM.downloader import Downloader
from MangaDM.utility import Logger, Utility


class MangaDM:
    """
    Manages the downloading of manga chapters from a JSON file. Handles
    initializing directories, downloading cover images, and processing chapters.
    """

    def __init__(
        self,
        json_file: str,
        dest_path: str = ".",
        chapters_limit: int = -1,
        force_download: bool = False,
        delete_if_success: bool = False,
    ) -> None:
        """
        Initialize the MangaDM with the path to the JSON file.

        :param json_file: Path to the JSON file containing manga data.
        :param dest_path: Destination path where manga chapters will be downloaded.
        :param chapters_limit: Number of chapters to download. If -1, download all chapters.
        :param force_download: If True, re-downloads files even if they exist.
        :param delete_if_success: If True, delete chapter data from JSON after successful download.
        """
        self.dest_path = dest_path
        self.json_file = json_file
        self.data = Utility.load_data(json_file)
        self.downloaded = 0
        self.chapters_limit = chapters_limit
        self.force_download = force_download
        self.delete_if_success = delete_if_success

        self.all_images_downloaded = True
        self.success_count = 0
        self.failure_count = 0
        self.chapters_downloaded = 0

        signal.signal(signal.SIGINT, self.signal_handler)
        signal.signal(signal.SIGTERM, self.signal_handler)

    def init_manga_directory(self, base_folder: str) -> None:
        cover_url = self.data[0].get("cover")
        if cover_url:
            filename = os.path.join(base_folder, "cover.jpg")
            if os.path.exists(filename):
                return
            Logger.info("Downloading cover image...")
            downloader = Downloader(dest_path=base_folder, name="cover.jpg")
            downloader.download_file(url=cover_url)
        else:
            Logger.warning("No cover image URL found in JSON data.")

    def process_images(self) -> None:
        """Process and download images based on the data from the JSON file."""
        if not self.data:
            Logger.error("No data available to process.")
            return

        manga_name = self.data[0].get("manganame", "UnknownManga")
        base_folder = os.path.join(self.dest_path, manga_name)
        self.init_manga_directory(base_folder)

        for entry in self.data:
            if self.chapters_limit != -1 and self.downloaded >= self.chapters_limit:
                break

            title: str = entry.get("title", "UnknownChapter").replace("/", "_")
            folder = os.path.join(base_folder, title)
            images = entry.get("images", [])

            downloader = Downloader(folder, self.force_download)
            success, failed = downloader.download_files(urls=images)

            self.success_count += success
            self.failure_count += failed
            if failed:
                self.all_images_downloaded = False

            if self.all_images_downloaded and self.delete_if_success:
                self.data.remove(entry)
                Utility.save_data(self.json_file, self.data)

            self.all_images_downloaded = True
            self.chapters_downloaded += 1

        self.log_download_results()

    def log_download_results(self) -> None:
        message = (
            f"Successfully downloaded {self.success_count} file{'s' if self.success_count != 1 else ''}. "
            f"Failed to download {self.failure_count} file{'s' if self.failure_count != 1 else ''}."
        )
        Logger.info(message)

    def signal_handler(self, sig: int, frame: Optional[Any]) -> None:
        Logger.warning("Termination signal received. Shutting down gracefully...")
        self.log_download_results()
        sys.exit(0)

    def start(self):
        self.process_images()
