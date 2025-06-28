import sys
from typing import List, Literal
import requests
from pathlib import Path

from mangadm.core.downloader import Downloader
from mangadm.components import StatsManager, Logger, SignalHandler
from mangadm.utils import Utility


class MangaDM:
    """Manages the downloading of manga chapters from a JSON file."""

    def __init__(
        self,
        json_file: Path,
        dest_path: str = ".",
        limit: int = -1,
        force_download: bool = False,
        delete_on_success: bool = False,
        update_details: bool = False,
        format: Literal["cbz", "epub"] = "cbz",
        transient: bool = True,
    ) -> None:
        if not str(json_file).lower().endswith(".json"):
            Logger.error(
                f"Unsupported file format: {json_file}. Please use JSON format."
            )
            sys.exit(0)

        self.data = Utility.load_data(json_file)
        if not self.data:
            Logger.error("No data available to process.")
            sys.exit(0)

        if not self.__validate_json_structure(self.data):
            Logger.error("The JSON structure is invalid.")
            sys.exit(0)

        self.json_file = Path(json_file)
        self.dest_path = Path(dest_path)
        self.limit = limit
        self.force_download = force_download
        self.delete_on_success = delete_on_success
        self.update_details = update_details
        self.format = format
        self.transient = transient

        self.stats_manager = StatsManager()
        self.stats_manager.set_total_chapters(len(self.data.get("chapters", [])))
        self.session = requests.Session()

        # Initialize SignalHandler with necessary resources
        SignalHandler.initialize(
            self.session,
            self.json_file,
            self.data,
            None,
            self.stats_manager,
        )

        self.downloader = Downloader(
            stats_manager=self.stats_manager,
            force_download=self.force_download,
            transient=self.transient,
            session=self.session,
        )

        # fmt: off
        # Prepare translation table for sanitizing folder and file names
        self.translation_table = str.maketrans({
            "/": "_", "\\": "_", "\"": "_", "'": "_", "?": "", "*": " ", "%": " ", 
            "$": "_", "#": "_", "@": "_", "~": "_", "}": "-", "{": "-", "|": "_", 
            ":": "_", "+": "_", "=": "_", "[": "-", "]": "-", "&": " - "
        })
        # fmt: on

        self.base_folder = self.dest_path / "{} ({})".format(
            self.data.get("details", {})
            .get("manganame", "UnknownManga")
            .translate(self.translation_table),
            self.data.get("details", {}).get("source"),
        )
        self.base_folder.mkdir(parents=True, exist_ok=True)

    def __validate_json_structure(self, data):
        if isinstance(data, dict):
            if "details" in data and "chapters" in data:
                if isinstance(data["details"], dict) and isinstance(
                    data["chapters"], list
                ):
                    return True
        return False

    def _should_stop_processing(self) -> bool:
        return self.limit != -1 and self.stats_manager.chapters_downloaded >= self.limit

    def _add_details(self, details):
        details_path = self.base_folder / "details.json"

        if details_path.exists() and not self.update_details:
            return

        details = dict(
            title=details.get("manganame", "UnknownManga"),
            author=details.get("author", None),
            artist=details.get("artist", None),
            description=details.get("description", None),
            genre=details.get("genre", []),
        )

        Utility.save_data(details_path, details)

    def _setup_manga_dir(self) -> None:
        details = self.data.get("details", {})
        self._add_details(details)

        cover_url = details.get("cover")
        if not cover_url:
            Logger.warning("No cover found in JSON data.")
            return

        cover_name = f"cover.{Utility.get_ext_from_url(cover_url)}"
        filename = self.base_folder / cover_name

        if filename.exists() and not self.update_details:
            return

        Logger.info("Downloading cover...")
        if not self.downloader.download_file(cover_url, self.base_folder, cover_name):
            Logger.error("Failed to download cover.")
            return

        Logger.success("Cover downloaded successfully")

    def _download_chapter_images(
        self, folder: str, temp_folder: str, images: List[str], count: int, entry: dict
    ) -> None:

        self.downloader.download_files(images, temp_folder, count)

        if self.stats_manager.all_images_downloaded:
            if Utility.rename(temp_folder, folder):
                self.stats_manager.update_chapter_stat(downloaded=True)
                if self.format == "cbz":
                    Utility.create_cbz(folder)
                elif self.format == "epub":
                    Utility.create_epub(folder)
                if self.delete_on_success:
                    self.data["chapters"].remove(entry)
                    Utility.save_data(self.json_file, self.data)
        else:
            self.stats_manager.update_chapter_stat(failure=True)

        self.stats_manager.all_images_downloaded = True

    def start(self) -> None:
        """Process and download images based on the data from the JSON file."""

        self._setup_manga_dir()

        for count, entry in enumerate(self.data.get("chapters", [])[:], start=1):
            if self._should_stop_processing():
                break

            images = entry.get("images", [])
            if not images:
                Logger.error("No images available to download.")
                continue

            title: str = entry.get("title", "UnknownChapter").translate(
                self.translation_table
            )
            folder = self.base_folder / title
            temp_folder = self.base_folder / f"{title}_tmp"

            if Utility.is_downloaded_chapter(str(folder), str(temp_folder), images):
                self.stats_manager.update_chapter_stat(skipped=True)
                continue

            self._download_chapter_images(folder, temp_folder, images, count, entry)

        self.stats_manager.log_download_results()
