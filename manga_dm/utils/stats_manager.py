from manga_dm.utils import Logger

from rich.console import Console
from rich.table import Table

console = Console()


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

        self.failure_count_chapter = 0

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

    def update_failure_chapter(self) -> None:
        self.failure_count_chapter += 1

    def reset_failure_chapter(self) -> None:
        self.failure_count_chapter = 0

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

        chapter_downloaded_message = (
            "No chapters were fully downloaded."
            if self.chapters_downloaded == 0
            else (
                "Completely downloaded 1 chapter."
                if self.chapters_downloaded == 1
                else f"Completely downloaded {self.chapters_downloaded} chapters."
            )
        )

        chapter_skipped_message = (
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
        table.add_row(f"[green]{chapter_downloaded_message}[/green]")
        table.add_row(f"[yellow]{chapter_skipped_message}[/yellow]")

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
        }
