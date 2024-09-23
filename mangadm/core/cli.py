import click
import json
import os
from mangadm import MangaDM
from mangadm.utils import CliUtility
from rich.console import Console
from click_completion import init

# Initialize the click-completion
init()

console = Console()

DEFAULT_SETTINGS = {
    "dest": ".",
    "limit": -1,
}

DEFAULT_FLAGS = {
    "force": False,
    "delete": False,
    "cbz": True,
    "transient": False,
}

def load_settings(user_settings, stored_settings):
    # Separate settings in loaded settings
    base_settings = {key: stored_settings.get(key, DEFAULT_SETTINGS[key]) for key in DEFAULT_SETTINGS}
    
    # Override defaults with user-provided settings if they are not None
    return {key: user_settings.get(key) if user_settings.get(key) is not None else base_settings[key]for key in DEFAULT_SETTINGS}
    
def load_flags_settings(user_flags, stored_settings):
    """Load and merge flags with user-provided flags."""

    return {
        key: user_flags[key] if user_flags[key] is not None else stored_settings.get(key, DEFAULT_FLAGS[key])
        for key in DEFAULT_FLAGS
    }

def load_and_merge_settings(user_settings, user_flags):
    """Merge default, stored, and user settings."""
    stored_settings = CliUtility.load_stored_settings()
    effective_settings = load_settings(user_settings, stored_settings)
    effective_flags = load_flags_settings(user_flags, stored_settings)
    
    return {**effective_settings, **effective_flags}

def save_default_settings(effective_settings):
    """Save the current effective settings as the new defaults."""
    CliUtility.save_stored_settings(effective_settings)
    click.echo("Settings have been saved:")
    display_saved_settings(effective_settings)

def display_saved_settings(effective_settings):
    """Display the saved settings in a user-friendly format."""
    click.echo("=" * 40)
    for key, value in effective_settings.items():
        console.print(f"{key.capitalize():<15}: {value}")
    click.echo("=" * 40)

@click.command()
@click.argument(
    "json_file", required=False,
    type=click.Path(exists=True), 
    
)
@click.option(
    "--dest", "-p", default=None,
    help="Destination path for downloading manga chapters.",
)
@click.option(
    "--limit", "-l", default=None, type=int,
    help="Number of chapters to download. If -1, download all chapters.",
)
@click.option(
    "--force/--no-force", "-f", is_flag=True, default=None,
    help="Re-download chapter if not complete.",
)
@click.option(
    "--delete/--no-delete", "-d", is_flag=True, default=None,
    help="Delete chapter data from JSON after successful download.",
)
@click.option(
    "--cbz/--no-cbz", "-z", is_flag=True, default=None,
    help="Save the chapter as CBZ.",
)
@click.option(
    "--transient/--no-transient", "-t", is_flag=True, default=None,
    help="Activate transient mode (progress bar will disappear after completion)."
)
@click.option(
    "--example", "-e", is_flag=True,
    help="Display an example JSON structure for the input file.",
)
@click.option(
    "--set-settings", "-s", is_flag=True,
    help="Save the current settings as default.",
)
@click.option(
    "--configure", "-c", is_flag=True,
    help="Open the configuration text UI to set up or change settings.",
)
@click.option(
    "--settings", is_flag=True,
    help="Display the current settings.",
)
@click.help_option("--help", "-h")
def cli(json_file, dest, limit, force, delete, cbz, transient, example, set_settings, configure, settings):
    """A command-line tool for downloading manga chapters based on a JSON file."""
    
    # Open settings UI if requested
    if configure:
        user_settings = CliUtility.settings_ui()
        if user_settings:
            save_default_settings(user_settings)
        return
    
    # Handle example option
    if example:
        CliUtility.display_example_json()
        return

    # Gather user-provided settings and flags
    user_settings = {
        "dest": dest,
        "limit": limit,
    }
    user_flags = {
        "force": force,
        "delete": delete,
        "cbz": cbz,
        "transient": transient,
    }

    # Merge settings and flags
    effective_settings = load_and_merge_settings(user_settings, user_flags)

    if settings:
        display_saved_settings(effective_settings)
        return

    if set_settings:
        save_default_settings(effective_settings)
        return

    if not json_file:
        click.echo("Error: Missing argument 'JSON_FILE'.")
        click.echo("For help, try 'mangadm --help'.")
        return

    # Start the manga download process
    manga_downloader = MangaDM(
        json_file=json_file,
        dest_path=effective_settings["dest"],
        chapters_limit=effective_settings["limit"],
        force_download=effective_settings["force"],
        delete_on_success=effective_settings["delete"],
        save_as_CBZ=effective_settings["cbz"],
        transient=effective_settings["transient"]
    )

    manga_downloader.start()

if __name__ == "__main__":
    cli()
