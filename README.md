# MangaDM - Manga Download Manager

**MangaDM** is a command-line tool and Python library for downloading manga chapters based on the metadata specified in a JSON file.

## Table of Contents

1. [Installation](#installation)\
   1.1 [Install from Source](#install-from-source)\
   1.2 [Install from Distribution Package](#install-from-distribution-package)
1. [Usage CLI](#usage-cli)\
   2.1 [Commands](#commands)
   - [`download`](#download)
   - [`configure`](#configure)
   - [`example`](#example)
   - [`view`](#view)\
     2.2 [General Notes](#general-notes)
1. [Using MangaDM as a Library](#using-mangadm-as-a-library)\
   3.1 [Example Usage](#example-usage)\
   3.2 [Parameters](#parameters)
1. [Example JSON Structure](#example-json-structure)\
   4.1 [Structure Breakdown](#structure-breakdown)\
   4.2 [Adding More Entries](#adding-more-entries)
1. [Contributing](#contributing)\
   5.1 [Bug Reports & Feature Requests](#bug-reports-and-feature-requests)
1. [License](#license)

______________________________________________________________________

## Installation

Before installing MangaDM, ensure that Python is installed on your system. You can then install MangaDM via one of the following methods:

### Install from Source

To install MangaDM from the source code:

1. Clone the repository:

   ```sh
   git clone https://github.com/xMohnad/MangaDM.git
   cd MangaDM
   ```

1. Install the tool:

   ```sh
   pip install .
   ```

### Install from Distribution Package

You can install MangaDM using the `pip` tool from a `.tar.gz` or `.whl` distribution package:

- **For `.tar.gz` file**:

  ```sh
  pip install dist/MangaDM*.tar.gz
  ```

- **For `.whl` file**:

  ```sh
  pip install dist/MangaDM*py3-none-any.whl
  ```

This will install MangaDM from the specified package located in the `dist` directory.

______________________________________________________________________

## Usage CLI

Once installed, you can use the `mangadm` command to download manga chapters.

### Commands

#### `download`

- **Purpose**: Downloads manga chapters based on a provided JSON file.
- **Arguments**:
  - `json_file`: Path to the JSON file containing manga download details.
- **Options**:
  - `--dest, -p`: Destination path for downloading manga (default is the current directory).
  - `--limit, -l`: Number of chapters to download (default is `-1` for all chapters).
  - `--force/--no-force, -f`: Force re-download of incomplete images.
  - `--delete/--no-delete, -d`: Delete data after successful download.
  - `--format, -m`: Format for downloaded manga (choices are based on `FormatType` enum).
  - `--transient/--no-transient, -t`: Enable or disable transient mode.
  - `--update-details/--no-update-details, -u`: Update `details.json` and re-download cover.

#### `configure`

- **Purpose**: Opens a configuration UI for setting up MangaDM options.

#### `example`

- **Purpose**: Displays an example JSON structure.

#### `view`

- **Purpose**: Views the current configuration settings.

### General Notes

- **Versioning**: The version is displayed with the `--version` flag.
- **Completion**: The CLI supports shell completion using `auto_click_auto`. The `--autocomplete` flag is available to enable shell completion for the default shell.
- **More**: Use `--help` flag in any of the commands.

______________________________________________________________________

## Using MangaDM as a Library

You can also use MangaDM as a Python library. Here’s how you can use it programmatically:

### Example Usage

```python
from mangadm import MangaDM

# Create an instance of MangaDM with desired parameters
mangadm = MangaDM(
    json_file="path/to/yourfile.json",
    dest_path="path/to/chapter",
    limit=1,
    delete_on_success=False,
    force_download=False,
    format="cbz",  # ["cbz", "epub"]
    transient=True
)

# Start the downloading process
mangadm.start()
```

### Parameters

- `json_file` (Path): The path to the JSON file containing manga data.
- `dest_path` (str): The destination path where manga chapters will be downloaded. Defaults to the current directory.
- `limit` (int): Number of chapters to download. If -1, download all chapters. Defaults to -1.
- `force_download` (bool): If `True`, re-download files even if they exist. Defaults to False.
- `delete_on_success` (bool): If `True`, delete chapter data from JSON after successful download. Defaults to False.
- `format` (Literal["cbz", "epub"]): The format in which to save the downloaded manga. Can be either `"cbz"` or `"epub"`. Defaults to `"cbz"`.
- `transient` (bool): If `True`, activates transient mode. Defaults to True.

______________________________________________________________________

## Example JSON Structure

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

### Adding More Entries

You can include multiple manga entries, and the MangaDM tool will handle each entry sequentially according to the options provided.

______________________________________________________________________

## Contributing

### Bug Reports and Feature Requests

If you encounter any issues while using MangaDM or have suggestions for new features, you can open an issue on the GitHub repository. Please provide detailed information about the issue or feature request to help in resolving it more effectively.

______________________________________________________________________

## License

MangaDM is open-source software licensed under the [MIT License](https://opensource.org/licenses/MIT). This means you can freely use, modify, and distribute the tool, provided you include the original license and copyright notice in any distributions or derivative works.
