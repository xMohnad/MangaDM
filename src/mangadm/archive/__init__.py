from __future__ import annotations

from enum import StrEnum
from typing import TYPE_CHECKING, Final, TypeAlias

from mangadm.archive.cbz import write_cbz
from mangadm.archive.epub import write_epub

if TYPE_CHECKING:
    from collections.abc import Callable, Sequence
    from pathlib import Path

    from mangadm.manga import Chapter, MangaDetails

    Writer: TypeAlias = Callable[[Path, Sequence[Path], MangaDetails, Chapter], None]


class FormatType(StrEnum):
    """Supported archive formats."""

    cbz = "cbz"
    epub = "epub"


_WRITERS: Final[dict[FormatType, Writer]] = {
    FormatType.cbz: write_cbz,
    FormatType.epub: write_epub,
}


def create_archive(
    fmt: FormatType,
    dest: Path,
    pages: Sequence[Path],
    details: MangaDetails,
    chapter: Chapter,
) -> None:
    """Write pages to `dest` in the given format, replacing it atomically."""
    part = dest.with_name(dest.name + ".part")
    try:
        _WRITERS[fmt](part, pages, details, chapter)
        part.replace(dest)
    except BaseException:
        part.unlink(missing_ok=True)
        raise
