from __future__ import annotations

import uuid
import zipfile
from datetime import UTC, datetime
from typing import TYPE_CHECKING, Final
from xml.sax.saxutils import escape, quoteattr

from mangadm.images import media_type

if TYPE_CHECKING:
    from collections.abc import Sequence
    from pathlib import Path

    from mangadm.manga import Chapter, MangaDetails

_CONTAINER: Final = """<?xml version="1.0" encoding="UTF-8"?>
<container version="1.0" xmlns="urn:oasis:names:tc:opendocument:xmlns:container">
  <rootfiles>
    <rootfile full-path="OEBPS/content.opf" media-type="application/oebps-package+xml"/>
  </rootfiles>
</container>
"""

_STYLE: Final = """html, body { margin: 0; padding: 0; background: #000; }
img { display: block; margin: 0 auto; max-width: 100%; max-height: 100vh; object-fit: contain; }
"""

_PAGE: Final = """<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE html>
<html xmlns="http://www.w3.org/1999/xhtml" lang="und">
<head>
  <meta charset="utf-8"/>
  <title>{title}</title>
  <link rel="stylesheet" type="text/css" href="../style.css"/>
</head>
<body><img src={src} alt=""/></body>
</html>
"""

_NAV: Final = """<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE html>
<html xmlns="http://www.w3.org/1999/xhtml" xmlns:epub="http://www.idpf.org/2007/ops" lang="und">
<head>
  <meta charset="utf-8"/>
  <title>{title}</title>
</head>
<body>
  <nav epub:type="toc" id="toc">
    <ol><li><a href={first}>{title}</a></li></ol>
  </nav>
</body>
</html>
"""

_PACKAGE: Final = """<?xml version="1.0" encoding="UTF-8"?>
<package xmlns="http://www.idpf.org/2007/opf" version="3.0" unique-identifier="book-id" xml:lang="und">
  <metadata xmlns:dc="http://purl.org/dc/elements/1.1/">
    <dc:identifier id="book-id">urn:uuid:{book_id}</dc:identifier>
    <dc:title>{title}</dc:title>
    <dc:language>und</dc:language>
{extra_metadata}
    <meta property="dcterms:modified">{modified}</meta>
  </metadata>
  <manifest>
    <item id="nav" href="nav.xhtml" media-type="application/xhtml+xml" properties="nav"/>
    <item id="style" href="style.css" media-type="text/css"/>
{manifest}
  </manifest>
  <spine>
{spine}
  </spine>
</package>
"""


def _metadata(details: MangaDetails) -> str:
    people = dict.fromkeys(filter(None, (details.author, details.artist)))
    elements = [f"<dc:creator>{escape(name)}</dc:creator>" for name in people]
    elements += [f"<dc:subject>{escape(genre)}</dc:subject>" for genre in details.genres]
    if details.description:
        elements.append(f"<dc:description>{escape(details.description)}</dc:description>")
    return "\n".join(f"    {element}" for element in elements)


def write_epub(dest: Path, pages: Sequence[Path], details: MangaDetails, chapter: Chapter) -> None:
    """Write pages into an EPUB 3 file with one XHTML page per image."""
    title = escape(f"{chapter.title}")
    key = chapter.document_location or f"{details.source}/{details.title}/{chapter.title}"

    manifest: list[str] = []
    spine: list[str] = []
    for index, page in enumerate(pages):
        cover = ' properties="cover-image"' if index == 0 else ""
        manifest.append(
            f'    <item id="page-{page.stem}" href="pages/{page.stem}.xhtml" media-type="application/xhtml+xml"/>'
        )
        manifest.append(
            f'    <item id="img-{page.stem}" href="images/{page.name}" media-type="{media_type(page)}"{cover}/>'
        )
        spine.append(f'    <itemref idref="page-{page.stem}"/>')

    package = _PACKAGE.format(
        book_id=uuid.uuid5(uuid.NAMESPACE_URL, key),
        title=title,
        extra_metadata=_metadata(details),
        modified=datetime.now(UTC).strftime("%Y-%m-%dT%H:%M:%SZ"),
        manifest="\n".join(manifest),
        spine="\n".join(spine),
    )

    with zipfile.ZipFile(dest, "w", zipfile.ZIP_STORED) as zf:
        zf.writestr("mimetype", "application/epub+zip")
        for name, content in {
            "META-INF/container.xml": _CONTAINER,
            "OEBPS/content.opf": package,
            "OEBPS/nav.xhtml": _NAV.format(title=title, first=quoteattr(f"pages/{pages[0].stem}.xhtml")),
            "OEBPS/style.css": _STYLE,
        }.items():
            zf.writestr(name, content, compress_type=zipfile.ZIP_DEFLATED)
        for page in pages:
            src = quoteattr(f"../images/{page.name}")
            zf.writestr(
                f"OEBPS/pages/{page.stem}.xhtml",
                _PAGE.format(title=title, src=src),
                compress_type=zipfile.ZIP_DEFLATED,
            )
            zf.write(page, f"OEBPS/images/{page.name}")
