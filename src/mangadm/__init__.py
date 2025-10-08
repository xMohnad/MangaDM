from pathlib import Path

import typer

__version__ = "0.6.0"
__config__: Path = Path(typer.get_app_dir(__name__)) / "config.yaml"
__config__.parent.mkdir(parents=True, exist_ok=True)
