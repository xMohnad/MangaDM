import json
from typing import Any, Dict, List, Optional
import os
from urllib.parse import urlparse, unquote
from .logger import Logger
import glob

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
    def check_if_chapters_downloaded(folder: str, images: list) -> None:
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
                return True
        return False

    @staticmethod
    def save_data(file_path: str, data: List[Dict[str, Any]]) -> None:
        try:
            with open(file_path, "w", encoding="utf-8") as file:
                json.dump(data, file, ensure_ascii=False, indent=4)
        except Exception as e:
            Logger.error(f"Failed to save data to JSON file {file_path}: {e}")
