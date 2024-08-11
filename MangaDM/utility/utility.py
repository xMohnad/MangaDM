import json
from typing import Any, Dict, List
from rich.progress import (
    Progress,
    BarColumn,
    DownloadColumn,
    TimeRemainingColumn,
    TransferSpeedColumn,
    ProgressColumn,
)
import os
from urllib.parse import urlparse, unquote

from .logger import Logger


class PercentageColumn(ProgressColumn):
    def render(self, task):
        percentage = task.percentage
        if percentage >= 75:
            color = "green"
        elif percentage >= 50:
            color = "yellow"
        else:
            color = "red"
        return f"[{color}]{percentage:.1f}%[/]"


class FileCountColumn(ProgressColumn):
    def __init__(self, total_files=None):
        self.total_files = total_files
        super().__init__()

    def render(self, task):
        completed_count = task.fields.get("completed_count", 0)
        total_files = self.total_files

        if total_files:
            if total_files and int(completed_count) >= total_files:
                color = "bold green"
            elif total_files:
                percentage_complete = (int(completed_count) / total_files) * 100
                if percentage_complete >= 75:
                    color = "bold cyan"
                elif percentage_complete >= 50:
                    color = "bold blue"
                else:
                    color = "bold magenta"
            else:
                color = "bold red"

            return f"[{color}]{completed_count}/{total_files}[/]"


class Utility:

    @staticmethod
    def get_size(local_filename):
        if os.path.exists(local_filename):
            return os.path.getsize(local_filename)
        else:
            return 0

    @staticmethod
    def create_bar(total_files=None, transient=False) -> Progress:
        return Progress(
            "[bold cyan] ●",
            PercentageColumn(),
            BarColumn(),
            (
                FileCountColumn(total_files=total_files)
                if total_files is not None
                else FileCountColumn()
            ),
            DownloadColumn(),
            TransferSpeedColumn(),
            TimeRemainingColumn(),
            transient=transient,
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
