import requests
from typing import Optional, Any
import signal
import sys
from rich.progress import Progress

from mangadm.components import StatsManager, Logger

# from mangadm.utils import Utility


class SignalHandler:
    _session = None
    _json_file = ""
    _data = []
    _progress = None
    _message = ""
    _stats_manager = None

    @classmethod
    def initialize(
        cls,
        session: Optional[requests.Session],
        json_file: Optional[str],
        data: list,
        progress: Optional[Progress],
        stats_manager: Optional[StatsManager],
    ) -> None:
        """Initialize the SignalHandler with necessary resources."""
        cls._session = session
        cls._json_file = json_file
        cls._data = data
        cls._progress = progress
        cls._stats_manager = stats_manager

        # Register signal handlers
        signal.signal(signal.SIGINT, cls.signal_handler)
        signal.signal(signal.SIGTERM, cls.signal_handler)
        signal.signal(signal.SIGTERM, cls.custom_signal_handler)

    @classmethod
    def signal_handler(cls, sig: int, frame: Optional[Any]) -> None:
        cls.clean_up_and_exit(results=True)

    @classmethod
    def custom_signal_handler(cls, sig: int, frame: Optional[Any]) -> None:
        cls.clean_up_and_exit()

    @classmethod
    def clean_up_and_exit(cls, results: bool = False) -> None:
        if cls._progress:
            cls._progress.stop()
        if cls._session:
            cls._session.close()

        # Utility.save_data(cls._json_file, cls._data)
        if results:
            Logger.error("Operation cancelled by user", False, red=True)

        cls._stats_manager.log_download_results()
        sys.exit(0)

    @classmethod
    def update_progress(cls, progress: Optional[Progress]) -> None:
        """Update the progress object."""
        cls._progress = progress

    @classmethod
    def update_session(cls, session: Optional[requests.Session]) -> None:
        """Update the session object."""
        cls._session = session

    @classmethod
    def update_data(cls, data: list, json_file: str) -> None:
        """Update data and json file path."""
        cls._data = data
        cls._json_file = json_file

    @classmethod
    def update_stats_manager(cls, stats_manager: Optional[StatsManager]) -> None:
        """Update the stats_manager object."""
        cls._stats_manager = stats_manager
