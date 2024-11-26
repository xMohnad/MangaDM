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
    pip install .
    ```

### Install from Distribution Package

If you have a `.tar.gz` file, you can install it using `pip`:

```sh
pip install dist/MangaDM*.tar.gz
```

-   or `.whl`

```sh
pip install dist/MangaDM*py3-none-any.whl
```

## Usage

Once installed, you can use the `mangadm` command to download manga chapters. Here are the available options

### Example Commands

```sh
mangadm [OPTIONS] [JSON_FILE]
```

#### Basic Usage

```sh
mangadm /path/to/manga.json
```

This command will download all chapters specified in the `manga.json` file to the current directory.

#### Specify Destination Path

```sh
mangadm /path/to/manga.json --dest /path/to/save
```

This command will download all chapters to the specified destination path.

#### Limit Number of Chapters

```sh
mangadm /path/to/manga.json --limit 10
```

This command will download only the first 10 chapters.

#### Force Re-download of Existing Files

```sh
mangadm /path/to/manga.json --force
```

This command will re-download files even if they already exist.

#### Delete Data After Successful Download

```sh
mangadm /path/to/manga.json --delete
```

This command will delete the chapter data from the JSON file after a successful download.


#### Enable Transient Mode

```sh
mangadm /path/to/manga.json --transient
```

This command will enable transient mode, where progress indicators are not persisted after the download process completes.

#### Set and Save Default Settings

To set and save your current settings as the default, use the `--set-settings` option:

```sh
mangadm /path/to/manga.json --dest /path/to/save --limit 10 --force --delete --set-settings
```

-   or

```sh
mangadm /path/to/manga.json --dest /path/to/save --limit 10 --no-force --no-delete --set-settings
```

This command will save the current settings (destination path, chapter limit, force re-download, delete on success) as the default for future downloads.


### Example JSON Structure

If you want to see an example of the expected JSON structure for the input file, you can use the `--example` option:

```sh
mangadm --example
``` 

### Options

-   `--dest` or `-p`: Destination path for downloading manga chapters. Default is the current directory.
-   `--limit` or `-l`: Number of chapters to download. If `-1`, download all chapters. Default is `-1`.
-   `--force/--no-force` or `-f`: Re-download chapter if not complete.
-   `--delete/--no-delete` or `-d`: Delete chapter data from JSON after successful download.
-   `format` or `-m` [cbz|epub]: The format in which to save the downloaded manga. Can be either `"cbz"` for a comic book archive or `"epub"` for an e-book file. Defaults to `"cbz"`.
-   `--transient/--no-transient` or `-t`: Activate transient mode (progress bar will disappear after completion).
-   `--example` or `-e`: Display an example JSON structure for the input file.
-   `--configure` or `-c`: when enabled, opens a text-based user interface to configure or change settings.
-   `--settings` or `-s`: Display the current settings.
-   `--set-settings`: Save the current settings as default.
-   `--help` or `-h`


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
    format="cbz", # ["cbz", "epub"]
    transient=True
)

# Start the downloading process
mangadm.start()
```

### Parameters

-   `json_file` (str): The path to the JSON file containing manga data.
-   `dest_path` (str): The destination path where manga chapters will be downloaded. Defaults to the current directory.
-   `limit` (int): Number of chapters to download. If -1, download all chapters. Defaults to -1.
-   `force_download` (bool): If `True`, re-download files even if they exist. Defaults to False.
-   `delete_on_success` (bool): If `True`, delete chapter data from JSON after successful download. Defaults to False.
-   `format` (Literal["cbz", "epub"]): The format in which to save the downloaded manga. Can be either `"cbz"` for a comic book archive or `"epub"` for an e-book file. Defaults to `"cbz"`.
-   `transient` (bool): If `True`, activates transient mode. This mode ensures that progress indicators are not persisted after the process completes. Defaults to True.

## Example JSON Structure

Below is an example of the JSON structure required for the input file:

```json
{
  "details": {
    "source": "Example Source Name",
    "manganame": "Example Manga Name",
    "cover": "https://example.com/cover.jpg",
    "description": "Example Description",
    "genre": [
      "genre 1",
      "genre 2",
      "etc"
    ],
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


## Contributing

### Bug Reports & Feature Requests

If you encounter any issues while using MangaDM or have suggestions for new features, you can open an issue on the GitHub repository. Please provide detailed information about the issue or feature request to help in resolving it more effectively.

## License

MangaDM is open-source software licensed under the [MIT License](https://opensource.org/licenses/MIT). This means you can freely use, modify, and distribute the tool, provided you include the original license and copyright notice in any distributions or derivative works.

