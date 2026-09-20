from __future__ import annotations

import json
from dataclasses import asdict, dataclass, field
from typing import TYPE_CHECKING

from dacite import DaciteError, from_dict

if TYPE_CHECKING:
    from pathlib import Path


@dataclass(frozen=True, slots=True)
class MangaDetails:
    """Manga metadata."""

    source: str
    title: str
    cover: str | None = None
    description: str | None = None
    genres: list[str] = field(default_factory=list)
    author: str | None = None
    artist: str | None = None

    def to_json(self, path: Path) -> None:
        """Write the details to a JSON file."""
        path.write_text(json.dumps(asdict(self), indent=4, ensure_ascii=False), encoding="utf-8")


@dataclass(frozen=True, slots=True)
class Chapter:
    """A chapter and its page image URLs."""

    title: str
    images: list[str]
    document_location: str | None = None


@dataclass(frozen=True, slots=True)
class Manga:
    """A manga with its chapters."""

    details: MangaDetails
    chapters: list[Chapter]

    @classmethod
    def from_json_file(cls, path: Path) -> Manga:
        """Load and validate a manga JSON file.

        Raises:
            ValueError: If the file is not valid JSON or does not match the schema.
        """
        try:
            data = json.loads(path.read_text(encoding="utf-8-sig"))
            if not isinstance(data, dict):
                raise ValueError("the top-level value must be an object")
            return from_dict(cls, data)
        except (ValueError, DaciteError) as e:
            raise ValueError(f"Invalid manga file {path}: {e}") from e
