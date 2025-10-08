from __future__ import annotations

import json
from dataclasses import asdict, dataclass
from pathlib import Path

from dacite import from_dict


@dataclass
class MangaDetails:
    source: str
    title: str
    cover: str
    description: str
    genres: list[str]
    author: str | None = None
    artist: str | None = None

    def to_json(self, path: Path) -> None:
        """Save manga details to a JSON file."""
        path.write_text(
            json.dumps(
                asdict(self),
                indent=4,
                ensure_ascii=False,
            ),
            encoding="utf-8",
        )


@dataclass
class Chapter:
    title: str
    images: list[str]


@dataclass
class Manga:
    details: MangaDetails
    chapters: list[Chapter]

    @classmethod
    def from_json_file(cls, file_path: Path) -> Manga:
        """Load a Manga instance from a JSON file."""
        return from_dict(
            cls,
            json.loads(file_path.read_text(encoding="utf-8")),  # pyright: ignore[reportAny]
        )
