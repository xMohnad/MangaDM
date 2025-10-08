from __future__ import annotations

from enum import Enum


class FormatType(str, Enum):
    cbz = "cbz"
    epub = "epub"

    @classmethod
    def formats(cls) -> list[str]:
        return [ft.value for ft in cls]
