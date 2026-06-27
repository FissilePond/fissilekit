"""Toolbar icons for the FissileKit image editor (Lucide-style, ISC-compatible shapes)."""

from __future__ import annotations

import math
import sys
from pathlib import Path

from PIL import Image, ImageDraw

_ICON_CACHE: dict[tuple[str, int, str], Image.Image] = {}


def _icons_dir() -> Path:
    if getattr(sys, "frozen", False):
        bundled = Path(sys._MEIPASS) / "assets" / "editor_icons"
        if bundled.is_dir():
            return bundled
    project = Path(__file__).resolve().parent
    bundled = project / "assets" / "editor_icons"
    if bundled.is_dir():
        return bundled
    return project / "logos para las herramientas"


def _parse_hex(color: str) -> tuple[int, int, int]:
    cleaned = color.lstrip("#")
    if len(cleaned) == 3:
        cleaned = "".join(ch * 2 for ch in cleaned)
    return (
        int(cleaned[0:2], 16),
        int(cleaned[2:4], 16),
        int(cleaned[4:6], 16),
    )


def _tint_icon(icon: Image.Image, color: str) -> Image.Image:
    icon = icon.convert("RGBA")
    red, green, blue = _parse_hex(color)
    _red, _green, _blue, alpha = icon.split()
    return Image.merge(
        "RGBA",
        (
            Image.new("L", icon.size, red),
            Image.new("L", icon.size, green),
            Image.new("L", icon.size, blue),
            alpha,
        ),
    )


_PNG_ALIASES = {
    "pencil": "draw",
    "bucket": "fill",
    "eyedropper": "dropper",
}

_ICON_PADDING = {
    "shape": 0.05,
    "text": 0.08,
    "rotate_left": 0.14,
    "rotate_right": 0.14,
    "rotate": 0.08,
    "eyedropper": 0.08,
    "bucket": 0.08,
    "undo": 0.06,
    "redo": 0.06,
}


def clear_icon_cache() -> None:
    _ICON_CACHE.clear()


def tint_image(icon: Image.Image, color: str) -> Image.Image:
    return _tint_icon(icon, color)


def _trim_icon(icon: Image.Image) -> Image.Image:
    bbox = icon.getbbox()
    if bbox:
        return icon.crop(bbox)
    return icon


def _fit_icon(icon: Image.Image, size: int, padding: float = 0.1) -> Image.Image:
    icon = _trim_icon(icon.convert("RGBA"))
    padding = max(0.02, min(0.22, padding))
    inner = max(8, int(size * (1 - padding * 2)))
    ratio = min(inner / max(icon.width, 1), inner / max(icon.height, 1))
    target_w = max(1, int(icon.width * ratio))
    target_h = max(1, int(icon.height * ratio))
    render_w = max(target_w * 3, target_w)
    render_h = max(target_h * 3, target_h)
    upscaled = icon.resize((render_w, render_h), Image.Resampling.LANCZOS)
    sharp = upscaled.resize((target_w, target_h), Image.Resampling.LANCZOS)
    canvas = _blank(size)
    offset_x = (size - sharp.width) // 2
    offset_y = (size - sharp.height) // 2
    canvas.paste(sharp, (offset_x, offset_y), sharp)
    return canvas


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


def _draw_rotate_left(draw: ImageDraw.ImageDraw, size: int, color: tuple[int, int, int, int]) -> None:
    w = max(2, size // 14)
    draw.arc([size * 0.18, size * 0.18, size * 0.82, size * 0.82], start=200, end=340, fill=color, width=w)
    draw.polygon(
        [
            (size * 0.22, size * 0.42),
            (size * 0.36, size * 0.30),
            (size * 0.36, size * 0.54),
        ],
        fill=color,
    )


def _draw_rotate_right(draw: ImageDraw.ImageDraw, size: int, color: tuple[int, int, int, int]) -> None:
    w = max(2, size // 14)
    draw.arc([size * 0.18, size * 0.18, size * 0.82, size * 0.82], start=20, end=160, fill=color, width=w)
    draw.polygon(
        [
            (size * 0.78, size * 0.42),
            (size * 0.64, size * 0.30),
            (size * 0.64, size * 0.54),
        ],
        fill=color,
    )


def _draw_flip_h(draw: ImageDraw.ImageDraw, size: int, color: tuple[int, int, int, int]) -> None:
    w = max(2, size // 14)
    mid = size / 2
    draw.rectangle([size * 0.2, size * 0.26, size * 0.8, size * 0.74], outline=color, width=w)
    draw.polygon([(size * 0.34, mid), (size * 0.24, size * 0.38), (size * 0.24, size * 0.62)], fill=color)
    draw.polygon([(size * 0.66, mid), (size * 0.76, size * 0.38), (size * 0.76, size * 0.62)], fill=color)
    draw.line([(mid, size * 0.22), (mid, size * 0.78)], fill=color, width=max(1, w // 2))


def _draw_flip_v(draw: ImageDraw.ImageDraw, size: int, color: tuple[int, int, int, int]) -> None:
    w = max(2, size // 14)
    mid = size / 2
    draw.rectangle([size * 0.26, size * 0.2, size * 0.74, size * 0.8], outline=color, width=w)
    draw.polygon([(mid, size * 0.34), (size * 0.38, size * 0.24), (size * 0.62, size * 0.24)], fill=color)
    draw.polygon([(mid, size * 0.66), (size * 0.38, size * 0.76), (size * 0.62, size * 0.76)], fill=color)
    draw.line([(size * 0.22, mid), (size * 0.78, mid)], fill=color, width=max(1, w // 2))


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


def _draw_eyedropper(draw: ImageDraw.ImageDraw, size: int, color: tuple[int, int, int, int]) -> None:
    w = max(2, size // 12)
    draw.line([(size * 0.78, size * 0.18), (size * 0.3, size * 0.66)], fill=color, width=w)
    draw.polygon(
        [
            (size * 0.24, size * 0.7),
            (size * 0.34, size * 0.8),
            (size * 0.2, size * 0.84),
        ],
        fill=color,
    )
    draw.ellipse([size * 0.58, size * 0.12, size * 0.84, size * 0.38], outline=color, width=max(1, w // 2))


def _draw_shape(draw: ImageDraw.ImageDraw, size: int, color: tuple[int, int, int, int]) -> None:
    pad = size * 0.22
    w = max(2, size // 14)
    draw.rectangle([pad, pad, size - pad, size - pad], outline=color, width=w)


def _draw_shape_line(draw: ImageDraw.ImageDraw, size: int, color: tuple[int, int, int, int]) -> None:
    w = max(2, size // 12)
    draw.line([(size * 0.18, size * 0.82), (size * 0.82, size * 0.18)], fill=color, width=w)


def _draw_shape_curve(draw: ImageDraw.ImageDraw, size: int, color: tuple[int, int, int, int]) -> None:
    w = max(2, size // 12)
    draw.line([(size * 0.16, size * 0.72), (size * 0.42, size * 0.24), (size * 0.84, size * 0.62)], fill=color, width=w)


def _draw_shape_rect(draw: ImageDraw.ImageDraw, size: int, color: tuple[int, int, int, int]) -> None:
    pad = size * 0.22
    w = max(2, size // 14)
    draw.rectangle([pad, pad, size - pad, size - pad], outline=color, width=w)


def _draw_shape_circle(draw: ImageDraw.ImageDraw, size: int, color: tuple[int, int, int, int]) -> None:
    pad = size * 0.2
    w = max(2, size // 14)
    draw.ellipse([pad, pad, size - pad, size - pad], outline=color, width=w)


def _draw_shape_oval(draw: ImageDraw.ImageDraw, size: int, color: tuple[int, int, int, int]) -> None:
    pad_x = size * 0.14
    pad_y = size * 0.26
    w = max(2, size // 14)
    draw.ellipse([pad_x, pad_y, size - pad_x, size - pad_y], outline=color, width=w)


def _draw_shape_star(draw: ImageDraw.ImageDraw, size: int, color: tuple[int, int, int, int]) -> None:
    w = max(2, size // 14)
    cx, cy = size * 0.5, size * 0.52
    points = []
    outer = size * 0.34
    inner = outer * 0.4
    for index in range(10):
        angle = -math.pi / 2 + (math.pi * index / 5)
        radius = outer if index % 2 == 0 else inner
        points.append((cx + radius * math.cos(angle), cy + radius * math.sin(angle)))
    draw.polygon(points, outline=color, width=w)


def _draw_shape_triangle(draw: ImageDraw.ImageDraw, size: int, color: tuple[int, int, int, int]) -> None:
    w = max(2, size // 14)
    draw.polygon(
        [(size * 0.5, size * 0.18), (size * 0.82, size * 0.78), (size * 0.18, size * 0.78)],
        outline=color,
        width=w,
    )


def _draw_shape_pentagon(draw: ImageDraw.ImageDraw, size: int, color: tuple[int, int, int, int]) -> None:
    w = max(2, size // 14)
    cx, cy, r = size * 0.5, size * 0.52, size * 0.3
    points = []
    for index in range(5):
        angle = -math.pi / 2 + (2 * math.pi * index / 5)
        points.append((cx + r * math.cos(angle), cy + r * math.sin(angle)))
    draw.polygon(points, outline=color, width=w)


def _draw_shape_hexagon(draw: ImageDraw.ImageDraw, size: int, color: tuple[int, int, int, int]) -> None:
    w = max(2, size // 14)
    cx, cy, r = size * 0.5, size * 0.52, size * 0.3
    points = []
    for index in range(6):
        angle = -math.pi / 2 + (2 * math.pi * index / 6)
        points.append((cx + r * math.cos(angle), cy + r * math.sin(angle)))
    draw.polygon(points, outline=color, width=w)


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
    "rotate_left": _draw_rotate_left,
    "rotate_right": _draw_rotate_right,
    "flip_h": _draw_flip_h,
    "flip_v": _draw_flip_v,
    "resize": _draw_resize,
    "draw": _draw_pencil,
    "pencil": _draw_pencil,
    "bucket": _draw_bucket,
    "eyedropper": _draw_eyedropper,
    "eraser": _draw_eraser,
    "shape": _draw_shape,
    "shape_line": _draw_shape_line,
    "shape_curve": _draw_shape_curve,
    "shape_rect": _draw_shape_rect,
    "shape_oval": _draw_shape_oval,
    "shape_circle": _draw_shape_circle,
    "shape_triangle": _draw_shape_triangle,
    "shape_pentagon": _draw_shape_pentagon,
    "shape_hexagon": _draw_shape_hexagon,
    "shape_star": _draw_shape_star,
    "text": _draw_text,
    "undo": _draw_undo,
    "redo": _draw_redo,
    "exit": _draw_exit,
    "save": _draw_save,
}


def _load_png(name: str, size: int, color: str) -> Image.Image | None:
    lookup = _PNG_ALIASES.get(name, name)
    path = _icons_dir() / f"{lookup}.png"
    if not path.is_file():
        legacy = _icons_dir() / f"{name}.png"
        if legacy.is_file():
            path = legacy
        else:
            return None
    with Image.open(path) as icon:
        icon_rgba = icon.convert("RGBA")
    padding = _ICON_PADDING.get(name, _ICON_PADDING.get(lookup, 0.1))
    fitted = _fit_icon(icon_rgba, size, padding=padding)
    return _tint_icon(fitted, color)


def render_icon(name: str, size: int = 22, color: str = "#e6e6e6") -> Image.Image:
    cache_key = (name, size, color)
    cached = _ICON_CACHE.get(cache_key)
    if cached is not None:
        return cached.copy()

    png = _load_png(name, size, color)
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
