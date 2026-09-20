import tomllib
from pathlib import Path

import typer

CONFIG_PATH: Path = Path(typer.get_app_dir("mangadm")) / "config.toml"


def load_config() -> dict[str, object]:
    """Read the config file, or return an empty dict if it doesn't exist.

    Raises:
        tomllib.TOMLDecodeError: If the file is not valid TOML.
    """
    if not CONFIG_PATH.is_file():
        return {}
    with CONFIG_PATH.open("rb") as f:
        return tomllib.load(f)
