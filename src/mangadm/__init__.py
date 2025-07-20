from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from typing import Any

    from .components.types import FormatType as FormatTypeType
    from .core.mangadm import MangaDM as MangaDMType

MangaDM: "type[MangaDMType]"
FormatType: "type[FormatTypeType]"

__version__ = "0.6.0"
__all__ = ["MangaDM", "FormatType"]


def __getattr__(name: str) -> "Any":
    if name == "MangaDM":
        from .core.mangadm import MangaDM

        return MangaDM
    if name == "FormatType":
        from .components.types import FormatType

        return FormatType
    raise AttributeError(f"module '{__name__}' has no attribute '{name}'")
