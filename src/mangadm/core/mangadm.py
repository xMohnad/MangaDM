import json
from pathlib import Path
from typing import Any, Dict, List, Optional, Union

from rich.console import Console, Group
from rich.live import Live

from mangadm.components import MangaArchiver
from mangadm.components.base_component import BaseComponent
from mangadm.components.types import DownloadResult, DownloadStatus, FormatType, Status
from mangadm.core.slide_loader import SlideLoader


class MangaDM(BaseComponent, Status):
    """Manages the downloading of manga chapters from a JSON file."""

    # fmt: off
    # Prepare translation table for sanitizing folder and file names
    translation_table = str.maketrans({
        "/": "_", "\\": "_", "\"": "_", "'": "_", "?": "", "*": " ", "%": " ", 
        "$": "_", "#": "_", "@": "_", "~": "_", "}": "-", "{": "-", "|": "_", 
        ":": "_", "+": "_", "=": "_", "[": "-", "]": "-", "&": " - "
    })
    # fmt: on

    def __init__(
        self,
        json_file: Path,
        dest_path: Path = Path("."),
        limit: int = -1,
        delete_on_success: bool = False,
        update_details: bool = False,
        format: FormatType = FormatType.cbz,
        console: Optional[Console] = None,
    ) -> None:
        super().__init__(console)
        self.json_file = json_file
        self.dest_path = dest_path
        self.limit = limit
        self.delete_on_success = delete_on_success
        self.update_details = update_details
        self.format = format

        self._results: List[DownloadResult] = []
        self.details = self.data.get("details", {})
        manga_name = self.details.get("manganame", "UnknownManga").translate(
            self.translation_table
        )
        source = self.details.get("source")
        self.base_folder = self.dest_path / f"{manga_name} ({source})"
        self.base_folder.mkdir(parents=True, exist_ok=True)

        self.loader = SlideLoader(console=self.console, save_dir=self.base_folder)
        self.archiver = MangaArchiver(self.console)

    @property
    def json_file(self):
        return self._json_file

    @json_file.setter
    def json_file(self, value):
        if not str(value).lower().endswith(".json"):
            raise ValueError(
                f"Unsupported file format: {value}. Please use JSON format."
            )
        if not isinstance(value, Path):
            value = Path(value)
        self.data = self._load_data(value)
        self._json_file = value

    @property
    def dest_path(self):
        return self._dest_path

    @dest_path.setter
    def dest_path(self, value):
        if not isinstance(value, Path):
            value = Path(value)
        value.mkdir(exist_ok=True, parents=True)
        self._dest_path = value

    @property
    def data(self):
        if not self._data:
            raise ValueError("No data available to process.")
        return self._data

    @data.setter
    def data(self, data):
        match data:
            case {"details": dict(), "chapters": list()}:
                self._data = data
            case _:
                raise ValueError(
                    "Invalid JSON structure. Expected format: "
                    "{ 'details': dict, 'chapters': list }"
                )

    def _should_stop_processing(self) -> bool:
        return (
            self.limit != -1 and (self.failed_count + self.success_count) >= self.limit
        )

    def is_downloaded_chapter(
        self,
        folder: Path,
        temp_folder: Path,
        images: List[str],
    ) -> bool:
        """Check if a chapter is already downloaded using only Path operations and multiple archive extensions."""
        folder_name = folder.name

        # Check if any archive with supported extensions exists
        for ext in [f.value for f in FormatType]:
            archive_file = folder.with_name(f"{folder_name}.{ext}")
            if archive_file.is_file():
                return True

        # Check if the temporary folder exists
        if temp_folder.is_dir():
            return False

        if not folder.is_dir():
            return False

        files = list(folder.iterdir())
        if any(self.loader.temp_ext in file.name for file in files):
            return False

        if len(images) == len(files):
            return True

        return False

    def _rename(self, temp_path: Path, folder_path: Path):
        try:
            if folder_path.exists():
                self.console.log(
                    f"'{str(temp_path)}' and '{str(folder_path)}' are considered the same on this file system (case-insensitive)."
                )
                return False
            temp_path.rename(folder_path)
            return True
        except Exception:
            return False

    def _load_data(self, file_path: Path) -> List[Dict[str, Any]]:
        """Load JSON data from a file."""
        if not file_path.exists():
            return []
        try:
            with open(file_path, "r", encoding="utf-8") as file:
                return json.load(file)
        except (json.JSONDecodeError, IOError):
            return []

    def _save_data(self, file_path: Union[str, Path], data: Dict[str, Any]) -> None:
        """Save data to a JSON file."""
        try:
            with open(file_path, "w", encoding="utf-8") as file:
                json.dump(data, file, ensure_ascii=False, indent=4)
        except (IOError, OSError):
            return

    def _setup_manga_dir(self) -> None:
        details_path = self.base_folder / "details.json"

        if not details_path.exists() and self.update_details:
            sanitized_details = {
                "title": self.details.get("manganame", "UnknownManga"),
                "author": self.details.get("author"),
                "artist": self.details.get("artist"),
                "description": self.details.get("description"),
                "genre": self.details.get("genre", []),
            }
            self._save_data(details_path, sanitized_details)

        cover_url = self.details.get("cover")
        if not cover_url:
            return  # No cover to process

        cover_filename = Path(f"cover{Path(cover_url).suffix}")
        cover_path = self.base_folder / cover_filename

        # Skip cover download if file already exists and update is disabled
        if cover_path.exists() and not self.update_details:
            return

        # Attempt to download the cover
        self.loader.one(cover_url, cover_filename)

    def _start(self) -> None:
        self._setup_manga_dir()
        self.chapters = self.data.get("chapters", [])

        for count, entry in enumerate(self.chapters[:], start=1):
            if self._should_stop_processing():
                break

            # Prepare paths
            title: str = entry.get("title", "UnknownChapter").translate(
                self.translation_table
            )
            folder = self.base_folder / title
            temp_folder = self.base_folder / f"{title}{self.loader.temp_ext}"

            images = entry.get("images", [])
            if not images:
                self.console.log(
                    f"Chapter [green]{title}[/] has no downloadable images."
                )
                continue

            # Skip if already downloaded
            if self.is_downloaded_chapter(folder, temp_folder, images):
                self._results.append(
                    DownloadResult(DownloadStatus.SKIPPED, self.loader.save_dir)
                )
                continue

            # Set up loader and start download
            self.loader.totel = (len(self.chapters), self.skipped_count, count)
            self.loader.save_dir = temp_folder
            self.loader.urls = images

            self.loader.all()

            if self.loader.all_success:
                self.loader.clear_results()
                self._results.append(
                    DownloadResult(DownloadStatus.SUCCESS, self.loader.save_dir)
                )

                if self._rename(temp_folder, folder):
                    self.archiver.create_archiver(folder, self.format)
                    if self.delete_on_success:
                        self.data["chapters"].remove(entry)
                        self._save_data(self.json_file, self.data)
            else:
                self._results.append(
                    DownloadResult(DownloadStatus.FAILED, self.loader.save_dir)
                )

        self.loader.spinner.remove_task(self.loader.spinner_task)

    def start(self) -> None:
        """Start download process"""
        with Live(
            Group(self.loader.spinner, self.loader.progress), console=self.console
        ):
            self._start()
