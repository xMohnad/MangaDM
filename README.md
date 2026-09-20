# MangaDM - Manga Download Manager

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](./LICENSE)
[![Ask DeepWiki](https://deepwiki.com/badge.svg)](https://deepwiki.com/xMohnad/MangaDM)
[![PyPI Version](https://img.shields.io/pypi/v/MangaDM.svg)](https://pypi.python.org/pypi/MangaDM)
[![Python Version](https://img.shields.io/pypi/pyversions/MangaDM.svg)](https://pypi.python.org/pypi/MangaDM)

**MangaDM** is a command-line tool for downloading manga from a JSON metadata file.

---

## Installation

```sh
pip install MangaDM
```

## Usage

```sh
mangadm download manga.json --format epub --dest ~/manga
mangadm download --help
```

## JSON Structure

```json
{
  "details": {
    "source": "Source Name",
    "title": "Manga Name",
    "cover": "https://example.com/cover.jpg",
    "description": "Description",
    "genres": ["genre 1", "genre 2"],
    "author": "string|null",
    "artist": "string|null"
  },
  "chapters": [
    {
      "title": "chapter 256 - Title",
      "images": [
        "https://example.com/image1.jpg",
        "https://example.com/image2.jpg"
      ],
      "document_location": "https://example.com/chapter-256"
    }
  ]
}
```

## Contributing

Contributions are welcome! If you'd like to contribute, please fork the repository and submit a pull request. For major changes, please open an issue first to discuss the proposed changes.
