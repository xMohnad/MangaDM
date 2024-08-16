import os
from typing import Any, List, Optional
from manga_dm.downloader import Downloader
from manga_dm.utils import Logger, Utility, StatsManager, SignalHandler
import requests


class MangaDM:
    """
    Manages the downloading of manga chapters from a JSON file.
    Handles initializing directories, downloading cover images, and processing chapters.
    """

    def __init__(
        self,
        json_file: str,
        dest_path: str = ".",
        chapters_limit: int = -1,
        force_download: bool = False,
        delete_on_success: bool = False,
    ) -> None:
        self.dest_path = dest_path
        self.json_file = json_file
        self.data = Utility.load_data(json_file)
        self.chapters_limit = chapters_limit
        self.force_download = force_download
        self.delete_on_success = delete_on_success
        self.stats_manager = StatsManager()
        self.stats_manager.set_total_chapters(len(self.data))
        self.session = requests.Session()

        # Initialize SignalHandler with necessary resources
        SignalHandler.initialize(
            self.session, self.json_file, self.data, None, self.stats_manager
        )

    def setup_manga_dir_with_cover(self, base_folder: str) -> None:
        cover_url = self.data[0].get("cover")
        if cover_url:
            filename = os.path.join(base_folder, "cover.jpg")
            if os.path.exists(filename) and not self.force_download:
                return

            Logger.info("Downloading cover...")
            self._download_cover_image(base_folder, cover_url)
        else:
            Logger.warning("No cover found in JSON data.")

    def _download_cover_image(self, base_folder: str, cover_url: str) -> None:
        downloader = Downloader(
            dest_path=base_folder,
            force_download=self.force_download,
            name="cover.jpg",
            session=self.session,
            stats_manager=self.stats_manager,
        )
        if downloader.download_file(url=cover_url):
            Logger.success("Cover downloaded successfully")
        else:
            Logger.error("Failed to download cover.")

    def process_images(self) -> None:
        """Process and download images based on the data from the JSON file."""
        if not self.data:
            Logger.error("No data available to process.")
            return

        manga_name = self.data[0].get("manganame", "UnknownManga")
        base_folder = os.path.join(self.dest_path, manga_name)

        self.setup_manga_dir_with_cover(base_folder)

        for count, entry in enumerate(self.data, start=1):
            if self._should_stop_processing():
                break

            images = entry.get("images", [])
            if not images:
                Logger.error("No images available to download.")
                continue

            title = entry.get("title", "UnknownChapter").replace("/", "_")
            folder = os.path.join(base_folder, title)

            if Utility.check_if_chapters_downloaded(folder, images):
                self.stats_manager.update_skipped_chapters()
                continue

            self._download_chapter_images(folder, images, count, entry)

        self.stats_manager.log_download_results()

    def _should_stop_processing(self) -> bool:
        return (
            self.chapters_limit != -1
            and self.stats_manager.chapters_downloaded >= self.chapters_limit
        )

    def _download_chapter_images(
        self, folder: str, images: List[str], count: int, entry: dict
    ) -> None:
        downloader = Downloader(
            dest_path=folder,
            force_download=self.force_download,
            session=self.session,
            stats_manager=self.stats_manager,
        )
        downloader.download_files(images, count)

        self.stats_manager.update_chapters_downloaded()

        if self.stats_manager.get_statistics()["failure_chapter"]:
            self.stats_manager.all_images_downloaded = False

        if self.stats_manager.all_images_downloaded and self.delete_on_success:
            self.data.remove(entry)
            Utility.save_data(self.json_file, self.data)

        self.stats_manager.reset_failure_chapter()
        self.stats_manager.all_images_downloaded = True

    def start(self) -> None:
        self.process_images()
