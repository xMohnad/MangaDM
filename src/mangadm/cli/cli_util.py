import json
import os
from pathlib import Path
from typing import Any, Dict, Optional

import click
from InquirerPy.resolver import prompt
from rich.console import Console
from rich.table import Table


class PartialMatchGroup(click.Group):
    def get_command(self, ctx: click.Context, cmd_name: str) -> Optional[click.Command]:
        """Finds and returns a command by name, supporting partial matches."""
        full_name = self._resolve_command_name(cmd_name)
        return super().get_command(ctx, full_name)

    def _resolve_command_name(self, partial_name: str) -> str:
        """Resolves a partial command name to the full command name."""
        matches = [name for name in self.commands if name.startswith(partial_name)]

        if not matches:
            return partial_name  # No match found, return as-is

        if len(matches) == 1:
            return matches[0]  # Single match found

        # Multiple matches found
        raise click.BadParameter(
            f"Ambiguous command '{partial_name}'. Possible matches: {', '.join(sorted(matches))}"
        )


class CliUtility:
    def __init__(self):
        self.console = Console()
        self.config_path = self._resolve_config_path()
        self.settings = self._load()

    def _resolve_config_path(self) -> Path:
        """
        Get the path to the configuration file.

        - On Linux: ~/.config/manga_dm/config.json
        - On Windows: %APPDATA%/manga_dm/config.json

        Creates the directory if it does not exist.

        Returns:
            str: Absolute path to the configuration file.
        """
        base_dir = Path(os.getenv("APPDATA") or Path.home() / ".config")
        config_dir = base_dir / "manga_dm"
        config_dir.mkdir(parents=True, exist_ok=True)
        return config_dir / "config.json"

    def _load(self) -> Dict[str, Any]:
        if not self.config_path.exists():
            return {}
        try:
            return json.loads(self.config_path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError) as e:
            self.console.print(f"[Load error] {e}", style="red")
            return {}

    def save(self, settings: Dict[str, Any]) -> None:
        try:
            self.config_path.write_text(
                json.dumps(settings, ensure_ascii=False, indent=4), encoding="utf-8"
            )
        except OSError as e:
            self.console.print(f"[Save error] {e}", style="red")

    def show_example(self) -> None:
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
                {"title": f"chapter {i} - Example Title", "images": image_urls}
                for i in range(256, 259)
            ],
        }
        self.console.print_json(json.dumps(example_json))

    def reset(self) -> None:
        confirmation = prompt(
            [
                {
                    "type": "confirm",
                    "name": "confirm_reset",
                    "message": "Are you sure you want to reset all settings?",
                    "default": False,
                }
            ]
        )
        if not confirmation.get("confirm_reset", False):
            self.console.print("[yellow]Reset cancelled.")
            return

        try:
            self.config_path.unlink()
            self.console.print("[green]Settings have been reset.")
        except FileNotFoundError:
            self.console.print("[yellow]No settings to reset.")

    def display_settings(self, settings: Dict[str, Any]) -> None:
        table = Table(title="Current MangaDM Settings")
        table.add_column("Key", style="cyan")
        table.add_column("Value", style="magenta")
        for key, value in settings.items():
            if key != "save_defaults":
                table.add_row(key, str(value))
        self.console.print(table)
