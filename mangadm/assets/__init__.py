from pathlib import Path

ROOT = Path(__file__).parent

def image_error() -> bytes:
    return (ROOT / "not_available_error.webp").read_bytes()

def epub_style_css() -> bytes:
    return (ROOT / "style.css").read_bytes()

def build_chapter_content(image_paths):
    """Build the HTML content for the EPUB chapter with all images."""
    content = '''
        <?xml version="1.0" encoding="utf-8"?>
        <!DOCTYPE html>
        <html xmlns="http://www.w3.org/1999/xhtml" xml:lang="en" lang="en">
        <head>
            <meta charset="utf-8" />
            <meta name="viewport" content="width=device-width, initial-scale=1.0" />
            <link rel="stylesheet" type="text/css" href="{style}" />
        </head>
        <body>
        '''.format(style="style.css")

    # Add image tags to the content
    for image_path in image_paths:
        filename = Path(image_path).name
        content += f'<img src="images/{filename}" alt="{filename}" />'

    content += '</body></html>'
    return content  

