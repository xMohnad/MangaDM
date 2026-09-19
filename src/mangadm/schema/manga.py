from __future__ import annotations

import json
from dataclasses import asdict, dataclass
from typing import TYPE_CHECKING

from dacite import from_dict

if TYPE_CHECKING:
    from pathlib import Path


@dataclass
class MangaDetails:
    """Detailed information about a manga."""

    source: str
    title: str
    cover: str
    description: str
    genres: list[str]
    author: str | None = None
    artist: str | None = None

    def to_json(self, path: Path) -> None:
        """Save manga details to a JSON file."""
        with path.open("w", encoding="utf-8") as f:
            json.dump(asdict(self), f, indent=4, ensure_ascii=False)


@dataclass
class Chapter:
    """Represents a manga chapter with images."""

    title: str
    images: list[str]
    document_location: str | None = None


@dataclass
class Manga:
    """A manga with details and its chapters."""

    details: MangaDetails
    chapters: list[Chapter]

    @classmethod
    def from_json_file(cls, file_path: Path) -> Manga:
        """Load a Manga instance from a JSON file."""
        with file_path.open("r", encoding="utf-8") as f:
            data: dict[str, object] = json.load(f)
        return from_dict(cls, data)
