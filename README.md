# MangaDM - Manga Download Manager

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](./LICENSE)

**MangaDM** is a command-line tool and Python library for downloading manga chapters based on the metadata specified in JSON files.

## Table of Contents

- [Installation](#installation)

  - [Install from PyPI](#install-from-pypi)
  - [Install from Source](#install-from-source)

- [CLI Usage](#cli-usage)

  - [Commands](#commands)
    - [download](#download)
    - [configure](#configure)
    - [example](#example)
    - [view](#view)
    - [reset](#reset)
    - [tui](#tui)
  - [General Notes](#general-notes)

- [Library Usage](#library-usage)

  - [Example](#example-usage)
  - [Parameters](#parameters)

- [JSON Structure](#json-structure)

  - [Structure Breakdown](#structure-breakdown)

- [Contributing](#contributing)

  - [Bug Reports & Feature Requests](#bug-reports-and-feature-requests)

______________________________________________________________________

## Installation

Ensure you have Python installed before proceeding.

______________________________________________________________________

### Install from PyPI

```sh
pip install MangaDM
```

______________________________________________________________________

### Install from Source

To install MangaDM directly from the source code:

1. **Clone the Repository**

   ```sh
   git clone https://github.com/xMohnad/MangaDM.git
   cd MangaDM
   ```

1. **Install MangaDM**

   ```sh
   pip install .
   ```

______________________________________________________________________

## CLI Usage

Once installed, you can use the `mangadm` command to download manga chapters.

### Commands

#### `download`

- **Purpose**: Downloads manga chapters based on a provided JSON file.
- **Arguments**:
  - `json_file`: Path to the JSON file containing manga download details.
- **Options**:
  - `--dest, -p`: Destination path for downloading manga (default is the current directory).
  - `--limit, -l`: Number of chapters to download (default is `-1` for all chapters).
  - `--delete/--no-delete, -d`: Delete data after successful download.
  - `--format, -f`: Format for downloaded manga (choices are based on `FormatType` enum).
  - `--update-details/--no-update-details, -u`: Update `details.json` and re-download cover.

#### `configure`

- **Purpose**: Opens a configuration UI for setting up MangaDM options.

#### `example`

- **Purpose**: Displays an example JSON structure.

#### `view`

- **Purpose**: Views the current configuration settings.

#### `reset`

- **Purpose**: Reset saved settings.

#### `tui`

- **Purpose**: Open Textual TUI.

### General Notes

- **Versioning**: The version is displayed with the `--version, -V` flag.
- **Completion**: The CLI supports shell completion using `auto_click_auto`. The `--autocomplete` flag is available to enable shell completion for the default shell.
- **More**: Use `--help` flag in any of the commands.

______________________________________________________________________

## Library Usage

You can also use MangaDM as a Python library. Here’s how you can use it programmatically:

### Example Usage

```python
from mangadm import MangaDM, FormatType

# Create an instance of MangaDM with desired parameters
mangadm = MangaDM(
    json_file="path/to/yourfile.json",
    dest_path="path/to/chapter",
    limit=1,
    delete_on_success=False,
    format=FormatType.cbz,
)

# Start the downloading process
mangadm.start()
```

### Parameters

- `json_file` (Path): The path to the JSON file containing manga data.
- `dest_path` (str): The destination path where manga chapters will be downloaded. Defaults to the current directory.
- `limit` (int): Number of chapters to download. If -1, download all chapters. Defaults to -1.
- `delete_on_success` (bool): If `True`, delete chapter data from JSON after successful download. Defaults to False.
- `format` (FormatType): The format in which to save the downloaded manga.

______________________________________________________________________

## JSON Structure

Below is an example of the JSON structure required for the input file:

```json
{
  "details": {
    "source": "Example Source Name",
    "manganame": "Example Manga Name",
    "cover": "https://example.com/cover.jpg",
    "description": "Example Description",
    "genre": ["genre 1", "genre 2", "etc"],
    "author": "Akutami Gege",
    "artist": "Akutami Gege"
  },
  "chapters": [
    {
      "title": "chapter 256 - Example Title",
      "images": [
        "https://example.com/image1.jpg",
        "https://example.com/image2.jpg",
        "https://example.com/image3.jpg",
        "https://example.com/image4.jpg",
        "etc"
      ]
    },
    {
      "title": "chapter 257 - Example Title",
      "images": [
        "https://example.com/image1.jpg",
        "https://example.com/image2.jpg",
        "https://example.com/image3.jpg",
        "https://example.com/image4.jpg",
        "etc"
      ]
    },
    {
      "title": "chapter 258 - Example Title",
      "images": [
        "https://example.com/image1.jpg",
        "https://example.com/image2.jpg",
        "https://example.com/image3.jpg",
        "https://example.com/image4.jpg",
        "etc"
      ]
    }
  ]
}
```

The JSON structure provided above illustrates the format expected for input files used by the MangaDM tool. Each JSON file should follow these guidelines:

### Structure Breakdown

- **`details`**: Contains metadata about the manga series.
  - **`source`**: The source or website where the manga is found.
  - **`manganame`**: The name of the manga series.
  - **`cover`**: A URL pointing to the cover image of the manga. This is optional but can enhance the metadata.
  - **`description`**: A short description of the manga.
  - **`genre`**: A list of genres the manga belongs to.
  - **`author`**: The name of the author of the manga.
  - **`artist`**: The name of the artist responsible for the manga's artwork.
- **`chapters`**: An array of objects, each representing a chapter in the manga.
  - **`title`**: The title or number of the chapter.
  - **`images`**: A list of URLs where each URL points to an image file, typically representing the pages of the manga chapter.

______________________________________________________________________

## Contributing

### Bug Reports and Feature Requests

If you encounter any issues while using MangaDM or have suggestions for new features,
you can open an issue on the GitHub repository.
Please provide detailed information about the issue or feature request to help in resolving it more effectively.
