from pathlib import Path

ROOT: Path = Path(__file__).parent


def placeholder_image() -> bytes:
    return (ROOT / "placeholder_image.webp").read_bytes()


def build_chapter_content(image_paths: list[Path]) -> str:
    """Build the HTML content for the EPUB chapter with all images."""
    content = """
        <?xml version="1.0" encoding="utf-8"?>
        <!DOCTYPE html>
        <html xmlns="http://www.w3.org/1999/xhtml" xml:lang="en" lang="en">
        <head>
            <meta charset="utf-8" />
            <meta name="viewport" content="width=device-width, initial-scale=1.0" />
        </head>
        <body>
        """

    # Add image tags to the content
    for image_path in image_paths:
        filename = image_path.name
        content += f'<img src="images/{filename}" alt="{filename}" />'

    content += "</body></html>"
    return content
