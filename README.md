# MangaDM - Manga Download Manager

**MangaDM** is a command-line tool and Python library for downloading manga chapters based on the metadata specified in a JSON file, with options to limit the number of chapters, re-download files, and clean up the JSON data.

## Installation

To install the MangaDM, you need to have Python installed on your system. You can then use `pip` to install from the source code or from a distribution package.

### Install from Source

1. Clone the repository:

    ```sh
    git clone https://github.com/xMohnad/MangaDM.git
    cd MangaDM
    ```

2. Install the tool:
    ```sh
    pip install .
    ```

### Install from Distribution Package

If you have a `.tar.gz` file, you can install it using `pip`:

```sh
pip install dist/MangaDM-0.1.tar.gz
```

## Usage

Once installed, you can use the `manga-dm` command to download manga chapters. Here are the available options:

### Basic Command

To start downloading manga chapters, use:

```sh
manga-dm path/to/yourfile.json
```

### Options

-   `--dest` or `-p`: Specify the destination path for downloading manga chapters. Defaults to the current directory.

    ```sh
    manga-dm path/to/yourfile.json --dest /path/to/destination
    ```

-   `--limit` or `-l`: Specify the number of chapters to download. If set to -1, all chapters will be downloaded. Defaults to -1.

    ```sh
    manga-dm path/to/yourfile.json --limit 10
    ```

-   `--force` or `-f`: Force re-download of files even if they already exist.

    ```sh
    manga-dm path/to/yourfile.json --force
    ```

-   `--delete` or `-d`: Delete chapter data from the JSON file after successful download. This will remove the downloaded chapters from the JSON file.

    ```sh
    manga-dm path/to/yourfile.json --delete
    ```

-   `--example` or `-e`: Display an example JSON structure for the input file.
    ```sh
    manga-dm --example
    ```

## Using MangaDM as a Library

You can also use MangaDM as a Python library. Here’s how you can use it programmatically:

### Example Usage

```python
from MangaDM import MangaDM

# Create an instance of MangaDM with desired parameters
manga_dm = MangaDM(
    json_file="path/to/yourfile.json",
    dest_path="path/to/chapter",
    chapters_limit=1,
    delete_if_success=False,
    force_download=False,
)

# Start the downloading process
manga_dm.start()
```

### Parameters

-   `json_file` (str): The path to the JSON file containing manga data.
-   `dest_path` (str): The destination path where manga chapters will be downloaded. Defaults to the current directory.
-   `chapters_limit` (int): Number of chapters to download. If -1, download all chapters. Defaults to -1.
-   `force_download` (bool): If True, re-download files even if they exist. Defaults to False.
-   `delete_if_success` (bool): If True, delete chapter data from JSON after successful download. Defaults to False.

## Example JSON Structure

Here’s an example of the JSON structure required for the input file:

```json
[
    {
        "manganame": "Jujutsu Kaisen",
        "cover": "https://example.com/cover.jpg",
        "title": "Jujutsu Kaisen - 256",
        "images": [
            "https://example.com/image1.jpg",
            "https://example.com/image2.jpg",
            "https://example.com/image3.jpg"
        ]
    }
]
```
