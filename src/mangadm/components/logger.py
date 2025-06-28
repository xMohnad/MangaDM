import signal
import time
from rich.console import Console
from rich.panel import Panel
from rich.text import Text

console = Console()


class Logger:
    """Class for handling colored and formatted logging messages."""

    _last_message = ""
    _last_time = 0
    _update_interval = (
        1.0  # Interval in seconds to consider updates for the same message
    )

    _error_count = 0
    _error_limit = 2
    _error_interval = 30  # Interval in seconds to consider errors for the limit

    @staticmethod
    def _should_update(message: str) -> bool:
        """Check if the message should update the existing message based on time interval."""
        current_time = time.time()
        if (
            message == Logger._last_message
            and (current_time - Logger._last_time) < Logger._update_interval
        ):
            return False
        Logger._last_message = message
        Logger._last_time = current_time
        return True

    @staticmethod
    def info(message: str) -> None:
        """Print an informational message."""
        if Logger._should_update(message):
            console.print(f"[bold cyan]{message}[/]")  # Cyan color

    @staticmethod
    def success(message: str) -> None:
        """Print a success message."""
        if Logger._should_update(message):
            console.print(f"[bold green]{message}[/]")  # Green color

    @staticmethod
    def warning(message: str, enhanced: bool = False) -> None:
        """Print a warning message."""
        if Logger._should_update(message):
            if enhanced:
                warning_text = Text(message, style="bold yellow", justify="center")
                warning_text.stylize("underline")
                console.print(Panel(warning_text, title="[bold red]Warning[/]", border_style="bright_yellow"))
            else:
                console.print(f"[bold yellow]{message}[/]")  # Yellow color

    @staticmethod
    def error(
        message: str, enhanced: bool = True, count: bool = True, red: bool = False, close: bool = False
    ) -> None:
        """Print an error message and check if the error threshold is reached."""
        if count:
            Logger._error_count += 1
        current_time = time.time()
        if (
            Logger._error_count > Logger._error_limit
            and (current_time - Logger._last_time) < Logger._error_interval
        ):
            Logger._shutdown_program("\nToo many errors encountered. Shutting down.")
        else:
            if Logger._should_update(message):
                if enhanced:
                    timestamp = time.strftime("[%Y-%m-%d %H:%M:%S]", time.localtime())
                    error_text = Text(message, style="bold red", justify="center")
                    error_text.stylize("underline")
                    console.print(
                        Panel(error_text, title=timestamp, border_style="bright_red")
                    )
                elif red:
                    console.print(f"[bold red]{message}[/]")
                else:
                    console.print(message)
        if close:
            signal.raise_signal(signal.SIGTERM)

    @staticmethod
    def _shutdown_program(message: str) -> None:
        """Shutdown the program with a message."""
        console.print(f"[red]{message}[/]")  # Red color
        signal.raise_signal(signal.SIGTERM)