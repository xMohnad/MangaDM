# pyright: reportUnknownMemberType=false

from __future__ import annotations

import logging
import shutil
import zipfile
from pathlib import Path
from typing import Callable

from ebooklib import epub  # pyright: ignore[reportMissingTypeStubs]

from mangadm.assets import build_chapter_content
from mangadm.schema.formats import FormatType

IMAGE_EXTENSIONS: list[str] = [".jpg", ".jpeg", ".gif", ".tiff", ".tif", ".png"]


class MangaArchiver:
    """Utility class to create manga archives in different formats (CBZ, EPUB)."""

    logger: logging.Logger = logging.getLogger(__name__)

    def get_image_paths(self, folder_path: Path) -> list[Path]:
        """Return sorted list of image paths from the given folder."""
        return sorted([file for file in folder_path.absolute().rglob("*") if file.suffix.lower() in IMAGE_EXTENSIONS])

    def _make_file(self, folder: Path, format: FormatType) -> Path:
        """Return a Path for the output archive file based on format."""
        return folder.with_suffix(f".{format.value}")

    def create_cbz(self, folder_path: Path, **_: object) -> None:
        """Create a CBZ (Comic Book ZIP) file from a folder and delete the original folder."""
        folder = folder_path.resolve()
        cbz_file = self._make_file(folder, FormatType.cbz)
        try:
            with zipfile.ZipFile(cbz_file, "w", zipfile.ZIP_DEFLATED) as cbz:
                for file_path in self.get_image_paths(folder):
                    cbz.write(file_path, file_path.relative_to(folder))
                    self.logger.debug("Added image '%s' to CBZ", file_path.name)

            shutil.rmtree(folder)
            self.logger.info("CBZ archive '%s' created successfully and folder removed", cbz_file.name)
        except (IOError, OSError):
            self.logger.exception(f"Error creating `{cbz_file.name}`")

    def create_epub(self, folder_path: Path, title: str = "", **_: object) -> None:
        """Create an EPUB file from a folder of images."""
        folder = folder_path.resolve()
        epub_file = self._make_file(folder, FormatType.epub)

        book = epub.EpubBook()
        book.set_title(title)

        image_paths = self.get_image_paths(folder)
        chapter = epub.EpubHtml(
            title=title,
            file_name="chapter.xhtml",
            content=build_chapter_content(image_paths),
        )
        book.add_item(chapter)

        # Add images as resources to the book
        for image_path in image_paths:
            book.add_item(epub.EpubImage(file_name=f"images/{image_path.name}", content=image_path.read_bytes()))
            self.logger.debug("Added image '%s' to EPUB", image_path.name)

        book.spine = ["nav", chapter]

        try:
            epub.write_epub(epub_file, book)
            shutil.rmtree(folder)
            self.logger.info("EPUB archive '%s' created successfully and folder removed", epub_file.name)
        except (IOError, OSError) as e:
            self.logger.exception("Error creating EPUB '%s': %r", epub_file.name, e)

    def create_archive(self, folder: Path, format: FormatType, title: str = "") -> None:
        """Dispatch to the correct archive creation method based on format.

        Args:
            folder (Path): Folder containing image files.
            format (FormatType): Target archive format (e.g., cbz or epub).
            title (str, optional): Optional title for formats that support it.
        """
        archiver: Callable[..., None] | None = getattr(self, f"create_{format.value}", None)
        if callable(archiver):
            self.logger.info("Starting archive creation for '%s' as %s", folder, format.value)
            archiver(folder_path=folder, title=title)
        else:
            self.logger.warning("No archiver found for format '%s'", format.value)
