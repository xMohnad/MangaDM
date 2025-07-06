from dataclasses import dataclass
from enum import Enum, auto
from pathlib import Path
from typing import List, Optional


class FormatType(str, Enum):
    cbz = "cbz"
    epub = "epub"


class DownloadStatus(Enum):
    SUCCESS = auto()
    FAILED = auto()
    SKIPPED = auto()
    REPLACED = auto()


@dataclass
class DownloadResult:
    status: DownloadStatus
    path: Optional[Path] = None
    error: Optional[BaseException] = None
    url: Optional[str] = None


class Status:
    def __init__(self) -> None:
        self._results: List[DownloadResult] = []

    @property
    def results(self) -> List[DownloadResult]:
        """Get the download results."""
        return self._results

    def clear_results(self):
        self._results.clear()

    def _get_status_count(self, status: DownloadStatus) -> int:
        """Helper method to count results by status."""
        return sum(1 for r in self.results if r.status == status)

    @property
    def success_count(self) -> int:
        """Get count of success downloads."""
        return self._get_status_count(DownloadStatus.SUCCESS)

    @property
    def failed_count(self) -> int:
        """Get count of failed downloads."""
        return self._get_status_count(DownloadStatus.FAILED)

    @property
    def skipped_count(self) -> int:
        """Get count of skipped downloads."""
        return self._get_status_count(DownloadStatus.SKIPPED)

    @property
    def replaced_count(self) -> int:
        """Get count of replaced downloads."""
        return self._get_status_count(DownloadStatus.REPLACED)

    @property
    def all_success(self) -> bool:
        """Check if all downloads were successful."""
        if not self.results:  # No downloads completed yet
            return False
        return all(
            result.status == DownloadStatus.SUCCESS
            or result.status == DownloadStatus.SKIPPED
            or result.status == DownloadStatus.REPLACED
            for result in self.results
        )
