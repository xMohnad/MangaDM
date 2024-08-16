import json
from typing import Any, Dict, List, Optional
import os
from urllib.parse import urlparse, unquote
from .logger import Logger

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
    def save_data(file_path: str, data: List[Dict[str, Any]]) -> None:
        try:
            with open(file_path, "w", encoding="utf-8") as file:
                json.dump(data, file, ensure_ascii=False, indent=4)
        except Exception as e:
            Logger.error(f"Failed to save data to JSON file {file_path}: {e}")


class StatsManager:
    """Manages the statistics for downloads and chapters."""

    def __init__(self) -> None:
        self.success_count = 0
        self.failure_count = 0
        self.skipped_count = 0
        self.chapters_downloaded = 0
        self.skipped_chapters = 0
        self.total_chapters = 0
        self.all_images_downloaded = True

        self.print_skip_msg = True

    def update_success(self) -> None:
        self.success_count += 1

    def update_failure(self) -> None:
        self.failure_count += 1

    def update_skipped(self) -> None:
        self.skipped_count += 1

    def update_chapters_downloaded(self) -> None:
        self.chapters_downloaded += 1

    def update_skipped_chapters(self) -> None:
        self.skipped_chapters += 1

    def set_total_chapters(self, total_chapters) -> None:
        self.total_chapters = total_chapters

    def skip_msg(self) -> None:

        messages = []

        if self.skipped_count > 0:
            if self.skipped_count == 1:
                messages.append("Skipped downloading 1 image.")
            else:
                messages.append(f"Skipped downloading {self.skipped_count} images.")

        if self.skipped_chapters > 0:
            if self.skipped_chapters == 1:
                messages.append("Skipped downloading 1 chapter.")
            else:
                messages.append(
                    f"Skipped downloading {self.skipped_chapters} chapters."
                )

        if messages and self.print_skip_msg:
            Logger.warning(" | ".join(messages))

    def log_download_results(self) -> None:
        # Handling image download results
        image_success_message = (
            "No images were successfully downloaded."
            if self.success_count == 0
            else (
                f"Successfully downloaded 1 image."
                if self.success_count == 1
                else f"Successfully downloaded {self.success_count} images."
            )
        )

        image_failure_message = (
            "No images failed to download."
            if self.failure_count == 0
            else (
                f"Failed to download 1 image."
                if self.failure_count == 1
                else f"Failed to download {self.failure_count} images."
            )
        )

        image_skipped_message = (
            "No images were skipped."
            if self.skipped_count == 0
            else (
                f"Skipped downloading 1 image."
                if self.skipped_count == 1
                else f"Skipped downloading {self.skipped_count} images."
            )
        )

        # Handling chapter download results
        chapter_total_message = f"Total chapters: {self.total_chapters}"

        chapter_downloaded_message = (
            "No chapters were fully downloaded."
            if self.chapters_downloaded == 0
            else (
                f"Completely downloaded 1 chapter."
                if self.chapters_downloaded == 1
                else f"Completely downloaded {self.chapters_downloaded} chapters."
            )
        )

        chapter_skipped_message = (
            "No chapters were skipped."
            if self.skipped_chapters == 0
            else (
                f"Skipped downloading 1 chapter."
                if self.skipped_chapters == 1
                else f"Skipped downloading {self.skipped_chapters} chapters."
            )
        )

        # Printing the formatted result
        message = (
            f"{image_success_message}\n{image_failure_message}\n{image_skipped_message}\n"
            f"{chapter_total_message}\n{chapter_downloaded_message}\n{chapter_skipped_message}\n"
        )
        Logger.info(message)

    def get_statistics(self) -> dict:
        return {
            "success": self.success_count,
            "failure": self.failure_count,
            "skipped": self.skipped_count,
            "total_chapters": self.total_chapters,
            "chapters_downloaded": self.chapters_downloaded,
            "skipped_chapters": self.skipped_chapters,
        }
