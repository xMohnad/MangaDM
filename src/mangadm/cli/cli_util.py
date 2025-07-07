import json
import os
from pathlib import Path
from typing import Any, Dict

import click


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
        appdata = os.getenv("APPDATA")
        config_dir = Path(appdata) if appdata else Path.home() / ".config"
        config_dir = config_dir / "manga_dm"
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
            click.echo(f"Failed to load config from {config_path}: {e}")
            return {}

    @staticmethod
    def save_stored_settings(settings: Dict[str, Any]) -> None:
        """Save settings to the configuration file."""
        config_path = CliUtility.get_config_path()

        try:
            with open(config_path, "w", encoding="utf-8") as config_file:
                json.dump(settings, config_file, ensure_ascii=False, indent=4)
        except (IOError, OSError) as e:
            click.echo(f"Failed to save config to {config_path}: {e}")

    @staticmethod
    def display_example_json():
        """Display an example JSON structure."""
        # Define common values
        image_urls = [
            "https://example.com/image1.jpg",
            "https://example.com/image2.jpg",
            "https://example.com/image3.jpg",
            "https://example.com/image4.jpg",
            "etc",
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

        from rich.console import Console

        console = Console()
        console.print_json(json.dumps(example_json))
