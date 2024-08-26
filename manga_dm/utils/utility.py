import json
from typing import Any, Dict, List, Optional
import os
import zipfile
from urllib.parse import urlparse, unquote
from .logger import Logger
import platform
import shutil
from rich.progress import (
    Progress,
    BarColumn,
    DownloadColumn,
    TimeRemainingColumn,
    TransferSpeedColumn,
    ProgressColumn,
)
from rich.console import Console


class CustomProgressColumn(ProgressColumn):
    def __init__(
        self, total_chapters: Optional[int] = None, total_img: Optional[int] = None
    ):
        super().__init__()
        self.total_chapters = total_chapters
        self.total_img = total_img

    def render(self, task) -> str:

        count_chapters = task.fields.get("count_chapters", 0)
        completed_imgs = task.fields.get("completed_imgs", 0)

        total_chapters = self.total_chapters
        total_img = self.total_img

        if total_chapters and total_img:
            percentage_complete = (completed_imgs / total_img) * 100 if total_img else 0

            img_color = (
                "bold green"
                if percentage_complete >= 75
                else "bold yellow" if percentage_complete >= 50 else "bold red"
            )
            chapter_color = "cyan"

            return (
                f"[{chapter_color}]{count_chapters}/{total_chapters}[/] "
                f"[{img_color}]{completed_imgs}/{total_img}[/]"
            )


class CustomPercentageColumn(ProgressColumn):
    def render(self, task):
        percentage = task.percentage
        color = (
            "bold green"
            if percentage >= 75
            else "bold yellow" if percentage >= 50 else "bold red"
        )
        return f"[{color}]{percentage:.1f}%[/]"


class Utility:

    @staticmethod
    def get_size(local_filename):
        if os.path.exists(local_filename):
            return os.path.getsize(local_filename)
        else:
            return 0

    @staticmethod
    def create_custom_progress_bar(
        total_img: Optional[int] = None, total_chapters: Optional[int] = None
    ) -> Progress:
        console = Console()
        return Progress(
            "[bold cyan]●[/]",
            CustomPercentageColumn(),
            BarColumn(),
            CustomProgressColumn(total_chapters, total_img),
            DownloadColumn(),
            TransferSpeedColumn(),
            TimeRemainingColumn(),
            console=console,
        )

    @staticmethod
    def get_filename_from_url(url: str):
        parsed_url = urlparse(url)
        filename = os.path.basename(parsed_url.path)
        return unquote(filename)

    @staticmethod
    def load_data(file_path: str) -> List[Dict[str, Any]]:
        try:
            with open(file_path, "r", encoding="utf-8") as file:
                return json.load(file)
        except Exception as e:
            Logger.error(f"Failed to load data from JSON file {file_path}: {e}")
            return []

    @staticmethod
    def isdownloaded_chapter(folder: str, temp_folder: str, images: list) -> bool:
        """Check if chapter downloaded"""
        folder_name = os.path.basename(folder.rstrip("/\\"))
        cbz_file = os.path.join(os.path.dirname(folder), f"{folder_name}.cbz")
        

        if not os.path.isdir(temp_folder):
            if os.path.isfile(cbz_file) or (
                os.path.isdir(folder) and len(images) == len(os.listdir(folder))
            ):
                return True

        return False

    @staticmethod
    def create_cbz(folder_path: str):
        folder_name = os.path.basename(folder_path.rstrip("/\\"))
        cbz_file = os.path.join(os.path.dirname(folder_path), f"{folder_name}.cbz")
    
        with zipfile.ZipFile(cbz_file, "w") as cbz:
            for root, _, files in os.walk(folder_path):
                for file in sorted(files):
                    file_path = os.path.join(root, file)
                    cbz.write(file_path, os.path.relpath(file_path, folder_path))

        try:
            shutil.rmtree(folder_path)
        except Exception as e:
            Logger.error(f"Error `{folder_name}.cbz`: {e}")

    @staticmethod
    def save_data(file_path: str, data: List[Dict[str, Any]]) -> None:
        try:
            with open(file_path, "w", encoding="utf-8") as file:
                json.dump(data, file, ensure_ascii=False, indent=4)
        except Exception as e:
            Logger.error(f"Failed to save data to JSON file {file_path}: {e}")

    @staticmethod
    def get_config_path():
        """Get the path to the configuration file, supports both Linux and Windows."""
        if platform.system() == "Windows":
            config_dir = os.path.join(os.getenv("APPDATA"), "manga_dm")
        else:
            config_dir = os.path.expanduser("~/.config/manga_dm")

        if not os.path.exists(config_dir):
            os.makedirs(config_dir)

        return os.path.join(config_dir, "config.json")

    @staticmethod
    def load_default_settings():
        """Load default settings from the config file."""
        config_path = Utility.get_config_path()
        if os.path.exists(config_path):
            with open(config_path, "r") as config_file:
                return json.load(config_file)
        return {}

    @staticmethod
    def save_default_settings(settings):
        """Save default settings to the config file."""
        config_path = Utility.get_config_path()
        try:
            with open(config_path, "w", encoding="utf-8") as config_file:
                json.dump(settings, config_file, ensure_ascii=False, indent=4)
        except Exception as e:
            Logger.error(f"Failed to save config to JSON file {config_path}: {e}")
