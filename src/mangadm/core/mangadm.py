import json
from functools import cached_property
from pathlib import Path
from typing import Dict, List, Optional

from rich.console import Console, Group
from rich.live import Live

from mangadm.components.archiver import MangaArchiver
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
        self._json_file = value
        self.data = self._load_data()

    @property
    def data(self) -> dict:
        """Get manga data with validation."""
        if not self._data:
            raise ValueError("No manga data available")
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

    @property
    def dest_path(self):
        return self._dest_path

    @dest_path.setter
    def dest_path(self, value):
        if not isinstance(value, Path):
            value = Path(value)

        self._dest_path = value
        details = self.data.get("details", {})
        manga_name = details.get("manganame", "UnknownManga").translate(
            self.translation_table
        )
        source = details.get("source", "unknown")
        self.base_folder = self.dest_path / f"{manga_name} ({source})"
        self.base_folder.mkdir(parents=True, exist_ok=True)

    @property
    def chapters(self) -> list:
        """Get chapters list with validation."""
        return self.data.get("chapters", [])

    @cached_property
    def details(self) -> Dict:
        """Get details."""
        return self.data.get("details", {})

    def _should_stop_processing(self) -> bool:
        """Check if processing should stop based on limit."""
        return self.limit > 0 and (self.failed_count + self.success_count) >= self.limit

    def _is_downloaded_chapter(
        self,
        folder: Path,
        temp_folder: Path,
        images: List[str],
    ) -> bool:
        """Check if a chapter is already downloaded using only Path operations and multiple archive extensions."""
        # Check if any archive with supported extensions exists
        for ext in [f.value for f in FormatType]:
            archive_file = folder.with_name(f"{folder.name}.{ext}")
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

        return len(images) == len(files)

    def _load_data(self) -> dict:
        """Load JSON data from file."""
        try:
            with open(self.json_file, "r", encoding="utf-8") as f:
                return json.load(f)
        except (json.JSONDecodeError, IOError) as e:
            self.console.log(f"Error loading JSON data: {e}")
            return {"details": {}, "chapters": []}

    def _save_data(self, file_path: Path, data: Dict) -> bool:
        """Save current data back to JSON file."""
        try:
            with open(file_path, "w", encoding="utf-8") as f:
                json.dump(data, f, ensure_ascii=False, indent=4)
            return True
        except (IOError, OSError) as e:
            self.console.log(f"Error saving data: {e}")
            return False

    def create_temp_folder(self, chapter_name: str) -> Path:
        """Create temporary folder for chapter downloads."""
        temp_path = self.base_folder / f"{chapter_name}_tmp"
        temp_path.mkdir(exist_ok=True)
        return temp_path

    def _rename(self, temp_path: Path, final_path: Path) -> bool:
        """Rename temporary folder to final chapter name."""
        try:
            if final_path.exists():
                self.console.log(f"Path already exists: {final_path}")
                return False
            temp_path.rename(final_path)
            return True
        except Exception as e:
            self.console.log(f"Error renaming folder: {e}")
            return False

    def _remove_chapter(self, chapter_data: dict) -> bool:
        """Remove chapter from data and save."""
        try:
            self.data["chapters"].remove(chapter_data)
            return self._save_data(self.json_file, self.data)
        except ValueError as e:
            self.console.log(f"Error removing chapter: {e}")
            return False

    def _setup_manga_metadata(self) -> None:
        """Setup manga details and cover image."""
        details_path = self.base_folder / "details.json"
        details = self.details
        if not details_path.exists() or self.update_details:
            sanitized_details = {
                "title": details.get("manganame", "UnknownManga"),
                "author": details.get("author"),
                "artist": details.get("artist"),
                "description": details.get("description"),
                "genre": details.get("genre", []),
            }
            self._save_data(details_path, sanitized_details)
        self._download_cover_image()

    def _download_cover_image(self) -> None:
        """Download manga cover image if needed."""
        cover_url = self.details.get("cover")
        if not cover_url:
            return

        cover_path = self.base_folder / f"cover{Path(cover_url).suffix}"
        if not cover_path.exists() or self.update_details:
            self.loader.one(cover_url, Path(cover_path.name))

    def _process_chapters(self) -> None:
        """Process all chapters in the manga data."""

        chapters = self.chapters[:]
        total_chapters = len(chapters)
        for idx, chapter in enumerate(chapters, 1):
            if self._should_stop_processing():
                break
            self._process_chapter(chapter, idx, total_chapters)

    def _process_chapter(
        self, chapter: dict, current_idx: int, total_chapters: int
    ) -> None:
        """Process a single manga chapter."""
        title = chapter.get("title", "UnknownChapter").translate(self.translation_table)
        images = chapter.get("images", [])

        if not images:
            self.console.log(f"Chapter [green]{title}[/] has no images.")
            return

        final_path = self.base_folder / title
        temp_path = self.create_temp_folder(title)

        if self._is_downloaded_chapter(final_path, temp_path, images):
            self._results.append(DownloadResult(DownloadStatus.SKIPPED, final_path))
            return

        self.loader.totel = (total_chapters, self.skipped_count, current_idx)
        self.loader.save_dir = temp_path
        self.loader.urls = images
        self.loader.all()

        if self.loader.all_success:
            self.loader.clear_results()
            self._results.append(
                DownloadResult(DownloadStatus.SUCCESS, self.loader.save_dir)
            )
            if self._rename(temp_path, final_path):
                self.archiver.create_archiver(final_path, self.format)
                if self.delete_on_success:
                    self._remove_chapter(chapter)
        else:
            self._results.append(
                DownloadResult(DownloadStatus.FAILED, self.loader.save_dir)
            )
        self.loader.spinner.remove_task(self.loader.spinner_task)

    def start(self) -> None:
        """Start download process"""
        with Live(
            Group(self.loader.spinner, self.loader.progress),
            console=self.console,
        ):
            self._setup_manga_metadata()
            self._process_chapters()
