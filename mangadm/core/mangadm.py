import os
from typing import List
import requests
import sys

from mangadm.core.downloader import Downloader
from mangadm.utils import Logger, Utility, StatsManager, SignalHandler

class MangaDM:
    """Manages the downloading of manga chapters from a JSON file."""

    def __init__(
        self, json_file: str, dest_path: str = ".", chapters_limit: int = -1,
        force_download: bool = False, delete_on_success: bool = False,
        save_as_CBZ: bool = False, transient: bool = False,
    ) -> None:
        if not json_file.endswith(".json"):
            Logger.error(f"Unsupported file format: {json_file}. Please use JSON format.")
            sys.exit(0)

        self.data = Utility.load_data(json_file)
        if not self.data:
            Logger.error("No data available to process.")
            sys.exit(0)

        self.json_file = json_file
        self.dest_path = dest_path
        self.chapters_limit = chapters_limit
        self.force_download = force_download
        self.delete_on_success = delete_on_success
        self.save_as_CBZ = save_as_CBZ
        self.transient = transient

        self.stats_manager = StatsManager()
        self.stats_manager.set_total_chapters(len(self.data))
        self.session = requests.Session()

        # Initialize SignalHandler with necessary resources
        SignalHandler.initialize(
            self.session, self.json_file, self.data, None, self.stats_manager
        )

        self.downloader = Downloader(
            stats_manager=self.stats_manager, force_download=self.force_download, 
            transient=self.transient, session=self.session
        )

        # Prepare translation table for sanitizing folder and file names
        self.translation_table = str.maketrans({
            "/": "_", "\\": "_", "\"": "_", "'": "_", "?": "", "*": " ", "%": " ", 
            "$": "_", "#": "_", "@": "_", "~": "_", "}": "-", "{": "-", "|": "_", 
            ":": "_", "+": "_", "=": "_", "[": "-", "]": "-", "&": " - "
        })

        manga_name = self.data[0].get("manganame", "UnknownManga").translate(self.translation_table)
        self.base_folder = os.path.join(self.dest_path, manga_name)

    def _should_stop_processing(self) -> bool:
        return (
            self.chapters_limit != -1
            and self.stats_manager.chapters_downloaded >= self.chapters_limit
        )

    def _setup_manga_dir_with_cover(self) -> None:
        cover_url = self.data[0].get("cover")
        cover_name = "cover.jpg"
        if not cover_url:
            Logger.warning("No cover found in JSON data.")
            return 

        filename = os.path.join(self.base_folder, cover_name)
        if os.path.exists(filename) and not self.force_download:
            return

        Logger.info("Downloading cover...")
        if not self.downloader.download_file(cover_url, self.base_folder, cover_name):
            Logger.error("Failed to download cover.")
            return 
        Logger.success("Cover downloaded successfully")

    def _download_chapter_images(
        self, folder: str, temp_folder: str, 
        images: List[str], count: int, entry: dict
    ) -> None:

        self.downloader.download_files(images, temp_folder, count)

        if self.stats_manager.all_images_downloaded:
            if Utility.rename(temp_folder, folder):
                self.stats_manager.update_chapter_stat(downloaded=True)
                if self.save_as_CBZ:
                    Utility.create_cbz(folder)
                if self.delete_on_success:
                    self.data.remove(entry)
                    Utility.save_data(self.json_file, self.data)
        else:
            self.stats_manager.update_chapter_stat(failure=True)

        self.stats_manager.all_images_downloaded = True

    def process_images(self) -> None:
        """Process and download images based on the data from the JSON file."""

        self._setup_manga_dir_with_cover()
        for count, entry in enumerate(self.data[:], start=1):
            if self._should_stop_processing():
                break

            images = entry.get("images", [])
            if not images:
                Logger.error("No images available to download.")
                continue

            title: str = entry.get("title", "UnknownChapter").translate(self.translation_table)
            folder = os.path.join(self.base_folder, title)
            temp_folder = os.path.join(self.base_folder, f"{title}_tamp")

            if Utility.is_downloaded_chapter(folder, temp_folder, images):
                self.stats_manager.update_chapter_stat(skipped=True)
                continue

            self._download_chapter_images(folder, temp_folder, images, count, entry)

        self.stats_manager.log_download_results()

    def start(self) -> None:
        self.process_images()
