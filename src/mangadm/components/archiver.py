import os
import shutil
import zipfile
from pathlib import Path
from typing import List

from ebooklib import epub
from rich.progress import Progress

from mangadm.assets import build_chapter_content, epub_style_css
from mangadm.components import FormatType


class MangaArchiver:
    def __init__(self, progress: Progress) -> None:
        self.SUPPORTED_IMAGE_EXTENSIONS = (".png", ".jpg", ".jpeg", ".webp")
        self.progress = progress

    def _get_image_paths(self, folder_path: Path):
        """Return sorted list of image paths from the given folder."""
        return [
            os.path.join(root, file)
            for root, _, files in os.walk(folder_path)
            for file in sorted(files)
            if file.lower().endswith(self.SUPPORTED_IMAGE_EXTENSIONS)
        ]

    def get_image_paths(self, folder_path: Path) -> List[Path]:
        """Return sorted list of image paths from the given folder."""
        folder = Path(folder_path).resolve()
        return sorted(
            [
                file
                for file in folder.rglob("*")
                if file.suffix.lower() in self.SUPPORTED_IMAGE_EXTENSIONS
            ]
        )

    def create_cbz(self, folder_path: Path) -> None:
        """Create a CBZ (Comic Book ZIP) file from a folder and delete the original folder."""
        folder = Path(folder_path).resolve()
        folder_name = folder.name
        cbz_file = folder.parent / f"{folder_name}.cbz"

        try:
            image_paths = self.get_image_paths(folder)

            with zipfile.ZipFile(cbz_file, "w", zipfile.ZIP_DEFLATED) as cbz:
                for file_path in image_paths:
                    cbz.write(file_path, file_path.relative_to(folder))

            shutil.rmtree(str(folder))
        except (IOError, OSError) as e:
            self.progress.log(f"Error creating `{cbz_file.name}`: {e}")

    def create_epub(self, folder_path: Path) -> None:
        """Create an EPUB file from a folder of images."""
        folder = Path(folder_path).resolve()
        folder_name = folder.name
        epub_file = folder.parent / f"{folder_name}.epub"

        book = epub.EpubBook()
        book.set_title(folder_name)
        book.set_language("en")

        # Add default Navigation files
        book.add_item(epub.EpubNcx())
        book.add_item(epub.EpubNav())

        # Add stylesheet
        style = epub.EpubItem(
            uid="style",
            file_name="style.css",
            media_type="text/css",
            content=epub_style_css(),
        )
        book.add_item(style)

        image_paths = self.get_image_paths(folder)

        # Create the chapter content with all images
        chapter_content = build_chapter_content(image_paths)
        chapter = epub.EpubHtml(
            title=folder_name,
            file_name="chap_all_images.xhtml",
            content=chapter_content,
        )
        book.add_item(chapter)

        # Add images as resources to the book
        for image_path in image_paths:
            filename = os.path.basename(image_path)
            with open(image_path, "rb") as img_file:
                img_item = epub.EpubImage()
                img_item.file_name = f"images/{filename}"
                img_item.content = img_file.read()
            book.add_item(img_item)

        # Set the table of contents and spine
        book.toc = [chapter]
        book.spine = ["nav", chapter]

        # Write the EPUB file
        epub.write_epub(epub_file, book)

        shutil.rmtree(folder)

    def create_archiver(self, folder: Path, format: FormatType):
        if format == FormatType.cbz:
            self.create_cbz(folder)
        elif format == FormatType.epub:
            self.create_epub(folder)
