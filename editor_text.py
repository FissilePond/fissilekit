"""Text objects, fonts, and rendering for the image editor."""

from __future__ import annotations

import math
import sys
import uuid
from dataclasses import dataclass, field
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

import editor_ops

FONT_DIR = Path("C:/Windows/Fonts") if sys.platform == "win32" else Path("/usr/share/fonts/truetype")

FONT_CATALOG: list[tuple[str, dict[str, str]]] = [
    ("Arial", {"regular": "arial.ttf", "bold": "arialbd.ttf", "italic": "ariali.ttf", "bold_italic": "arialbi.ttf"}),
    ("Calibri", {"regular": "calibri.ttf", "bold": "calibrib.ttf", "italic": "calibrii.ttf", "bold_italic": "calibriz.ttf"}),
    ("Segoe UI", {"regular": "segoeui.ttf", "bold": "segoeuib.ttf", "italic": "segoeuii.ttf", "bold_italic": "segoeuiz.ttf"}),
    ("Times New Roman", {"regular": "times.ttf", "bold": "timesbd.ttf", "italic": "timesi.ttf", "bold_italic": "timesbi.ttf"}),
    ("Courier New", {"regular": "cour.ttf", "bold": "courbd.ttf", "italic": "couri.ttf", "bold_italic": "courbi.ttf"}),
    ("Georgia", {"regular": "georgia.ttf", "bold": "georgiab.ttf", "italic": "georgiai.ttf", "bold_italic": "georgiaz.ttf"}),
    ("Verdana", {"regular": "verdana.ttf", "bold": "verdanab.ttf", "italic": "verdanai.ttf", "bold_italic": "verdanaz.ttf"}),
    ("Trebuchet MS", {"regular": "trebuc.ttf", "bold": "trebucbd.ttf", "italic": "trebucit.ttf", "bold_italic": "trebucbi.ttf"}),
    ("Comic Sans MS", {"regular": "comic.ttf", "bold": "comicbd.ttf", "italic": "comic.ttf", "bold_italic": "comicbd.ttf"}),
    ("Impact", {"regular": "impact.ttf", "bold": "impact.ttf", "italic": "impact.ttf", "bold_italic": "impact.ttf"}),
]

DEFAULT_FONT_FAMILY = FONT_CATALOG[0][0]
DEFAULT_FONT_SIZE = 36.0
MIN_FONT_SIZE = 24.0
HANDLE_HIT_RADIUS = 8.0
TEXT_HANDLE_CURSORS = {
    "nw": "size_nw_se",
    "se": "size_nw_se",
    "ne": "size_ne_sw",
    "sw": "size_ne_sw",
}


@dataclass
class TextObject:
    id: str = field(default_factory=lambda: uuid.uuid4().hex)
    x: float = 0.0
    y: float = 0.0
    text: str = ""
    font_family: str = DEFAULT_FONT_FAMILY
    font_size: float = DEFAULT_FONT_SIZE
    color: str = "#ffffff"
    bold: bool = False
    italic: bool = False
    underline: bool = False
    strikethrough: bool = False
    border_enabled: bool = False
    border_color: str = "#000000"
    border_width: int = 2

    def copy(self) -> TextObject:
        return TextObject(
            id=self.id,
            x=self.x,
            y=self.y,
            text=self.text,
            font_family=self.font_family,
            font_size=self.font_size,
            color=self.color,
            bold=self.bold,
            italic=self.italic,
            underline=self.underline,
            strikethrough=self.strikethrough,
            border_enabled=self.border_enabled,
            border_color=self.border_color,
            border_width=self.border_width,
        )


def list_font_families() -> list[str]:
    available: list[str] = []
    for family, variants in FONT_CATALOG:
        regular = variants.get("regular", "")
        if regular and (FONT_DIR / regular).is_file():
            available.append(family)
    return available or [DEFAULT_FONT_FAMILY]


def _font_variant_key(bold: bool, italic: bool) -> str:
    if bold and italic:
        return "bold_italic"
    if bold:
        return "bold"
    if italic:
        return "italic"
    return "regular"


def _resolve_font_path(family: str, bold: bool, italic: bool) -> Path | None:
    lookup = {name: files for name, files in FONT_CATALOG}
    files = lookup.get(family)
    if files is None:
        files = FONT_CATALOG[0][1]
    key = _font_variant_key(bold, italic)
    filename = files.get(key) or files.get("regular")
    if not filename:
        return None
    path = FONT_DIR / filename
    if path.is_file():
        return path
    fallback = FONT_DIR / files.get("regular", "")
    return fallback if fallback.is_file() else None


def load_font(family: str, size: float, bold: bool = False, italic: bool = False) -> ImageFont.FreeTypeFont | ImageFont.ImageFont:
    size = max(int(MIN_FONT_SIZE), int(round(size)))
    path = _resolve_font_path(family, bold, italic)
    if path is not None:
        try:
            return ImageFont.truetype(str(path), size=size)
        except OSError:
            pass
    try:
        return ImageFont.truetype("arial.ttf", size=size)
    except OSError:
        return ImageFont.load_default()


def tk_font_tuple(obj: TextObject, scale: float = 1.0) -> tuple:
    size = max(int(MIN_FONT_SIZE), int(round(obj.font_size * scale)))
    style_parts: list[str] = []
    if obj.bold:
        style_parts.append("bold")
    if obj.italic:
        style_parts.append("italic")
    if obj.underline:
        style_parts.append("underline")
    if obj.strikethrough:
        style_parts.append("overstrike")
    if style_parts:
        return (obj.font_family, size, " ".join(style_parts))
    return (obj.font_family, size)


def measure_text_object(obj: TextObject) -> tuple[float, float, float, float]:
    sample = obj.text if obj.text else "M"
    font = load_font(obj.font_family, obj.font_size, obj.bold, obj.italic)
    left, top, right, bottom = font.getbbox(sample)
    return obj.x + left, obj.y + top, obj.x + right, obj.y + bottom


def copy_text_objects(objects: list[TextObject]) -> list[TextObject]:
    return [item.copy() for item in objects]


def find_object_at(objects: list[TextObject], x: float, y: float) -> TextObject | None:
    for obj in reversed(objects):
        x0, y0, x1, y1 = measure_text_object(obj)
        pad = 6.0
        if x0 - pad <= x <= x1 + pad and y0 - pad <= y <= y1 + pad:
            return obj
    return None


def hit_text_handle(
    obj: TextObject,
    x: float,
    y: float,
) -> str | None:
    x0, y0, x1, y1 = measure_text_object(obj)
    handles = {
        "nw": (x0, y0),
        "ne": (x1, y0),
        "sw": (x0, y1),
        "se": (x1, y1),
    }
    for name, (hx, hy) in handles.items():
        if math.hypot(x - hx, y - hy) <= HANDLE_HIT_RADIUS:
            return name
    return None


def _draw_decorations(
    draw: ImageDraw.ImageDraw,
    obj: TextObject,
    x: float,
    y: float,
    width: float,
    height: float,
    fill_rgba: tuple[int, int, int, int],
) -> None:
    line_w = max(1, int(round(obj.font_size / 14)))
    if obj.underline:
        uy = y + height
        draw.line([(x, uy), (x + width, uy)], fill=fill_rgba, width=line_w)
    if obj.strikethrough:
        sy = y + height / 2
        draw.line([(x, sy), (x + width, sy)], fill=fill_rgba, width=line_w)


def render_text_object(draw: ImageDraw.ImageDraw, obj: TextObject) -> None:
    if not obj.text:
        return
    font = load_font(obj.font_family, obj.font_size, obj.bold, obj.italic)
    fill = editor_ops.hex_to_rgba(obj.color, 100)
    stroke_w = max(1, int(obj.border_width)) if obj.border_enabled else 0
    stroke_fill = editor_ops.hex_to_rgba(obj.border_color, 100) if obj.border_enabled else None
    draw.text(
        (obj.x, obj.y),
        obj.text,
        font=font,
        fill=fill,
        stroke_width=stroke_w,
        stroke_fill=stroke_fill,
        anchor="lt",
    )
    bbox = font.getbbox(obj.text)
    left, top, right, bottom = bbox
    abs_x = obj.x + left
    abs_y = obj.y + top
    width = max(1.0, right - left)
    height = max(1.0, bottom - top)
    _draw_decorations(draw, obj, abs_x, abs_y, width, height, fill)


def render_text_layer(
    objects: list[TextObject],
    size: tuple[int, int],
    *,
    exclude_ids: set[str] | None = None,
) -> Image.Image | None:
    if not objects:
        return None
    skip = exclude_ids or set()
    layer = Image.new("RGBA", size, (0, 0, 0, 0))
    draw = ImageDraw.Draw(layer)
    rendered = False
    for obj in objects:
        if obj.id in skip or not obj.text:
            continue
        render_text_object(draw, obj)
        rendered = True
    return layer if rendered else None


def new_text_object(x: float, y: float, **kwargs) -> TextObject:
    return TextObject(x=x, y=y, **kwargs)


def offset_text_objects(objects: list[TextObject], dx: float, dy: float) -> None:
    for obj in objects:
        obj.x += dx
        obj.y += dy


def crop_text_objects(objects: list[TextObject], left: int, top: int) -> list[TextObject]:
    kept: list[TextObject] = []
    for obj in objects:
        obj.x -= left
        obj.y -= top
        x0, y0, x1, y1 = measure_text_object(obj)
        if x1 >= 0 and y1 >= 0:
            kept.append(obj)
    return kept


def scale_text_objects(
    objects: list[TextObject],
    scale_x: float,
    scale_y: float,
) -> None:
    uniform = (scale_x + scale_y) / 2
    for obj in objects:
        obj.x *= scale_x
        obj.y *= scale_y
        obj.font_size = max(MIN_FONT_SIZE, obj.font_size * uniform)


def flip_text_objects_horizontal(objects: list[TextObject], image_width: int) -> None:
    for obj in objects:
        x0, _y0, x1, _y1 = measure_text_object(obj)
        center = (x0 + x1) / 2
        obj.x = image_width - center - (x1 - x0) / 2


def flip_text_objects_vertical(objects: list[TextObject], image_height: int) -> None:
    for obj in objects:
        _x0, y0, _x1, y1 = measure_text_object(obj)
        center = (y0 + y1) / 2
        obj.y = image_height - center - (y1 - y0) / 2


def rotate_text_objects(
    objects: list[TextObject],
    image_width: int,
    image_height: int,
    degrees: float,
) -> None:
    if abs(degrees) < 0.01:
        return
    radians = math.radians(degrees)
    cos_a = math.cos(radians)
    sin_a = math.sin(radians)
    cx = image_width / 2
    cy = image_height / 2
    for obj in objects:
        x0, y0, x1, y1 = measure_text_object(obj)
        center_x = (x0 + x1) / 2
        center_y = (y0 + y1) / 2
        dx = center_x - cx
        dy = center_y - cy
        rotated_x = cx + dx * cos_a - dy * sin_a
        rotated_y = cy + dx * sin_a + dy * cos_a
        obj.x += rotated_x - center_x
        obj.y += rotated_y - center_y
