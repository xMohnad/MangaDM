from typing import Optional

from rich.console import Console


class BaseComponent:
    """Base class for all components with shared functionality."""

    def __init__(self, console: Optional[Console] = None):
        self._console = console or Console()

    @property
    def console(self) -> Console:
        return self._console

    @console.setter
    def console(self, value: Console):
        self._console = value
