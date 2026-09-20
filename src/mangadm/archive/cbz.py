from __future__ import annotations

import zipfile
from typing import TYPE_CHECKING

from mangadm.archive.comicinfo import COMIC_INFO_FILE, build_comic_info

if TYPE_CHECKING:
    from collections.abc import Sequence
    from pathlib import Path

    from mangadm.manga import Chapter, MangaDetails


def write_cbz(dest: Path, pages: Sequence[Path], details: MangaDetails, chapter: Chapter) -> None:
    """Write pages and ComicInfo.xml into a CBZ file."""
    with zipfile.ZipFile(dest, "w", zipfile.ZIP_STORED) as zf:
        zf.writestr(COMIC_INFO_FILE, build_comic_info(details, chapter), compress_type=zipfile.ZIP_DEFLATED)
        for page in pages:
            zf.write(page, page.name)
