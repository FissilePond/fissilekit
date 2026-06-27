"""Shared UI typography for the desktop app."""
import tkinter as tk
import tkinter.font as tkfont

_PREFERRED_FAMILIES = (
    "Segoe UI Variable Text",
    "Segoe UI Variable",
    "Calibri",
    "Segoe UI",
    "Cascadia UI",
    "Tahoma",
)


def resolve_ui_font_family(root: tk.Misc | None = None) -> str:
    owns_root = root is None
    if owns_root:
        root = tk.Tk()
        root.withdraw()
    try:
        families = set(tkfont.families(root))
        for name in _PREFERRED_FAMILIES:
            if name in families:
                return name
    finally:
        if owns_root:
            root.destroy()
    return "TkDefaultFont"


def font_tuple(family: str, size: int, *styles: str) -> tuple:
    if styles:
        return (family, size, *styles)
    return (family, size)


def configure_ui_fonts(root: tk.Misc) -> dict[str, tuple]:
    family = resolve_ui_font_family(root)
    fonts = {
        "family": family,
        "normal": font_tuple(family, 10),
        "bold": font_tuple(family, 10, "bold"),
        "title": font_tuple(family, 12, "bold"),
        "small": font_tuple(family, 9),
        "caption": font_tuple(family, 8),
        "section": font_tuple(family, 11),
        "hero": font_tuple(family, 13, "bold"),
    }
    return fonts
