from typing import Optional
import requests
import os
from rich.progress import Progress
from ..utility import Utility, Logger


class Downloader:
    """Manages the downloading of files, supporting resume capability and displaying progress."""

    def __init__(
        self, dest_path: str = ".", force_download=False, name: Optional[str] = None
    ):
        self.session = requests.Session()
        self.download_path = dest_path
        self.force_download = force_download
        self.name = name

    def download(self, url, progress: Progress, completed_files=None):
        local_filename = self.name if self.name else Utility.get_filename_from_url(url)
        temp_filename = f"{local_filename}_temp"

        full_temp_path = os.path.join(self.download_path, temp_filename)
        full_path = os.path.join(self.download_path, local_filename)

        # Ensure download path exists
        os.makedirs(self.download_path, exist_ok=True)

        # Check if the file already exists and force_download is not set
        if not self.force_download and os.path.exists(full_path):
            Logger.skipping_msg()
            return

        # Remove existing file if force_download is True
        if self.force_download and os.path.exists(full_path):
            os.remove(full_path)

        current_size = Utility.get_size(full_temp_path)
        headers = {"Range": f"bytes={current_size}-"}
        try:
            with self.session.get(url, headers=headers, stream=True) as response:
                response.raise_for_status()
                total_size = (
                    int(response.headers.get("content-length", 0)) + current_size
                )
                with progress:
                    with open(full_temp_path, "ab") as file:
                        task = progress.add_task(
                            "", total=total_size, completed=current_size
                        )
                        for chunk in response.iter_content(chunk_size=1024):
                            file.write(chunk)
                            progress.update(
                                task,
                                advance=len(chunk),
                                completed_count=(completed_files),
                            )

            # After download is complete, rename temp file to final file name
            os.rename(full_temp_path, full_path)
            return local_filename

        except requests.RequestException as e:
            Logger.error(f"Error downloading {local_filename}: {e}")
        except IOError as e:
            Logger.error(f"File error for {local_filename}: {e}")
        except Exception as e:
            Logger.error(f"An unexpected error occurred: {e}")
        return False

    def download_files(self, urls: list):
        """Downloads files from the given URLs."""
        Dsuccess = 0
        Dfailed = 0
        progress = Utility.create_bar(len(urls))
        for completed, url in enumerate(urls, start=1):
            if self.download(url, progress, completed):
                Dsuccess += 1
            Dfailed += 1
        self.close()
        return Dsuccess, Dfailed

    def download_file(self, url):
        """Downloads a single file from the given URL."""

        progress = Utility.create_bar()
        filename = self.download(url, progress)
        self.close()
        if filename:
            Logger.success(f"Successfully downloaded {filename}")
            return True
        Logger.error("Failed to download.")
        return False

    def close(self):
        self.session.close()  # Close the session when done
