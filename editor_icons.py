"""Toolbar icons for the FissileKit image editor (Lucide-style, ISC-compatible shapes)."""

from __future__ import annotations

import sys
from pathlib import Path

from PIL import Image, ImageDraw

_ICON_CACHE: dict[tuple[str, int, str], Image.Image] = {}


def _icons_dir() -> Path:
    if getattr(sys, "frozen", False):
        bundled = Path(sys._MEIPASS) / "assets" / "editor_icons"
        if bundled.is_dir():
            return bundled
    return Path(__file__).resolve().parent / "assets" / "editor_icons"


def _blank(size: int) -> Image.Image:
    return Image.new("RGBA", (size, size), (0, 0, 0, 0))


def _draw_crop(draw: ImageDraw.ImageDraw, size: int, color: tuple[int, int, int, int]) -> None:
    pad = size * 0.18
    x0, y0 = pad, pad
    x1, y1 = size - pad, size - pad
    w = max(2, size // 16)
    draw.rectangle([x0, y0, x1, y1], outline=color, width=w)
    handle = size * 0.14
    for cx, cy in ((x0, y0), (x1, y0), (x0, y1), (x1, y1)):
        draw.rectangle([cx - handle / 2, cy - handle / 2, cx + handle / 2, cy + handle / 2], fill=color)


def _draw_rotate(draw: ImageDraw.ImageDraw, size: int, color: tuple[int, int, int, int]) -> None:
    pad = size * 0.2
    draw.arc([pad, pad, size - pad, size - pad], start=45, end=300, fill=color, width=max(2, size // 14))
    tip_x = size * 0.72
    tip_y = size * 0.24
    draw.polygon(
        [
            (tip_x, tip_y - size * 0.12),
            (tip_x + size * 0.14, tip_y + size * 0.02),
            (tip_x - size * 0.02, tip_y + size * 0.12),
        ],
        fill=color,
    )


def _draw_resize(draw: ImageDraw.ImageDraw, size: int, color: tuple[int, int, int, int]) -> None:
    pad = size * 0.22
    w = max(2, size // 16)
    draw.line([(pad, size - pad), (size - pad, pad)], fill=color, width=w)
    draw.polygon(
        [
            (size - pad, pad - size * 0.1),
            (size - pad + size * 0.12, pad + size * 0.02),
            (size - pad - size * 0.02, pad + size * 0.12),
        ],
        fill=color,
    )
    draw.polygon(
        [
            (pad, size - pad + size * 0.1),
            (pad - size * 0.12, size - pad - size * 0.02),
            (pad + size * 0.02, size - pad - size * 0.12),
        ],
        fill=color,
    )


def _draw_pencil(draw: ImageDraw.ImageDraw, size: int, color: tuple[int, int, int, int]) -> None:
    w = max(2, size // 12)
    draw.line([(size * 0.18, size * 0.82), (size * 0.78, size * 0.22)], fill=color, width=w)
    draw.polygon(
        [
            (size * 0.78, size * 0.22),
            (size * 0.88, size * 0.32),
            (size * 0.28, size * 0.92),
            (size * 0.18, size * 0.82),
        ],
        fill=color,
    )


def _draw_bucket(draw: ImageDraw.ImageDraw, size: int, color: tuple[int, int, int, int]) -> None:
    w = max(2, size // 14)
    draw.polygon(
        [
            (size * 0.28, size * 0.34),
            (size * 0.72, size * 0.34),
            (size * 0.66, size * 0.62),
            (size * 0.34, size * 0.62),
        ],
        outline=color,
        width=w,
    )
    draw.line([(size * 0.22, size * 0.34), (size * 0.78, size * 0.34)], fill=color, width=w)
    draw.polygon(
        [(size * 0.36, size * 0.72), (size * 0.64, size * 0.72), (size * 0.58, size * 0.88), (size * 0.42, size * 0.88)],
        fill=color,
    )


def _draw_eraser(draw: ImageDraw.ImageDraw, size: int, color: tuple[int, int, int, int]) -> None:
    draw.polygon(
        [
            (size * 0.22, size * 0.58),
            (size * 0.48, size * 0.28),
            (size * 0.82, size * 0.52),
            (size * 0.56, size * 0.82),
        ],
        fill=color,
    )
    draw.line([(size * 0.18, size * 0.62), (size * 0.82, size * 0.62)], fill=(0, 0, 0, 180), width=max(1, size // 18))


def _draw_shape(draw: ImageDraw.ImageDraw, size: int, color: tuple[int, int, int, int]) -> None:
    pad = size * 0.22
    w = max(2, size // 14)
    draw.rectangle([pad, pad, size - pad, size - pad], outline=color, width=w)


def _draw_text(draw: ImageDraw.ImageDraw, size: int, color: tuple[int, int, int, int]) -> None:
    w = max(2, size // 14)
    draw.line([(size * 0.28, size * 0.26), (size * 0.72, size * 0.26)], fill=color, width=w)
    draw.line([(size * 0.5, size * 0.26), (size * 0.5, size * 0.78)], fill=color, width=w)
    draw.line([(size * 0.34, size * 0.78), (size * 0.66, size * 0.78)], fill=color, width=w)


def _draw_undo(draw: ImageDraw.ImageDraw, size: int, color: tuple[int, int, int, int]) -> None:
    w = max(2, size // 14)
    draw.arc([size * 0.18, size * 0.28, size * 0.82, size * 0.82], start=200, end=340, fill=color, width=w)
    draw.polygon(
        [
            (size * 0.22, size * 0.46),
            (size * 0.36, size * 0.34),
            (size * 0.36, size * 0.58),
        ],
        fill=color,
    )


def _draw_redo(draw: ImageDraw.ImageDraw, size: int, color: tuple[int, int, int, int]) -> None:
    w = max(2, size // 14)
    draw.arc([size * 0.18, size * 0.28, size * 0.82, size * 0.82], start=20, end=160, fill=color, width=w)
    draw.polygon(
        [
            (size * 0.78, size * 0.46),
            (size * 0.64, size * 0.34),
            (size * 0.64, size * 0.58),
        ],
        fill=color,
    )


def _draw_exit(draw: ImageDraw.ImageDraw, size: int, color: tuple[int, int, int, int]) -> None:
    w = max(2, size // 12)
    pad = size * 0.28
    draw.line([(pad, pad), (size - pad, size - pad)], fill=color, width=w)
    draw.line([(size - pad, pad), (pad, size - pad)], fill=color, width=w)


def _draw_save(draw: ImageDraw.ImageDraw, size: int, color: tuple[int, int, int, int]) -> None:
    w = max(2, size // 14)
    body = [size * 0.22, size * 0.18, size * 0.78, size * 0.82]
    draw.rectangle(body, outline=color, width=w)
    draw.rectangle([size * 0.36, size * 0.18, size * 0.64, size * 0.36], fill=color)
    draw.rectangle([size * 0.34, size * 0.48, size * 0.66, size * 0.78], outline=color, width=w)


_DRAWERS = {
    "crop": _draw_crop,
    "rotate": _draw_rotate,
    "resize": _draw_resize,
    "draw": _draw_pencil,
    "pencil": _draw_pencil,
    "bucket": _draw_bucket,
    "eraser": _draw_eraser,
    "shape": _draw_shape,
    "text": _draw_text,
    "undo": _draw_undo,
    "redo": _draw_redo,
    "exit": _draw_exit,
    "save": _draw_save,
}


def _load_png(name: str, size: int) -> Image.Image | None:
    path = _icons_dir() / f"{name}.png"
    if not path.is_file():
        return None
    with Image.open(path) as icon:
        icon_rgba = icon.convert("RGBA")
    icon_rgba.thumbnail((size, size), Image.Resampling.LANCZOS)
    return icon_rgba


def render_icon(name: str, size: int = 22, color: str = "#e6e6e6") -> Image.Image:
    cache_key = (name, size, color)
    cached = _ICON_CACHE.get(cache_key)
    if cached is not None:
        return cached.copy()

    png = _load_png(name, size)
    if png is not None:
        _ICON_CACHE[cache_key] = png.copy()
        return png

    cleaned = color.lstrip("#")
    if len(cleaned) == 3:
        cleaned = "".join(ch * 2 for ch in cleaned)
    rgba = (
        int(cleaned[0:2], 16),
        int(cleaned[2:4], 16),
        int(cleaned[4:6], 16),
        255,
    )
    image = _blank(size)
    drawer = _DRAWERS.get(name)
    if drawer is not None:
        drawer(ImageDraw.Draw(image), size, rgba)
    _ICON_CACHE[cache_key] = image.copy()
    return image
