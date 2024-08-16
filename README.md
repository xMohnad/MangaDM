# MangaDM - Manga Download Manager

**MangaDM** is a command-line tool and Python library for downloading manga chapters based on the metadata specified in a JSON file.

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
    pip install -e .
    ```

### Install from Distribution Package

If you have a `.tar.gz` file, you can install it using `pip`:

```sh
pip install dist/MangaDM-x.x.tar.gz
```

-   or `.whl`

```sh
pip install dist/MangaDM-x.x-py3-none-any.whl
```

## Usage

Once installed, you can use the `manga-dm` command to download manga chapters. Here are the available options

### Example Commands

```sh
manga-dm [OPTIONS] [JSON_FILE]
```

#### Basic Usage

```sh
manga-dm /path/to/manga.json
```

This command will download all chapters specified in the `manga.json` file to the current directory.

#### Specify Destination Path

```sh
manga-dm /path/to/manga.json --dest /path/to/save
```

This command will download all chapters to the specified destination path.

#### Limit Number of Chapters

```sh
manga-dm /path/to/manga.json --limit 10
```

This command will download only the first 10 chapters.

#### Force Re-download of Existing Files

```sh
manga-dm /path/to/manga.json --force
```

This command will re-download files even if they already exist.

#### Delete Data After Successful Download

```sh
manga-dm /path/to/manga.json --delete
```

This command will delete the chapter data from the JSON file after a successful download.

#### Set and Save Default Settings

To set and save your current settings as the default, use the `--set-defaults` option:

```sh
manga-dm /path/to/manga.json --dest /path/to/save --limit 10 --force --delete --set-defaults
```

This command will save the current settings (destination path, chapter limit, force re-download, delete on success) as the default for future downloads.

### Options

-   `--dest` or `-p`: Destination path for downloading manga chapters. Default is the current directory.
-   `--limit` or `-l`: Number of chapters to download. If `-1`, download all chapters. Default is `-1`.
-   `--force` or `-f`: Re-download files even if they exist.
-   `--delete` or `-d`: Delete chapter data from JSON after successful download.
-   `--set-defaults` or `-s`: Save the current settings as default.
-   `--example` or `-e`: Display an example JSON structure for the input file.
-   `--help` or `-h`: Show this message and exit.

### Example JSON Structure

If you want to see an example of the expected JSON structure for the input file, you can use the `--example` option:

```sh
manga-dm --example
```

## Using MangaDM as a Library

You can also use MangaDM as a Python library. Here’s how you can use it programmatically:

### Example Usage

```python
from manga_dm import MangaDM

# Create an instance of MangaDM with desired parameters
manga_dm = MangaDM(
    json_file="path/to/yourfile.json",
    dest_path="path/to/chapter",
    chapters_limit=1,
    delete_on_success=False,
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
-   `delete_on_success` (bool): If True, delete chapter data from JSON after successful download. Defaults to False.

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
    },
    {
        "manganame": "Boruto",
        "cover": "https://example.com/cover.jpg",
        "title": "Boruto - 7",
        "images": [
            "https://example.com/image1.jpg",
            "https://example.com/image2.jpg",
            "https://example.com/image3.jpg"
        ]
    }
    // ....
]
```

## Contributing

If you'd like to contribute to this project, feel free to fork the repository and submit a pull request. Any improvements or bug fixes are welcome!
