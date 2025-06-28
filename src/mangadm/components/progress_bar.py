from typing import Optional 
import time  

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
from rich.table import Table
from rich.console import Console

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
 