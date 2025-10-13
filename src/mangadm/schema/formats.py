from __future__ import annotations

from enum import Enum


class FormatType(str, Enum):
    """
    Enum representing supported output formats for manga archives.

    Attributes:
        cbz (str): Comic Book ZIP format.
        epub (str): EPUB e-book format.
    """

    cbz = "cbz"
    epub = "epub"

    @classmethod
    def formats(cls) -> list[str]:
        """
        Return a list of all supported format values.

        Returns:
            list[str]: A list of supported format strings
        """
        return [ft.value for ft in cls]
