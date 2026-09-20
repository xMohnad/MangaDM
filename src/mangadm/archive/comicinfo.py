from __future__ import annotations

import re
import xml.etree.ElementTree as ET
from typing import TYPE_CHECKING, Final

if TYPE_CHECKING:
    from mangadm.manga import Chapter, MangaDetails

COMIC_INFO_FILE: Final = "ComicInfo.xml"

_NUMBER: Final = re.compile(r"\d+(?:\.\d+)?")
_XML_ILLEGAL: Final = re.compile(r"[\x00-\x08\x0b\x0c\x0e-\x1f]")


def build_comic_info(details: MangaDetails, chapter: Chapter) -> bytes:
    """Build the ComicInfo.xml content for a chapter."""
    number = _NUMBER.search(chapter.title)
    fields = {
        "Title": chapter.title,
        "Series": details.title,
        "Number": number.group() if number else None,
        "Summary": details.description,
        "Writer": details.author,
        "Penciller": details.artist,
        "Genre": ", ".join(details.genres),
        "Web": chapter.document_location,
    }
    root = ET.Element("ComicInfo")
    for tag, value in fields.items():
        if value:
            ET.SubElement(root, tag).text = _XML_ILLEGAL.sub("", value)
    ET.indent(root)
    return ET.tostring(root, encoding="utf-8", xml_declaration=True)
