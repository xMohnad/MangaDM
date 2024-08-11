import sys, time
from rich.console import Console


console = Console()


class Logger:
    """Class for handling colored and formatted logging messages."""

    _last_message = ""
    _last_time = 0
    _update_interval = (
        1.0  # Interval in seconds to consider updates for the same message
    )

    _error_count = 0
    _error_limit = 5
    _error_interval = 60  # Interval in seconds to consider errors for the limit

    _skipping = 0

    @staticmethod
    def _should_update(message: str) -> bool:
        """
        Check if the message should update the existing message based on time interval.
        """
        current_time = time.time()
        if (
            message == Logger._last_message
            and (current_time - Logger._last_time) < Logger._update_interval
        ):
            return False
        Logger._last_message = message
        Logger._last_time = current_time
        return True

    def skipping_msg() -> None:
        """ """
        Logger._skipping += 1
        if Logger._skipping % 10 == 0:  # Print a message every 10 skips
            Logger.warning(f"Skipping download. Total skipped: {Logger._skipping}.")

    @staticmethod
    def info(message: str) -> None:
        """Print an informational message."""
        if Logger._should_update(message):
            console.print(f"[cyan]{message}[/]")  # Cyan color

    @staticmethod
    def success(message: str) -> None:
        """Print a success message."""
        if Logger._should_update(message):
            console.print(f"[green]{message}[/]")  # Green color

    @staticmethod
    def warning(message: str) -> None:
        """Print a warning message."""
        if Logger._should_update(message):
            console.print(f"[yellow]{message}[/]")  # Yellow color

    @staticmethod
    def error(message: str) -> None:
        """Print an error message and check if the error threshold is reached."""
        Logger._error_count += 1
        current_time = time.time()
        if (
            Logger._error_count > Logger._error_limit
            and (current_time - Logger._last_time) < Logger._error_interval
        ):
            Logger._shutdown_program(f"Too many errors encountered. Shutting down.")
        else:
            if Logger._should_update(message):
                console.print(f"[red]{message}[/]")  # Red color

    @staticmethod
    def _shutdown_program(message: str) -> None:
        """Shutdown the program with a message."""
        console.print(f"[red]{message}[/]")  # Red color
        sys.exit(1)
