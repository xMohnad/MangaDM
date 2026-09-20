from __future__ import annotations

from typing import TYPE_CHECKING, Final

if TYPE_CHECKING:
    from pathlib import Path

DEFAULT_EXTENSION: Final = "jpg"
HEAD_SIZE: Final = 32

MEDIA_TYPES: Final[dict[str, str]] = {
    "jpg": "image/jpeg",
    "png": "image/png",
    "gif": "image/gif",
    "webp": "image/webp",
    "avif": "image/avif",
    "jxl": "image/jxl",
}
_EXTENSIONS: Final[dict[str, str]] = {v: k for k, v in MEDIA_TYPES.items()} | {"image/jpg": "jpg"}


def sniff_extension(head: bytes) -> str | None:
    """Return the image extension matching the file signature, if known."""
    if head.startswith(b"\xff\xd8\xff"):
        return "jpg"
    if head.startswith(b"\x89PNG\r\n\x1a\n"):
        return "png"
    if head.startswith((b"GIF87a", b"GIF89a")):
        return "gif"
    if head[:4] == b"RIFF" and head[8:12] == b"WEBP":
        return "webp"
    if head[4:8] == b"ftyp" and head[8:12] in {b"avif", b"avis"}:
        return "avif"
    if head.startswith((b"\xff\x0a", b"\x00\x00\x00\x0cJXL ")):
        return "jxl"
    return None


def detect_extension(head: bytes, content_type: str | None = None) -> str:
    """Detect the extension from file signature, then MIME type, then fall back to jpg."""
    mime = (content_type or "").split(";")[0].strip().lower()
    return sniff_extension(head) or _EXTENSIONS.get(mime) or DEFAULT_EXTENSION


def media_type(path: Path) -> str:
    """Return the MIME type for an image path."""
    return MEDIA_TYPES.get(path.suffix.lstrip(".").lower(), "application/octet-stream")
