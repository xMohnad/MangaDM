from pathlib import Path

ROOT = Path(__file__).parent

def image_error() -> bytes:
    return (ROOT / "not_available_error.webp").read_bytes()
