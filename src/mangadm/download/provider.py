from __future__ import annotations

import shutil
from functools import cached_property
from typing import TYPE_CHECKING, Final

from mangadm.images import MEDIA_TYPES

if TYPE_CHECKING:
    from collections.abc import Sequence
    from pathlib import Path

    from mangadm.archive import FormatType
    from mangadm.manga import Chapter, MangaDetails

TMP_DIR_SUFFIX: Final = "_tmp"
TMP_FILE_SUFFIX: Final = ".tmp"
MIN_DISK_SPACE: Final = 200 * 1024 * 1024
MAX_NAME_BYTES: Final = 200

_TRANSLATION: Final = str.maketrans(
    {
        "/": "_",
        "\\": "_",
        '"': "_",
        "'": "_",
        "<": "_",
        ">": "_",
        "?": "",
        "*": " ",
        "%": " ",
        "$": "_",
        "#": "_",
        "@": "_",
        "~": "_",
        "}": "-",
        "{": "-",
        "|": "_",
        ":": "_",
        "+": "_",
        "=": "_",
        "[": "-",
        "]": "-",
        "&": "-",
    }
)


def sanitize_filename(name: str, max_bytes: int = MAX_NAME_BYTES) -> str:
    """Make a string safe to use as a file or folder name."""
    chars = (" " if c.isspace() else c for c in name.translate(_TRANSLATION))
    cleaned = "".join(c for c in chars if c.isprintable())
    truncated = cleaned.encode()[:max_bytes].decode(errors="ignore")
    return truncated.strip(" .") or "_"


class DownloadProvider:
    """Resolves the paths used by a manga download."""

    def __init__(self, dest: Path, details: MangaDetails, fmt: FormatType) -> None:
        """Initialize the provider for one manga."""
        self._dest = dest
        self._details = details
        self._format = fmt

    @cached_property
    def manga_dir(self) -> Path:
        """Manga folder, created on first access."""
        name = f"{sanitize_filename(self._details.title)} ({sanitize_filename(self._details.source)})"
        path = self._dest / name
        path.mkdir(parents=True, exist_ok=True)
        return path

    @property
    def details_path(self) -> Path:
        """Path of the saved manga details."""
        return self.manga_dir / "details.json"

    def chapter_dirnames(self, chapters: Sequence[Chapter]) -> list[str]:
        """Unique folder names for the chapters, in order."""
        seen: dict[str, int] = {}
        names: list[str] = []
        for chapter in chapters:
            base = sanitize_filename(chapter.title)
            seen[base] = count = seen.get(base, 0) + 1
            names.append(base if count == 1 else f"{base} ({count})")
        return names

    def archive_path(self, dirname: str) -> Path:
        """Final archive path of a chapter."""
        return self.manga_dir / f"{dirname}.{self._format}"

    def tmp_dir(self, dirname: str) -> Path:
        """Temporary folder holding the pages of an unfinished chapter."""
        return self.manga_dir / f"{dirname}{TMP_DIR_SUFFIX}"

    def is_downloaded(self, dirname: str) -> bool:
        """Whether the chapter archive already exists."""
        return self.archive_path(dirname).is_file()

    def has_enough_space(self) -> bool:
        """Whether there is enough free disk space to download a chapter."""
        return shutil.disk_usage(self.manga_dir).free >= MIN_DISK_SPACE

    @staticmethod
    def existing_images(directory: Path) -> dict[str, Path]:
        """Finished images in a folder, keyed by file name without extension."""
        if not directory.is_dir():
            return {}
        return {p.stem: p for p in directory.iterdir() if p.is_file() and p.suffix[1:].lower() in MEDIA_TYPES}
