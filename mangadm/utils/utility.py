from typing import Any, Dict, List
from urllib.parse import urlparse, unquote
import os, shutil, json
from pathlib import Path

import zipfile
from ebooklib import epub

from mangadm.components import Logger
from mangadm.assets import build_chapter_content, epub_style_css

from rich.console import Console

console = Console()

SUPPORTED_IMAGE_EXTENSIONS = (".png", ".jpg", ".jpeg", ".gif", ".bmp", ".webp")


class Utility:

    @staticmethod
    def get_size(local_filename: str) -> int:
        """Get the size of a file if it exists, otherwise return 0."""
        return os.path.getsize(local_filename) if os.path.exists(local_filename) else 0

    @staticmethod
    def get_filename_from_url(url: str) -> str:
        """Extract and decode the filename from a given URL."""
        return unquote(os.path.basename(urlparse(url).path))

    @staticmethod
    def get_ext_from_url(url: str) -> str:
        """Extract extension image from a given URL."""
        return Utility.get_filename_from_url(url).rsplit(".")[-1]

    @staticmethod
    def load_data(file_path: str) -> List[Dict[str, Any]]:
        """Load JSON data from a file."""
        if not os.path.exists(file_path):
            Logger.error(f"File {file_path} does not exist.")
            return []
        try:
            with open(file_path, "r", encoding="utf-8") as file:
                return json.load(file)
        except (json.JSONDecodeError, IOError) as e:
            Logger.error(f"Failed to load data from JSON file {file_path}: {e}")
            return []

    @staticmethod
    def is_downloaded_chapter(folder: str, temp_folder: str, images: List[str]) -> bool:
        """Check if a chapter is already downloaded."""
        folder_name = os.path.basename(folder.rstrip("/\\"))
        cbz_file = os.path.join(os.path.dirname(folder), f"{folder_name}.cbz")

        # Check if .cbz file exists
        if os.path.isfile(cbz_file):
            return True

        # Check if the temporary folder exists
        if os.path.isdir(temp_folder):
            return False

        folder_exists = os.path.isdir(folder)
        files = os.listdir(folder) if folder_exists else []
        has_temp = any("_temp" in file for file in files)

        # Check if has _temp in files
        if folder_exists and has_temp:
            return False

        # Check if the number of images matches the files in the folder
        if folder_exists and len(images) == len(files):
            return True

    @staticmethod
    def _get_image_paths(folder_path: str):
        """Return sorted list of image paths from the given folder."""
        return [
            os.path.join(root, file)
            for root, _, files in os.walk(folder_path)
            for file in sorted(files)
            if file.lower().endswith(SUPPORTED_IMAGE_EXTENSIONS)
        ]

    def get_image_paths(folder_path: str) -> List[Path]:
        """Return sorted list of image paths from the given folder."""
        folder = Path(folder_path).resolve()
        return sorted(
            [
                file
                for file in folder.rglob("*")
                if file.suffix.lower() in SUPPORTED_IMAGE_EXTENSIONS
            ]
        )

    @staticmethod
    def create_cbz(folder_path: str) -> None:
        """Create a CBZ (Comic Book ZIP) file from a folder and delete the original folder."""
        folder = Path(folder_path).resolve()
        folder_name = folder.name
        cbz_file = folder.parent / f"{folder_name}.cbz"

        try:
            image_paths = Utility.get_image_paths(folder)

            with zipfile.ZipFile(cbz_file, "w", zipfile.ZIP_DEFLATED) as cbz:
                for file_path in image_paths:
                    cbz.write(file_path, file_path.relative_to(folder))

            shutil.rmtree(str(folder))
        except (IOError, OSError) as e:
            Logger.error(f"Error creating `{cbz_file.name}`: {e}")

    @staticmethod
    def create_epub(folder_path: str) -> None:
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

        image_paths = Utility.get_image_paths(str(folder))

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
        book.toc = (chapter,)
        book.spine = ["nav", chapter]

        # Write the EPUB file
        epub.write_epub(epub_file, book)

        shutil.rmtree(folder)

    @staticmethod
    def save_data(file_path: str, data: List[Dict[str, Any]]) -> None:
        """Save data to a JSON file."""
        try:
            with open(file_path, "w", encoding="utf-8") as file:
                json.dump(data, file, ensure_ascii=False, indent=4)
        except (IOError, OSError) as e:
            Logger.error(f"Failed to save data to JSON file {file_path}: {e}")

    @staticmethod
    def rename(temp_folder, folder):
        try:
            temp_path = Path(temp_folder)
            folder_path = Path(folder)

            if folder_path.exists():
                Logger.warning(
                    f"'{temp_folder}' and '{folder}' are considered the same on this file system (case-insensitive).",
                    enhanced=True,
                )
                return False

            temp_path.rename(folder_path)
            return True

        except FileExistsError:
            msg = f"A file or folder named '{folder}' already exists."
        except PermissionError:
            msg = f"Permission denied. Cannot rename '{temp_folder}' to '{folder}'."
        except OSError as e:
            msg = f"OS error occurred: {e.strerror} (Error code: {e.errno})"
        except Exception as e:
            msg = f"An unexpected error occurred: {str(e)}"

        Logger.warning("Failed to rename temp file or folder:")
        Logger.error(msg, count=False)
        return False


class CliUtility:

    @staticmethod
    def get_config_path() -> str:
        """
        Get the path to the configuration file.
        
        - On Linux: ~/.config/manga_dm/config.json
        - On Windows: %APPDATA%/manga_dm/config.json
        
        Creates the directory if it does not exist.
        
        Returns:
            str: Absolute path to the configuration file.
        """
        config_dir = Path(
            (Path.home() / ".config" if not os.getenv("APPDATA") else Path(os.getenv("APPDATA")))
        ) / "manga_dm"
        
        config_dir.mkdir(parents=True, exist_ok=True)
    
        return str(config_dir / "config.json")
        
    @staticmethod
    def load_stored_settings() -> Dict[str, Any]:
        """Load stored settings from the configuration file."""
        config_path = CliUtility.get_config_path()

        if not os.path.exists(config_path):
            return {}

        try:
            with open(config_path, "r", encoding="utf-8") as config_file:
                return json.load(config_file)
        except (IOError, json.JSONDecodeError) as e:
            Logger.error(f"Failed to load config from {config_path}: {e}")
            return {}

    @staticmethod
    def save_stored_settings(settings: Dict[str, Any]) -> None:
        """Save settings to the configuration file."""
        config_path = CliUtility.get_config_path()

        try:
            with open(config_path, "w", encoding="utf-8") as config_file:
                json.dump(settings, config_file, ensure_ascii=False, indent=4)
        except (IOError, OSError) as e:
            Logger.error(f"Failed to save config to {config_path}: {e}")

    @staticmethod
    def display_example_json():
        """Display an example JSON structure."""
        # Define common values
        image_urls = [
            "https://example.com/image1.jpg",
            "https://example.com/image2.jpg",
            "https://example.com/image3.jpg",
            "https://example.com/image4.jpg",
            "etc"
        ]

        example_json = {
            "details": {
                "source": "Example Source Name",
                "manganame": "Example Manga Name",
                "cover": "https://example.com/cover.jpg",
                "description": "Example Description",
                "genre": ["genre 1", "genre 2", "etc"],
                "author": "Akutami Gege",
                "artist": "Akutami Gege",
            },
            "chapters": [
                {
                    "title": "chapter 256 - Example Title",
                    "images": image_urls,
                },
                {
                    "title": "chapter 257 - Example Title",
                    "images": image_urls,
                },
                {
                    "title": "chapter 258 - Example Title",
                    "images": image_urls,
                },
            ],
        }

        console.print_json(json.dumps(example_json))