import os
import json
import shutil
import zipfile 
import time 
import signal
import sys
import requests
from pathlib import Path
from typing import Any, Dict, List, Optional
from urllib.parse import urlparse, unquote
from rich.progress import (
    Progress,
    BarColumn,
    DownloadColumn,
    TimeRemainingColumn,
    TransferSpeedColumn,
    ProgressColumn,
)
    # TimeElapsedColumn
    # TaskProgressColumn
from rich.text import Text
from rich.console import Console
from rich.table import Table

from mangadm.utils import Logger

console = Console() 

class CustomProgressColumn(ProgressColumn):
    def __init__(
        self, total_chapters: Optional[int] = None, total_img: Optional[int] = None,
    ):
        super().__init__()
        self.total_chapters = total_chapters
        self.total_img = total_img

        self._show_percentage = False
        self._last_update_time = time.time()
        self._update_interval = 3.0  # Interval in seconds

    def render(self, task) -> str:

        if not self.total_chapters or not self.total_img:
            return ""
            
        count_chapters = task.fields.get("count_chapters", 0)
        completed_imgs = task.fields.get("completed_imgs", 0)

        percentage_complete_img = (completed_imgs / self.total_img) * 100
        percentage_complete_chapter = (count_chapters / self.total_chapters) * 100
        
        img_color = (
            "green" if percentage_complete_img >= 75
            else "yellow" if percentage_complete_img >= 50
            else "red"
        )

        # Update the display toggle based on elapsed time
        if self._should_update_display():
            self._show_percentage = not self._show_percentage

        # Determine what to display based on the current state
        if self._show_percentage:
            img_progress = f"[{img_color}]{percentage_complete_img:.0f}%[/]"
            chapter_progress = f"[blue]{percentage_complete_chapter:.0f}%[/]"
        else:
            img_progress = f"[{img_color}]{completed_imgs}/{self.total_img}[/]"
            chapter_progress = f"[blue]{count_chapters}/{self.total_chapters}[/]"

        return f"{chapter_progress} {img_progress}"

    def _should_update_display(self) -> bool:
        current_time = time.time()
        if (current_time - self._last_update_time) >= self._update_interval:
            self._last_update_time = current_time
            return True
        return False

class CustomPercentageColumn(ProgressColumn):
    def render(self, task):
        percentage = task.percentage
        
        if task.total is None or percentage is None:
            return self.format_text("", "white")

        color = self.get_color_for_percentage(percentage)
        return self.format_text(f"{percentage:.1f}%", color)

    def get_color_for_percentage(self, percentage):
        if percentage >= 75:
            return "blue"
        elif percentage >= 50:
            return "magenta"
        return "cyan"

    def format_text(self, text, color):
        rich_text = Text(text, style=color)
        return rich_text

class Utility:

    @staticmethod
    def get_size(local_filename: str) -> int:
        """Get the size of a file if it exists, otherwise return 0."""
        return os.path.getsize(local_filename) if os.path.exists(local_filename) else 0

    @staticmethod
    def create_custom_progress_bar(
        total_img: Optional[int] = None, total_chapters: Optional[int] = None, transient: bool = True 
    ) -> Progress:
        """Create a custom progress bar with optional image and chapter totals."""
        return Progress(
            "[bold cyan]●[/]",
            CustomPercentageColumn(),
            BarColumn(),
            CustomProgressColumn(total_chapters, total_img),
            DownloadColumn(),
            TransferSpeedColumn(),
            TimeRemainingColumn(),
            console=console,
            transient=transient 
        )

    @staticmethod
    def get_filename_from_url(url: str) -> str:
        """Extract and decode the filename from a given URL."""
        return unquote(os.path.basename(urlparse(url).path))

    @staticmethod
    def load_data(file_path: str) -> List[Dict[str, Any]]:
        """Load JSON data from a file."""
        if not os.path.exists(file_path):
            Logger.error(f"File {file_path} does not exist.")
            return []
        try:
            with open(file_path, "r", encoding="utf-8") as file:
                return json.load(file)
        except (json.JSONDecodeError, IOError) as e:
            Logger.error(f"Failed to load data from JSON file {file_path}: {e}")
            return []
        
    @staticmethod
    def is_downloaded_chapter(folder: str, temp_folder: str, images: List[str]) -> bool:
        """Check if a chapter is already downloaded."""
        folder_name = os.path.basename(folder.rstrip("/\\"))
        cbz_file = os.path.join(os.path.dirname(folder), f"{folder_name}.cbz")
        
        # Check if .cbz file exists
        if os.path.isfile(cbz_file):
            return True

        # Check if the temporary folder exists
        if os.path.isdir(temp_folder):
            return False

        folder_exists = os.path.isdir(folder)
        files = os.listdir(folder) if folder_exists else []
        has_temp = any("_temp" in file for file in files)

        # Check if has _temp in files
        if folder_exists and has_temp:
            return False

        # Check if the number of images matches the files in the folder
        if folder_exists and len(images) == len(files):
            return True 

    @staticmethod
    def create_cbz(folder_path: str) -> None:
        """Create a CBZ (Comic Book ZIP) file from a folder and delete the original folder."""
        folder_name = os.path.basename(folder_path.rstrip("/\\"))
        cbz_file = os.path.join(os.path.dirname(folder_path), f"{folder_name}.cbz")
    
        try:
            with zipfile.ZipFile(cbz_file, "w", zipfile.ZIP_DEFLATED) as cbz:
                for root, _, files in os.walk(folder_path):
                    for file in sorted(files):
                        file_path = os.path.join(root, file)
                        cbz.write(file_path, os.path.relpath(file_path, folder_path))
            shutil.rmtree(folder_path)
        except (IOError, OSError) as e:
            Logger.error(f"Error creating `{folder_name}.cbz`: {e}")

    @staticmethod
    def save_data(file_path: str, data: List[Dict[str, Any]]) -> None:
        """Save data to a JSON file."""
        try:
            with open(file_path, "w", encoding="utf-8") as file:
                json.dump(data, file, ensure_ascii=False, indent=4)
        except (IOError, OSError) as e:
            Logger.error(f"Failed to save data to JSON file {file_path}: {e}")

    @staticmethod
    def rename(temp_folder, folder):
        try:
            temp_path = Path(temp_folder)
            folder_path = Path(folder)

            if folder_path.exists():
                Logger.warning(f"'{temp_folder}' and '{folder}' are considered the same on this file system (case-insensitive).", enhanced=True)
                return False

            temp_path.rename(folder_path)
            return True

        except FileExistsError:
            msg = f"A file or folder named '{folder}' already exists."
        except PermissionError:
            msg = f"Permission denied. Cannot rename '{temp_folder}' to '{folder}'."
        except OSError as e:
            msg = f"OS error occurred: {e.strerror} (Error code: {e.errno})"
        except Exception as e:
            msg = f"An unexpected error occurred: {str(e)}"

        Logger.warning("Failed to rename temp file or folder:")
        Logger.error(msg, count=False)
        return False

class CliUtility:

    @staticmethod
    def get_config_path() -> str:
        """Get the configuration file path, supporting both Linux and Windows."""
        config_dir = os.path.join(os.getenv("APPDATA") or os.path.expanduser("~/.config"), "manga_dm")

        if not os.path.exists(config_dir):
            os.makedirs(config_dir)

        return os.path.join(config_dir, "config.json")
        
    @staticmethod
    def load_stored_settings() -> Dict[str, Any]:
        """Load stored settings from the configuration file."""
        config_path = CliUtility.get_config_path()

        if not os.path.exists(config_path):
            return {}
        
        try:
            with open(config_path, "r", encoding="utf-8") as config_file:
                return json.load(config_file)
        except (IOError, json.JSONDecodeError) as e:
            Logger.error(f"Failed to load config from {config_path}: {e}")
            return {}

    @staticmethod
    def save_stored_settings(settings: Dict[str, Any]) -> None:
        """Save settings to the configuration file."""
        config_path = CliUtility.get_config_path()

        try:
            with open(config_path, "w", encoding="utf-8") as config_file:
                json.dump(settings, config_file, ensure_ascii=False, indent=4)
        except (IOError, OSError) as e:
            Logger.error(f"Failed to save config to {config_path}: {e}")


    @staticmethod
    def display_example_json():
        """Display an example JSON structure."""
        example_json = [
            {
                "manganame": "Jujutsu Kaisen",
                "cover": "https://example.com/cover.jpg",
                "title": "Jujutsu Kaisen - 256",
                "images": [
                    "https://example.com/image1.jpg",
                    "https://example.com/image2.jpg",
                    "https://example.com/image3.jpg",
                ],
            },
            {
                "manganame": "Boruto",
                "cover": "https://example.com/cover.jpg",
                "title": "Boruto - 7",
                "images": [
                    "https://example.com/image1.jpg",
                    "https://example.com/image2.jpg",
                    "https://example.com/image3.jpg",
                ],
            },
        ]
        console.print_json(json.dumps(example_json))
    
    @staticmethod
    def settings_ui():
        """Display a text UI for configuring settings."""
        default_settings = CliUtility.load_stored_settings()
    
        settings_questions = [
            {
                "type": "input",
                "name": "dest",
                "message": "Destination path for downloading manga chapters:",
                "default": str(default_settings.get("dest", ".")),
            },
            {
                "type": "input",
                "name": "limit",
                "message": "Number of chapters to download (enter -1 to download all chapters):",
                "default": str(default_settings.get("limit", -1)),
                "validate": lambda result: result.isdigit() or (result == "-1") or "Please enter a valid number (-1 or a positive integer)",
                "filter": lambda result: int(result) if result.isdigit() or result == "-1" else -1,
            },
        ]
    
        flags_questions = [
            {
                "type": "confirm",
                "name": "force",
                "message": "Re-download files even if not complete?",
                "default": default_settings.get("force", False),
            },
            {
                "type": "confirm",
                "name": "delete",
                "message": "Delete chapter data from JSON after successful download?",
                "default": default_settings.get("delete", False),
            },
            {
                "type": "confirm",
                "name": "cbz",
                "message": "Save the chapter as CBZ?",
                "default": default_settings.get("cbz", False),
            },
            {
                "type": "confirm",
                "name": "transient",
                "message": "Activate transient mode (will disappear after completion)?",
                "default": default_settings.get("transient", False),
            },
            {
                "type": "confirm",
                "name": "save_defaults",
                "message": "Would you like to save these settings as the new default?",
                "default": False,
            }
        ]
    
        # Prompt for settings and flags
        from InquirerPy import prompt
        settings_answers = prompt(settings_questions)
        flags_answers = prompt(flags_questions)
    
        # Combine answers
        combined_answers = {**settings_answers, **flags_answers}
    
        # Save defaults if requested
        if combined_answers.get("save_defaults"):
            return combined_answers
        else:
            console.print("Settings were not saved as default.")


class StatsManager:
    """Manages the statistics for downloads and chapters."""

    def __init__(self) -> None:
        self.success_count = 0
        self.failure_count = 0
        self.skipped_count = 0
        
        self.chapters_downloaded = 0
        self.failure_count_chapter = 0
        self.skipped_chapters = 0

        self.total_chapters = 0
        self.all_images_downloaded = True
        self.print_skip_msg = True

    def update_stat(self, success: bool = None, failure: bool = None, skipped: bool = None) -> None:
        if success:
            self.success_count += 1
        if failure:
            self.failure_count += 1
        if skipped:
            self.skipped_count += 1

    def update_chapter_stat(self, downloaded: bool = False, failure: bool = None, skipped: bool = False) -> None:
        if downloaded:
            self.chapters_downloaded += 1
        if failure:
            self.failure_count_chapter += 1
        if skipped:
            self.skipped_chapters += 1

    def set_total_chapters(self, total_chapters) -> None:
        self.total_chapters = total_chapters

    def skip_msg(self) -> None:
        messages = []

        if self.skipped_chapters > 0:
            if self.skipped_chapters == 1:
                messages.append("Skipped downloading 1 chapter.")
            else:
                messages.append(
                    f"Skipped downloading {self.skipped_chapters} chapters."
                )

        if self.skipped_count > 0:
            if self.skipped_count == 1:
                messages.append("Skipped downloading 1 image.")
            else:
                messages.append(f"Skipped downloading {self.skipped_count} images.")

        if messages and self.print_skip_msg:
            Logger.info(" | ".join(messages))


    def chapter_remaining(self):
        return self.total_chapters - (self.chapters_downloaded + self.skipped_chapters)

    def log_download_results(self) -> None:
        # Handling image download results
        image_success_message = (
            "No images were successfully downloaded."
            if self.success_count == 0
            else (
                "Successfully downloaded 1 image."
                if self.success_count == 1
                else f"Successfully downloaded {self.success_count} images."
            )
        )

        image_failure_message = (
            "No images failed to download."
            if self.failure_count == 0
            else (
                "Failed to download 1 image."
                if self.failure_count == 1
                else f"Failed to download {self.failure_count} images."
            )
        )

        image_skipped_message = (
            "No images were skipped."
            if self.skipped_count == 0
            else (
                "Skipped downloading 1 image."
                if self.skipped_count == 1
                else f"Skipped downloading {self.skipped_count} images."
            )
        )

        # Handling chapter download results
        chapter_total_message = f"Total chapters: {self.total_chapters}"
        chapter_remaining_message = f"Remaining chapters: {self.chapter_remaining()}"

        completed_chapters_message = (
            "No chapters were fully downloaded."
            if self.chapters_downloaded == 0
            else (
                "Completely downloaded 1 chapter."
                if self.chapters_downloaded == 1
                else f"Completely downloaded {self.chapters_downloaded} chapters."
            )
        )

        incomplete_chapters_message = (
            "No chapters were not fully downloaded."
            if self.failure_count_chapter == 0
            else (
                "Not fully downloaded 1 chapter."
                if self.failure_count_chapter == 1
                else f"Not fully downloaded {self.failure_count_chapter} chapters."
            )
        )
        
        skipped_chapters_message = (
            "No chapters were skipped."
            if self.skipped_chapters == 0
            else (
                "Skipped downloading 1 chapter."
                if self.skipped_chapters == 1
                else f"Skipped downloading {self.skipped_chapters} chapters."
            )
        )

        # Create a table
        table = Table(show_header=False)

        # Add rows to the table
        table.add_row(f"[green]{image_success_message}[/green]")
        table.add_row(f"[red]{image_failure_message}[/red]")
        table.add_row(f"[yellow]{image_skipped_message}[/yellow]")
        table.add_row(f"[cyan]{chapter_total_message}[/cyan]")
        table.add_row(f"[green]{completed_chapters_message}[/green]")
        table.add_row(f"[red]{incomplete_chapters_message}[/red]")
        table.add_row(f"[yellow]{skipped_chapters_message}[/yellow]")
        table.add_row(f"[cyan]{chapter_remaining_message}[/cyan]")

        # Print the table
        console.print(table)

    def get_statistics(self) -> dict:
        return {
            "success": self.success_count,
            "failure": self.failure_count,
            "skipped": self.skipped_count,
            "total_chapters": self.total_chapters,
            "chapters_downloaded": self.chapters_downloaded,
            "failure_chapter": self.failure_count_chapter,
            "skipped_chapters": self.skipped_chapters,
            "chapter_remaining": self.chapter_remaining(),
        }

class SignalHandler:
    _session = None
    _json_file = ""
    _data = []
    _progress = None
    _message = ""
    _stats_manager = None

    @classmethod
    def initialize(
        cls,
        session: Optional[requests.Session],
        json_file: str,
        data: list,
        progress: Optional[Progress],
        stats_manager: Optional[StatsManager],
    ) -> None:
        """Initialize the SignalHandler with necessary resources."""
        cls._session = session
        cls._json_file = json_file
        cls._data = data
        cls._progress = progress
        cls._stats_manager = stats_manager

        # Register signal handlers
        signal.signal(signal.SIGINT, cls.signal_handler)
        signal.signal(signal.SIGTERM, cls.signal_handler)
        signal.signal(signal.SIGTERM, cls.custom_signal_handler)

    @classmethod
    def signal_handler(cls, sig: int, frame: Optional[Any]) -> None:
        cls.clean_up_and_exit(results=True)

    @classmethod
    def custom_signal_handler(cls, sig: int, frame: Optional[Any]) -> None:
        cls.clean_up_and_exit()

    @classmethod
    def clean_up_and_exit(cls, results: bool = False) -> None:
        if cls._progress:
            cls._progress.stop()
        if cls._session:
            cls._session.close()
        Utility.save_data(cls._json_file, cls._data)
        if results:
            Logger.warning("Shutting down gracefully...")
        
        cls._stats_manager.log_download_results()
        sys.exit(0)

    @classmethod
    def update_progress(cls, progress: Optional[Progress]) -> None:
        """Update the progress object."""
        cls._progress = progress

    @classmethod
    def update_session(cls, session: Optional[requests.Session]) -> None:
        """Update the session object."""
        cls._session = session

    @classmethod
    def update_data(cls, data: list, json_file: str) -> None:
        """Update data and json file path."""
        cls._data = data
        cls._json_file = json_file

    @classmethod
    def update_stats_manager(cls, stats_manager: Optional[StatsManager]) -> None:
        """Update the stats_manager object."""
        cls._stats_manager = stats_manager
