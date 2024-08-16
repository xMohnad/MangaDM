import signal
import sys
import os
import time
from typing import Any, Optional
from manga_dm.downloader import Downloader
from manga_dm.utils import Logger, Utility, StatsManager
import requests
import glob


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

        signal.signal(signal.SIGINT, self._signal_handler)
        signal.signal(signal.SIGTERM, self._signal_handler)

    def check_and_update_chapters(self, folder: str, images: list) -> None:
        """
        Check if all images are downloaded in the given folder.

        :param folder: Directory where images are expected to be located.
        :param images: List of expected image file names.
        """
        if os.path.isdir(folder):  # Ensure that the folder exists
            # Check for temporary files in the folder
            temp_files_exist = glob.glob(os.path.join(folder, "*_temp"))
            # Check if all images are downloaded (i.e., no temporary files and number of images matches)
            if not temp_files_exist and len(images) == len(os.listdir(folder)):
                self.stats_manager.update_skipped_chapters()
                return True
        return False

    def init_manga_directory(self, base_folder: str) -> None:
        cover_url = self.data[0].get("cover")
        if cover_url:
            filename = os.path.join(base_folder, "cover.jpg")
            if os.path.exists(filename) and not self.force_download:
                return

            Logger.info("Downloading cover...")
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
        else:
            Logger.warning("No cover found in JSON data.")

    def process_images(self) -> None:
        """Process and download images based on the data from the JSON file."""
        if not self.data:
            Logger.error("No data available to process.")
            return

        manga_name = self.data[0].get("manganame", "UnknownManga")
        base_folder = os.path.join(self.dest_path, manga_name)

        self.init_manga_directory(base_folder)

        for count, entry in enumerate(self.data, start=1):
            if (
                self.chapters_limit != -1
                and self.stats_manager.chapters_downloaded >= self.chapters_limit
            ):
                break

            images = entry.get("images", [])
            if not images:
                Logger.error("No images available to download.")
                continue

            title = entry.get("title", "UnknownChapter").replace("/", "_")
            folder = os.path.join(base_folder, title)

            if self.check_and_update_chapters(folder, images):
                continue

            downloader = Downloader(
                dest_path=folder,
                force_download=self.force_download,
                session=self.session,
                stats_manager=self.stats_manager,
            )
            downloader.download_files(images, count)

            self.stats_manager.update_chapters_downloaded()

            if self.stats_manager.get_statistics()["failure"]:
                self.stats_manager.all_images_downloaded = False

            if self.stats_manager.all_images_downloaded and self.delete_on_success:
                self.data.remove(entry)
                Utility.save_data(self.json_file, self.data)

            self.stats_manager.all_images_downloaded = True

    def _signal_handler(self, sig: int, frame: Optional[Any]) -> None:
        self.session.close()
        Utility.save_data(self.json_file, self.data)
        Logger.warning("Termination signal received. Shutting down gracefully...")
        sys.exit(0)

    def start(self) -> None:
        self.process_images()
