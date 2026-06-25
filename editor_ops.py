"""Advanced image operations for the FissileKit editor."""

from __future__ import annotations

import math
from collections import deque

import numpy as np
from PIL import Image, ImageChops, ImageDraw

RESIZE_PRESETS = {
    "baja": 640,
    "media": 1280,
    "alta": 1920,
}

CROP_ASPECTS = {
    "free": None,
    "1:1": 1.0,
    "9:16": 9 / 16,
    "16:9": 16 / 9,
}


def clamp_crop_box(
    box: tuple[float, float, float, float],
    width: int,
    height: int,
) -> tuple[int, int, int, int]:
    x0, y0, x1, y1 = box
    left, right = sorted((x0, x1))
    top, bottom = sorted((y0, y1))
    left = max(0, min(int(round(left)), width - 1))
    top = max(0, min(int(round(top)), height - 1))
    right = max(left + 1, min(int(round(right)), width))
    bottom = max(top + 1, min(int(round(bottom)), height))
    return left, top, right, bottom


def initial_crop_box(width: int, height: int, margin: float = 0.08) -> tuple[int, int, int, int]:
    mx = max(1, int(width * margin))
    my = max(1, int(height * margin))
    return mx, my, max(mx + 1, width - mx), max(my + 1, height - my)


def full_image_crop_box(width: int, height: int) -> tuple[int, int, int, int]:
    return 0, 0, width, height


def fit_crop_box_to_aspect(
    box: tuple[int, int, int, int],
    aspect: float | None,
    image_width: int,
    image_height: int,
) -> tuple[int, int, int, int]:
    if aspect is None or aspect <= 0:
        return box
    left, top, right, bottom = box
    center_x = (left + right) / 2
    center_y = (top + bottom) / 2
    width = max(1.0, float(right - left))
    height = max(1.0, float(bottom - top))
    current = width / height
    if current > aspect:
        width = height * aspect
    else:
        height = width / aspect
    left = center_x - width / 2
    right = center_x + width / 2
    top = center_y - height / 2
    bottom = center_y + height / 2
    return clamp_crop_box((left, top, right, bottom), image_width, image_height)


def darken_outside_box(
    image: Image.Image,
    box: tuple[int, int, int, int],
    strength: float = 0.52,
) -> Image.Image:
    """Oscurece fuera del recorte para previsualizacion (la imagen completa sigue visible)."""
    result = image.convert("RGBA").copy()
    left, top, right, bottom = box
    width, height = result.size
    left = max(0, min(int(left), width))
    top = max(0, min(int(top), height))
    right = max(left, min(int(right), width))
    bottom = max(top, min(int(bottom), height))
    shade = Image.new("RGBA", (width, height), (0, 0, 0, int(255 * strength)))
    mask = Image.new("L", (width, height), 255)
    if right > left and bottom > top:
        draw = ImageDraw.Draw(mask)
        draw.rectangle([left, top, right - 1, bottom - 1], fill=0)
    return Image.alpha_composite(result, Image.composite(shade, Image.new("RGBA", (width, height), (0, 0, 0, 0)), mask))


CORNER_HANDLES = frozenset({"tl", "tr", "bl", "br"})
EDGE_HANDLES = frozenset({"tm", "bm", "ml", "mr"})


def _fit_aspect_within(
    w: float,
    h: float,
    aspect: float,
    max_w: float,
    max_h: float,
    min_size: float = 4.0,
) -> tuple[float, float]:
    w = max(min_size, w)
    h = max(min_size, h)
    if w / h > aspect:
        w = h * aspect
    else:
        h = w / aspect
    if w > max_w:
        w = max(min_size, max_w)
        h = w / aspect
    if h > max_h:
        h = max(min_size, max_h)
        w = h * aspect
    if w > max_w:
        w = max(min_size, max_w)
        h = min(h, w / aspect)
    if h > max_h:
        h = max(min_size, max_h)
        w = min(w, h * aspect)
    return max(min_size, w), max(min_size, h)


def _anchor_max_size(anchor: str, ax: float, ay: float, image_width: int, image_height: int) -> tuple[float, float]:
    if anchor == "tl":
        return float(image_width) - ax, float(image_height) - ay
    if anchor == "tr":
        return ax, float(image_height) - ay
    if anchor == "bl":
        return float(image_width) - ax, ay
    return ax, ay


def _box_from_anchor(anchor: str, ax: float, ay: float, w: float, h: float) -> tuple[float, float, float, float]:
    if anchor == "tl":
        return ax, ay, ax + w, ay + h
    if anchor == "tr":
        return ax - w, ay, ax, ay + h
    if anchor == "bl":
        return ax, ay - h, ax + w, ay
    return ax - w, ay - h, ax, ay


def clamp_crop_preserve_aspect_at_anchor(
    anchor: str,
    ax: float,
    ay: float,
    w: float,
    h: float,
    aspect: float,
    image_width: int,
    image_height: int,
) -> tuple[int, int, int, int]:
    ax = max(0.0, min(ax, float(image_width)))
    ay = max(0.0, min(ay, float(image_height)))
    max_w, max_h = _anchor_max_size(anchor, ax, ay, image_width, image_height)
    w, h = _fit_aspect_within(w, h, aspect, max(1.0, max_w), max(1.0, max_h))
    left, top, right, bottom = _box_from_anchor(anchor, ax, ay, w, h)
    left = max(0, int(round(left)))
    top = max(0, int(round(top)))
    right = max(left + 1, min(int(round(right)), image_width))
    bottom = max(top + 1, min(int(round(bottom)), image_height))
    return left, top, right, bottom


def _resize_corner_aspect_locked(
    origin: tuple[float, float, float, float],
    handle: str,
    dx: float,
    dy: float,
    aspect: float,
    image_width: int,
    image_height: int,
    min_side: float = 4.0,
) -> tuple[int, int, int, int]:
    """Redimensiona desde una esquina manteniendo proporcion; la esquina opuesta queda fija."""
    ol, ot, or_, ob = origin
    orig_w = max(min_side, or_ - ol)
    orig_h = max(min_side, ob - ot)

    if handle == "br":
        w = max(min_side, orig_w + dx)
        h = max(min_side, orig_h + dy)
        if w / h > aspect:
            w = h * aspect
        else:
            h = w / aspect
        return clamp_crop_preserve_aspect_at_anchor("tl", ol, ot, w, h, aspect, image_width, image_height)
    if handle == "tl":
        w = max(min_side, orig_w - dx)
        h = max(min_side, orig_h - dy)
        if w / h > aspect:
            w = h * aspect
        else:
            h = w / aspect
        return clamp_crop_preserve_aspect_at_anchor("br", or_, ob, w, h, aspect, image_width, image_height)
    if handle == "tr":
        w = max(min_side, orig_w + dx)
        h = max(min_side, orig_h - dy)
        if w / h > aspect:
            w = h * aspect
        else:
            h = w / aspect
        return clamp_crop_preserve_aspect_at_anchor("bl", ol, ob, w, h, aspect, image_width, image_height)
    if handle == "bl":
        w = max(min_side, orig_w - dx)
        h = max(min_side, orig_h + dy)
        if w / h > aspect:
            w = h * aspect
        else:
            h = w / aspect
        return clamp_crop_preserve_aspect_at_anchor("tr", or_, ot, w, h, aspect, image_width, image_height)
    return clamp_crop_box(origin, image_width, image_height)


def resize_crop_box_by_handle(
    origin: tuple[int, int, int, int],
    handle: str,
    dx: float,
    dy: float,
    image_width: int,
    image_height: int,
    aspect: float | None = None,
) -> tuple[int, int, int, int]:
    if handle == "move":
        return move_crop_box(origin, dx, dy, image_width, image_height)

    ol, ot, or_, ob = map(float, origin)
    if aspect and aspect > 0 and handle in CORNER_HANDLES:
        return _resize_corner_aspect_locked(origin, handle, dx, dy, aspect, image_width, image_height)

    left, top, right, bottom = ol, ot, or_, ob
    if handle == "tl":
        left += dx
        top += dy
    elif handle == "tr":
        right += dx
        top += dy
    elif handle == "bl":
        left += dx
        bottom += dy
    elif handle == "br":
        right += dx
        bottom += dy
    elif handle == "tm":
        top += dy
    elif handle == "bm":
        bottom += dy
    elif handle == "ml":
        left += dx
    elif handle == "mr":
        right += dx
    return clamp_crop_box((left, top, right, bottom), image_width, image_height)


def crop_box_from_drag_anchor(
    start: tuple[float, float],
    end: tuple[float, float],
    image_width: int,
    image_height: int,
    aspect: float | None = None,
) -> tuple[int, int, int, int]:
    x0, y0 = start
    dx = end[0] - x0
    dy = end[1] - y0
    if not aspect or aspect <= 0:
        return clamp_crop_box((x0, y0, end[0], end[1]), image_width, image_height)

    abs_dx = abs(dx)
    abs_dy = abs(dy)
    if abs_dx / max(abs_dy, 1e-6) > aspect:
        w, h = abs_dx, abs_dx / aspect
    else:
        h, w = abs_dy, abs_dy * aspect

    if dx >= 0 and dy >= 0:
        anchor = "tl"
    elif dx < 0 and dy >= 0:
        anchor = "tr"
    elif dx >= 0 and dy < 0:
        anchor = "bl"
    else:
        anchor = "br"

    return clamp_crop_preserve_aspect_at_anchor(anchor, x0, y0, w, h, aspect, image_width, image_height)


def mask_outside_box_inplace(image: Image.Image, box: tuple[int, int, int, int]) -> None:
    left, top, right, bottom = box
    width, height = image.size
    left = max(0, min(int(left), width))
    top = max(0, min(int(top), height))
    right = max(left, min(int(right), width))
    bottom = max(top, min(int(bottom), height))
    mask = Image.new("L", (width, height), 0)
    if right > left and bottom > top:
        draw = ImageDraw.Draw(mask)
        draw.rectangle([left, top, right - 1, bottom - 1], fill=255)
    alpha = image.getchannel("A")
    image.putalpha(ImageChops.multiply(alpha, mask))


def apply_aspect_ratio(
    box: tuple[float, float, float, float],
    aspect: float | None,
    handle: str,
    image_width: int,
    image_height: int,
) -> tuple[float, float, float, float]:
    if aspect is None or aspect <= 0:
        return box
    left, top, right, bottom = box
    width = max(1.0, right - left)
    height = max(1.0, bottom - top)
    current = width / height
    if current > aspect:
        width = height * aspect
    else:
        height = width / aspect
    if handle in {"tl", "bl"}:
        right = left + width
    elif handle in {"tr", "br"}:
        left = right - width
    else:
        center_x = (left + right) / 2
        left = center_x - width / 2
        right = center_x + width / 2
    if handle in {"tl", "tr"}:
        bottom = top + height
    elif handle in {"bl", "br"}:
        top = bottom - height
    else:
        center_y = (top + bottom) / 2
        top = center_y - height / 2
        bottom = center_y + height / 2
    left = max(0.0, min(left, image_width - 1))
    top = max(0.0, min(top, image_height - 1))
    right = max(left + 1, min(right, image_width))
    bottom = max(top + 1, min(bottom, image_height))
    return left, top, right, bottom


def resize_to_preset(
    image: Image.Image,
    preset: str,
    custom_width: int | None = None,
    custom_height: int | None = None,
) -> Image.Image:
    width, height = image.size
    if preset == "custom":
        if not custom_width or not custom_height:
            raise ValueError("Tamano personalizado invalido.")
        return image.resize((int(custom_width), int(custom_height)), Image.Resampling.LANCZOS)
    if preset == "original":
        return image.copy()
    max_side = RESIZE_PRESETS.get(preset, RESIZE_PRESETS["media"])
    scale = max_side / max(width, height)
    new_size = (max(1, int(width * scale)), max(1, int(height * scale)))
    if new_size == (width, height):
        return image.copy()
    return image.resize(new_size, Image.Resampling.LANCZOS)


def canvas_content_offset(
    anchor: str,
    canvas_width: int,
    canvas_height: int,
    content_width: int,
    content_height: int,
) -> tuple[int, int]:
    if anchor == "tl":
        return 0, 0
    if anchor == "tr":
        return canvas_width - content_width, 0
    if anchor == "bl":
        return 0, canvas_height - content_height
    if anchor == "br":
        return canvas_width - content_width, canvas_height - content_height
    return (canvas_width - content_width) // 2, (canvas_height - content_height) // 2


CANVAS_RESOLUTIONS = {
    "hd": (1280, 720),
    "fhd": (1920, 1080),
    "4k": (3840, 2160),
}


def canvas_dimensions_from_preset(resolution: str, aspect: str) -> tuple[int, int]:
    base_w, base_h = CANVAS_RESOLUTIONS.get(resolution, CANVAS_RESOLUTIONS["fhd"])
    long_side = max(base_w, base_h)
    short_side = min(base_w, base_h)
    if aspect == "9:16":
        height = long_side
        width = int(round(height * 9 / 16))
        return max(1, width), height
    if aspect == "1:1":
        return short_side, short_side
    if aspect == "16:9":
        width = long_side
        height = int(round(width * 9 / 16))
        return width, max(1, height)
    return base_w, base_h


def fit_image_on_canvas(
    image_width: int,
    image_height: int,
    canvas_width: int,
    canvas_height: int,
) -> tuple[float, float, float]:
    if image_width <= 0 or image_height <= 0:
        return 0.0, 0.0, 1.0
    scale = min(canvas_width / image_width, canvas_height / image_height)
    scaled_w = image_width * scale
    scaled_h = image_height * scale
    placement_x = (canvas_width - scaled_w) / 2
    placement_y = (canvas_height - scaled_h) / 2
    return placement_x, placement_y, scale


def compose_canvas_layout(
    image: Image.Image,
    stroke_layer: Image.Image | None,
    canvas_width: int,
    canvas_height: int,
    placement_x: float,
    placement_y: float,
    content_scale: float,
    preview: bool = False,
) -> tuple[Image.Image, Image.Image | None]:
    base = image.convert("RGBA")
    canvas_w = max(1, int(canvas_width))
    canvas_h = max(1, int(canvas_height))
    scale = max(0.01, float(content_scale))
    scaled_w = max(1, int(round(base.width * scale)))
    scaled_h = max(1, int(round(base.height * scale)))
    resample = Image.Resampling.BILINEAR if preview else Image.Resampling.LANCZOS
    scaled_base = base.resize((scaled_w, scaled_h), resample)
    px = int(round(placement_x))
    py = int(round(placement_y))
    new_base = Image.new("RGBA", (canvas_w, canvas_h), (0, 0, 0, 0))
    new_base.paste(scaled_base, (px, py), scaled_base)
    new_stroke = None
    if stroke_layer is not None:
        stroke_rgba = stroke_layer.convert("RGBA")
        if stroke_rgba.size != base.size:
            stroke_rgba = stroke_rgba.resize(base.size, Image.Resampling.NEAREST)
        scaled_stroke = stroke_rgba.resize((scaled_w, scaled_h), resample)
        new_stroke = Image.new("RGBA", (canvas_w, canvas_h), (0, 0, 0, 0))
        new_stroke.paste(scaled_stroke, (px, py), scaled_stroke)
    return new_base, new_stroke


def paired_scale_dimensions(
    source_width: int,
    source_height: int,
    target_width: int,
    target_height: int,
    lock_aspect: bool,
    edited_axis: str,
) -> tuple[int, int]:
    tw = max(1, int(target_width))
    th = max(1, int(target_height))
    if not lock_aspect or source_width <= 0 or source_height <= 0:
        return tw, th
    aspect = source_width / source_height
    if edited_axis == "w":
        return tw, max(1, int(round(tw / aspect)))
    return max(1, int(round(th * aspect))), th


def resize_scale_image(
    image: Image.Image,
    target_width: int,
    target_height: int,
    lock_aspect: bool = True,
) -> Image.Image:
    width, height = image.size
    tw = max(1, int(target_width))
    th = max(1, int(target_height))
    if lock_aspect and width > 0 and height > 0:
        aspect = width / height
        dw = abs(tw - width) / max(width, 1)
        dh = abs(th - height) / max(height, 1)
        if dw >= dh:
            th = max(1, int(round(tw / aspect)))
        else:
            tw = max(1, int(round(th * aspect)))
    if (tw, th) == (width, height):
        return image.copy()
    return image.resize((tw, th), Image.Resampling.LANCZOS)


def resize_canvas_layers(
    image: Image.Image,
    stroke_layer: Image.Image | None,
    canvas_width: int,
    canvas_height: int,
    anchor: str = "center",
) -> tuple[Image.Image, Image.Image | None]:
    base = image.convert("RGBA")
    content_w, content_h = base.size
    canvas_w = max(1, int(canvas_width))
    canvas_h = max(1, int(canvas_height))
    offset_x, offset_y = canvas_content_offset(anchor, canvas_w, canvas_h, content_w, content_h)
    new_base = Image.new("RGBA", (canvas_w, canvas_h), (0, 0, 0, 0))
    new_base.paste(base, (offset_x, offset_y), base)
    new_stroke = None
    if stroke_layer is not None:
        stroke_rgba = stroke_layer.convert("RGBA")
        if stroke_rgba.size != base.size:
            stroke_rgba = stroke_rgba.resize(base.size, Image.Resampling.NEAREST)
        new_stroke = Image.new("RGBA", (canvas_w, canvas_h), (0, 0, 0, 0))
        new_stroke.paste(stroke_rgba, (offset_x, offset_y), stroke_rgba)
    return new_base, new_stroke


def preset_scale_dimensions(
    source_width: int,
    source_height: int,
    max_side: int,
) -> tuple[int, int]:
    if source_width <= 0 or source_height <= 0:
        return 1, 1
    scale = max_side / max(source_width, source_height)
    return (
        max(1, int(round(source_width * scale))),
        max(1, int(round(source_height * scale))),
    )


def trim_transparent(image: Image.Image) -> Image.Image:
    rgba = image.convert("RGBA")
    bbox = rgba.split()[-1].getbbox()
    if bbox is None:
        return rgba
    return rgba.crop(bbox)


def trim_layers_together(
    image: Image.Image,
    stroke_layer: Image.Image | None,
) -> tuple[Image.Image, Image.Image | None]:
    base = image.convert("RGBA")
    if stroke_layer is not None:
        stroke_rgba = stroke_layer.convert("RGBA")
        if stroke_rgba.size != base.size:
            stroke_rgba = stroke_rgba.resize(base.size, Image.Resampling.NEAREST)
        combined = Image.alpha_composite(base, stroke_rgba)
    else:
        stroke_rgba = None
        combined = base
    bbox = combined.split()[-1].getbbox()
    if bbox is None:
        return base, stroke_rgba
    trimmed_base = base.crop(bbox)
    trimmed_stroke = stroke_rgba.crop(bbox) if stroke_rgba is not None else None
    return trimmed_base, trimmed_stroke


def rotate_free(image: Image.Image, degrees: float) -> Image.Image:
    if abs(degrees) < 0.01:
        return image.copy()
    source = trim_transparent(image)
    rotated = source.rotate(
        -degrees,
        expand=True,
        resample=Image.Resampling.BICUBIC,
        fillcolor=(0, 0, 0, 0),
    )
    return trim_transparent(rotated)


def rotate_free_preview(image: Image.Image, degrees: float) -> Image.Image:
    if abs(degrees) < 0.01:
        return image.copy()
    source = trim_transparent(image)
    rotated = source.rotate(
        -degrees,
        expand=True,
        resample=Image.Resampling.BILINEAR,
        fillcolor=(0, 0, 0, 0),
    )
    return trim_transparent(rotated)


def rotate_image_and_stroke(
    image: Image.Image,
    stroke_layer: Image.Image | None,
    degrees: float,
) -> tuple[Image.Image, Image.Image | None]:
    if abs(degrees) < 0.01:
        return image.copy(), stroke_layer.copy() if stroke_layer is not None else None
    base, stroke = trim_layers_together(image, stroke_layer)
    rotated_base = base.rotate(
        -degrees,
        expand=True,
        resample=Image.Resampling.BICUBIC,
        fillcolor=(0, 0, 0, 0),
    )
    rotated_stroke = None
    if stroke is not None:
        rotated_stroke = stroke.rotate(
            -degrees,
            expand=True,
            resample=Image.Resampling.BICUBIC,
            fillcolor=(0, 0, 0, 0),
        )
    return trim_layers_together(rotated_base, rotated_stroke)


def flip_horizontal(image: Image.Image) -> Image.Image:
    return image.transpose(Image.Transpose.FLIP_LEFT_RIGHT)


def flip_vertical(image: Image.Image) -> Image.Image:
    return image.transpose(Image.Transpose.FLIP_TOP_BOTTOM)


def rgba_to_hex(rgba: tuple[int, ...]) -> str:
    red, green, blue = rgba[0], rgba[1], rgba[2]
    return f"#{red:02x}{green:02x}{blue:02x}"


def sample_composite_color(image: Image.Image, x: float, y: float) -> tuple[int, int, int, int] | None:
    ix = int(round(x))
    iy = int(round(y))
    if ix < 0 or iy < 0 or ix >= image.width or iy >= image.height:
        return None
    pixel = image.getpixel((ix, iy))
    if isinstance(pixel, int):
        return pixel, pixel, pixel, 255
    if len(pixel) == 3:
        return pixel[0], pixel[1], pixel[2], 255
    return pixel[0], pixel[1], pixel[2], pixel[3]


def hex_to_rgba(value: str, opacity: int = 255) -> tuple[int, int, int, int]:
    cleaned = (value or "#ffffff").lstrip("#")
    if len(cleaned) == 3:
        cleaned = "".join(ch * 2 for ch in cleaned)
    red = int(cleaned[0:2], 16)
    green = int(cleaned[2:4], 16)
    blue = int(cleaned[4:6], 16)
    alpha = max(0, min(255, int(opacity * 255 / 100)))
    return red, green, blue, alpha


def interpolate_segment(
    start: tuple[float, float],
    end: tuple[float, float],
    step: float = 1.5,
) -> list[tuple[float, float]]:
    x0, y0 = start
    x1, y1 = end
    distance = ((x1 - x0) ** 2 + (y1 - y0) ** 2) ** 0.5
    if distance <= step:
        return [start, end]
    count = max(2, int(distance / step) + 1)
    points = []
    for index in range(count):
        t = index / (count - 1)
        points.append((x0 + (x1 - x0) * t, y0 + (y1 - y0) * t))
    return points


def brush_interpolation_step(size: int) -> float:
    return max(0.35, float(size) / 14.0)


def densify_stroke_points(
    points: list[tuple[float, float]],
    size: int,
) -> list[tuple[float, float]]:
    if not points:
        return []
    if len(points) == 1:
        return [points[0]]
    step = brush_interpolation_step(size)
    dense: list[tuple[float, float]] = []
    for index in range(len(points) - 1):
        segment = interpolate_segment(points[index], points[index + 1], step=step)
        if dense and segment:
            segment = segment[1:]
        dense.extend(segment)
    return dense


def _stamp_brush_discs(
    draw: ImageDraw.ImageDraw,
    points: list[tuple[float, float]],
    radius: float,
    fill,
) -> None:
    r = max(1.0, radius)
    ri = int(round(r))
    for x, y in points:
        cx = int(round(x))
        cy = int(round(y))
        draw.ellipse([cx - ri, cy - ri, cx + ri, cy + ri], fill=fill)


def bucket_fill(
    image: Image.Image,
    x: int,
    y: int,
    fill_rgba: tuple[int, int, int, int],
    tolerance: int = 32,
) -> None:
    if image.mode != "RGBA":
        raise ValueError("La imagen debe estar en RGBA.")
    x = max(0, min(int(x), image.width - 1))
    y = max(0, min(int(y), image.height - 1))
    data = np.array(image, copy=True)
    _flood_fill_array(data, x, y, fill_rgba, tolerance)
    image.paste(Image.fromarray(data))


def bucket_fill_stroke_from_composite(
    stroke_layer: Image.Image,
    composite: Image.Image,
    x: int,
    y: int,
    fill_rgba: tuple[int, int, int, int],
    tolerance: int = 32,
) -> None:
    if stroke_layer.mode != "RGBA":
        raise ValueError("La capa de trazos debe estar en RGBA.")
    if composite.mode != "RGBA":
        composite = composite.convert("RGBA")
    x = max(0, min(int(x), composite.width - 1))
    y = max(0, min(int(y), composite.height - 1))
    source = np.asarray(composite, dtype=np.int16)
    stroke_data = np.array(stroke_layer, copy=True)
    mask = _flood_fill_mask(source, x, y, tolerance)
    if not mask.any():
        return
    fill = np.array(fill_rgba, dtype=np.uint8)
    stroke_data[mask] = fill
    stroke_layer.paste(Image.fromarray(stroke_data))


def _flood_fill_mask(source: np.ndarray, x: int, y: int, tolerance: int) -> np.ndarray:
    height, width = source.shape[:2]
    target = source[y, x, :3]
    tol = max(0, int(tolerance))
    visited = np.zeros((height, width), dtype=bool)
    queue: deque[tuple[int, int]] = deque([(x, y)])
    while queue:
        cx, cy = queue.popleft()
        if cx < 0 or cy < 0 or cx >= width or cy >= height or visited[cy, cx]:
            continue
        if np.max(np.abs(source[cy, cx, :3] - target)) > tol:
            continue
        visited[cy, cx] = True
        queue.append((cx + 1, cy))
        queue.append((cx - 1, cy))
        queue.append((cx, cy + 1))
        queue.append((cx, cy - 1))
    return visited


def _flood_fill_array(
    data: np.ndarray,
    x: int,
    y: int,
    fill_rgba: tuple[int, int, int, int],
    tolerance: int,
) -> None:
    source = data.astype(np.int16, copy=False)
    mask = _flood_fill_mask(source, x, y, tolerance)
    if not mask.any():
        return
    fill = np.array(fill_rgba, dtype=np.uint8)
    data[mask] = fill


def draw_brush_stroke(
    image: Image.Image,
    points: list[tuple[float, float]],
    color: tuple[int, int, int, int],
    size: int,
    mode: str = "pencil",
) -> None:
    if not points:
        return
    if image.mode != "RGBA":
        raise ValueError("La imagen debe estar en RGBA.")
    radius = max(1.0, float(size) / 2.0)
    dense = densify_stroke_points(points, size)
    layer = Image.new("RGBA", image.size, (0, 0, 0, 0))
    draw = ImageDraw.Draw(layer)
    _stamp_brush_discs(draw, dense, radius, color)
    image.alpha_composite(layer)


def erase_manual_stroke(image: Image.Image, points: list[tuple[float, float]], size: int) -> None:
    radius = max(1.0, float(size) / 2.0)
    dense = densify_stroke_points(points, size)
    mask = Image.new("L", image.size, 0)
    draw = ImageDraw.Draw(mask)
    _stamp_brush_discs(draw, dense, radius, 255)
    alpha = image.getchannel("A")
    image.putalpha(ImageChops.subtract(alpha, mask))


def _color_distance(data: np.ndarray, x: int, y: int) -> np.ndarray:
    target = data[y, x, :3].astype(np.int16)
    diff = np.abs(data[:, :, :3].astype(np.int16) - target)
    return np.max(diff, axis=2)


def remove_color_global(image: Image.Image, x: int, y: int, tolerance: int = 32) -> None:
    rgba = image.convert("RGBA")
    data = np.array(rgba, copy=True)
    x = max(0, min(int(x), data.shape[1] - 1))
    y = max(0, min(int(y), data.shape[0] - 1))
    mask = _color_distance(data, x, y) <= tolerance
    data[mask, 3] = 0
    image.paste(Image.fromarray(data))


def normalize_shape_box(
    start: tuple[float, float],
    end: tuple[float, float],
) -> tuple[float, float, float, float] | None:
    x0, y0 = start
    x1, y1 = end
    left, right = sorted((x0, x1))
    top, bottom = sorted((y0, y1))
    if right - left < 1 or bottom - top < 1:
        return None
    return left, top, right, bottom


SHAPE_CENTER_KINDS = frozenset({"circle"})
SHAPE_BOX_KINDS = frozenset({"rectangle", "oval", "triangle", "pentagon", "hexagon", "star"})
SHAPE_REGULAR_BOX_KINDS = frozenset({"triangle", "pentagon", "hexagon", "star"})
SHAPE_POLYGON_SIDES = {"triangle": 3, "pentagon": 5, "hexagon": 6}
SHAPE_CLICK_DRAG_THRESHOLD = 3.0


def clamp_image_point(
    x: float,
    y: float,
    image_width: float,
    image_height: float,
) -> tuple[float, float]:
    return (
        max(0.0, min(float(x), float(image_width))),
        max(0.0, min(float(y), float(image_height))),
    )


def default_shape_click_size(image_width: float, image_height: float) -> float:
    return max(24.0, min(min(image_width, image_height) * 0.12, 120.0))


def shape_drag_distance(
    start: tuple[float, float],
    end: tuple[float, float],
) -> float:
    return math.hypot(end[0] - start[0], end[1] - start[1])


def fit_shape_box_to_image(
    box: tuple[float, float, float, float],
    image_width: float,
    image_height: float,
) -> tuple[float, float, float, float]:
    left, top, right, bottom = box
    width = right - left
    height = bottom - top
    if width <= 0 or height <= 0:
        return box

    if width > image_width:
        left, right = 0.0, float(image_width)
    elif left < 0.0:
        right -= left
        left = 0.0
        if right > image_width:
            left -= right - image_width
            right = float(image_width)
            left = max(0.0, left)
    elif right > image_width:
        left -= right - image_width
        right = float(image_width)
        left = max(0.0, left)

    if height > image_height:
        top, bottom = 0.0, float(image_height)
    elif top < 0.0:
        bottom -= top
        top = 0.0
        if bottom > image_height:
            top -= bottom - image_height
            bottom = float(image_height)
            top = max(0.0, top)
    elif bottom > image_height:
        top -= bottom - image_height
        bottom = float(image_height)
        top = max(0.0, top)

    return left, top, right, bottom


def normalize_shape_box_or_click(
    start: tuple[float, float],
    end: tuple[float, float],
    image_width: float,
    image_height: float,
) -> tuple[float, float, float, float] | None:
    if shape_drag_distance(start, end) < SHAPE_CLICK_DRAG_THRESHOLD:
        default = default_shape_click_size(image_width, image_height)
        cx, cy = start
        half = default / 2
        box = (cx - half, cy - half, cx + half, cy + half)
        return fit_shape_box_to_image(box, image_width, image_height)
    box = normalize_shape_box(start, end)
    if box is None:
        return None
    return box


def shape_box_center_radius(
    box: tuple[float, float, float, float],
) -> tuple[float, float, float]:
    left, top, right, bottom = box
    cx = (left + right) / 2
    cy = (top + bottom) / 2
    radius = min(right - left, bottom - top) / 2
    return cx, cy, radius


def star_vertices(
    center_x: float,
    center_y: float,
    outer_radius: float,
    *,
    points: int = 5,
    inner_ratio: float = 0.4,
    rotation: float = -math.pi / 2,
) -> list[tuple[float, float]]:
    if outer_radius < 1 or points < 2:
        return []
    inner_radius = outer_radius * inner_ratio
    vertices: list[tuple[float, float]] = []
    for index in range(points * 2):
        angle = rotation + (math.pi * index / points)
        radius = outer_radius if index % 2 == 0 else inner_radius
        vertices.append(
            (
                center_x + radius * math.cos(angle),
                center_y + radius * math.sin(angle),
            )
        )
    return vertices


def resolve_shape_geometry(
    kind: str,
    start: tuple[float, float],
    end: tuple[float, float],
    image_width: float,
    image_height: float,
) -> tuple[tuple[float, float], tuple[float, float]] | None:
    start = (float(start[0]), float(start[1]))
    end = (float(end[0]), float(end[1]))
    default = default_shape_click_size(image_width, image_height)

    if kind == "line":
        if shape_drag_distance(start, end) < SHAPE_CLICK_DRAG_THRESHOLD:
            end = (start[0] + default / 2, start[1])
        if shape_drag_distance(start, end) < 1:
            return None
        return start, end

    if kind == "circle":
        if shape_drag_distance(start, end) < SHAPE_CLICK_DRAG_THRESHOLD:
            end = (start[0] + default / 2, start[1])
        if shape_radius_from_center(start, end) < 1:
            return None
        return start, end

    if kind in SHAPE_BOX_KINDS:
        box = normalize_shape_box_or_click(start, end, image_width, image_height)
        if box is None:
            return None
        left, top, right, bottom = box
        if right - left < 1 or bottom - top < 1:
            return None
        return (left, top), (right, bottom)

    return None


def shape_radius_from_center(
    center: tuple[float, float],
    point: tuple[float, float],
) -> float:
    return math.hypot(point[0] - center[0], point[1] - center[1])


def regular_polygon_vertices(
    center_x: float,
    center_y: float,
    radius: float,
    sides: int,
    rotation: float = -math.pi / 2,
) -> list[tuple[float, float]]:
    if radius < 1 or sides < 3:
        return []
    vertices: list[tuple[float, float]] = []
    for index in range(sides):
        angle = rotation + (2 * math.pi * index / sides)
        vertices.append(
            (
                center_x + radius * math.cos(angle),
                center_y + radius * math.sin(angle),
            )
        )
    return vertices


def _catmull_rom_point(
    p0: tuple[float, float],
    p1: tuple[float, float],
    p2: tuple[float, float],
    p3: tuple[float, float],
    t: float,
) -> tuple[float, float]:
    t2 = t * t
    t3 = t2 * t
    x = 0.5 * (
        (2 * p1[0])
        + (-p0[0] + p2[0]) * t
        + (2 * p0[0] - 5 * p1[0] + 4 * p2[0] - p3[0]) * t2
        + (-p0[0] + 3 * p1[0] - 3 * p2[0] + p3[0]) * t3
    )
    y = 0.5 * (
        (2 * p1[1])
        + (-p0[1] + p2[1]) * t
        + (2 * p0[1] - 5 * p1[1] + 4 * p2[1] - p3[1]) * t2
        + (-p0[1] + 3 * p1[1] - 3 * p2[1] + p3[1]) * t3
    )
    return x, y


def catmull_rom_chain(
    points: list[tuple[float, float]],
    samples_per_segment: int = 16,
) -> list[tuple[float, float]]:
    if len(points) <= 1:
        return list(points)
    if len(points) == 2:
        return interpolate_segment(points[0], points[1], step=1.0)
    extended = [points[0], *points, points[-1]]
    result: list[tuple[float, float]] = []
    for index in range(1, len(extended) - 2):
        p0, p1, p2, p3 = extended[index - 1], extended[index], extended[index + 1], extended[index + 2]
        for sample in range(samples_per_segment):
            t = sample / samples_per_segment
            result.append(_catmull_rom_point(p0, p1, p2, p3, t))
    result.append(points[-1])
    return result


def render_shape(
    image: Image.Image,
    kind: str,
    start: tuple[float, float],
    end: tuple[float, float] | None = None,
    curve_points: list[tuple[float, float]] | None = None,
    *,
    fill_enabled: bool,
    fill_rgba: tuple[int, int, int, int],
    stroke_enabled: bool,
    stroke_rgba: tuple[int, int, int, int],
    stroke_width: int,
) -> None:
    if image.mode != "RGBA":
        raise ValueError("La imagen debe estar en RGBA.")
    if not fill_enabled and not stroke_enabled:
        return
    img_w, img_h = image.size
    draw = ImageDraw.Draw(image)
    fill = fill_rgba if fill_enabled else None
    outline = stroke_rgba if stroke_enabled else None
    width = max(1, int(stroke_width)) if stroke_enabled else 0

    if kind == "curve":
        points = list(curve_points or [])
        if len(points) < 2:
            return
        points = [clamp_image_point(px, py, img_w, img_h) for px, py in points]
        path = catmull_rom_chain(points)
        line_color = outline if stroke_enabled else fill
        line_width = width if stroke_enabled else max(1, width)
        if line_color is not None and len(path) >= 2:
            draw.line(path, fill=line_color, width=line_width, joint="curve")
        return

    if end is None:
        return
    geometry = resolve_shape_geometry(kind, start, end, img_w, img_h)
    if geometry is None:
        return
    start, end = geometry

    if kind == "line":
        line_color = outline if stroke_enabled else fill
        line_width = width if stroke_enabled else max(1, width)
        if line_color is None:
            return
        draw.line([start, end], fill=line_color, width=line_width, joint="curve")
        return

    if kind == "circle":
        radius = shape_radius_from_center(start, end)
        cx, cy = start
        bbox = [cx - radius, cy - radius, cx + radius, cy + radius]
        draw.ellipse(bbox, fill=fill, outline=outline, width=width)
        return

    if kind in SHAPE_REGULAR_BOX_KINDS:
        box = (*start, *end)
        cx, cy, radius = shape_box_center_radius(box)
        if radius < 1:
            return
        if kind == "star":
            vertices = star_vertices(cx, cy, radius)
        else:
            sides = SHAPE_POLYGON_SIDES[kind]
            vertices = regular_polygon_vertices(cx, cy, radius, sides)
        if vertices:
            draw.polygon(vertices, fill=fill, outline=outline, width=width)
        return

    if kind == "rectangle":
        draw.rectangle([*start, *end], fill=fill, outline=outline, width=width)
        return

    if kind == "oval":
        draw.ellipse([*start, *end], fill=fill, outline=outline, width=width)


def remove_color_flood(image: Image.Image, x: int, y: int, tolerance: int = 32) -> None:
    if image.mode != "RGBA":
        converted = image.convert("RGBA")
        image.paste(converted)
    x = max(0, min(int(x), image.width - 1))
    y = max(0, min(int(y), image.height - 1))
    try:
        ImageDraw.floodfill(image, (x, y), (0, 0, 0, 0), thresh=tolerance)
        return
    except (AttributeError, TypeError):
        pass
    data = np.array(image, copy=True)
    height, width = data.shape[:2]
    target = data[y, x, :3].astype(np.int16)
    visited = np.zeros((height, width), dtype=bool)
    stack = [(x, y)]
    while stack:
        cx, cy = stack.pop()
        if cx < 0 or cy < 0 or cx >= width or cy >= height or visited[cy, cx]:
            continue
        if np.max(np.abs(data[cy, cx, :3].astype(np.int16) - target)) > tolerance:
            continue
        visited[cy, cx] = True
        data[cy, cx, 3] = 0
        stack.extend([(cx + 1, cy), (cx - 1, cy), (cx, cy + 1), (cx, cy - 1)])
    image.paste(Image.fromarray(data))


def remove_color_magic(
    image: Image.Image,
    points: list[tuple[float, float]],
    target_rgba: tuple[int, int, int, int],
    tolerance: int,
    size: int,
) -> None:
    if not points:
        return
    data = np.array(image.convert("RGBA"), copy=True)
    target = np.array(target_rgba[:3], dtype=np.int16)
    radius = max(1, size // 2)
    height, width = data.shape[:2]
    for px, py in points:
        x0 = max(0, int(px) - radius)
        y0 = max(0, int(py) - radius)
        x1 = min(width, int(px) + radius + 1)
        y1 = min(height, int(py) + radius + 1)
        patch = data[y0:y1, x0:x1]
        diff = np.abs(patch[:, :, :3].astype(np.int16) - target)
        mask = np.max(diff, axis=2) <= tolerance
        patch[mask, 3] = 0
        data[y0:y1, x0:x1] = patch
    image.paste(Image.fromarray(data))


def heal_stroke(
    image: Image.Image,
    reference: Image.Image,
    points: list[tuple[float, float]],
    size: int,
) -> None:
    if not points or reference.size != image.size:
        return
    radius = max(1, size // 2)
    for px, py in points:
        x0 = max(0, int(px) - radius)
        y0 = max(0, int(py) - radius)
        x1 = min(image.width, int(px) + radius + 1)
        y1 = min(image.height, int(py) + radius + 1)
        patch = reference.crop((x0, y0, x1, y1))
        image.paste(patch, (x0, y0), patch if patch.mode == "RGBA" else None)


CROP_HANDLE_VISUAL_RADIUS = 7
CROP_HANDLE_HIT_RADIUS = 15


def crop_handle_canvas_positions(
    box: tuple[int, int, int, int],
    scale: float,
    offset_x: float,
    offset_y: float,
    corners_only: bool = False,
) -> dict[str, tuple[float, float]]:
    left, top, right, bottom = box
    x0 = offset_x + left * scale
    y0 = offset_y + top * scale
    x1 = offset_x + right * scale
    y1 = offset_y + bottom * scale
    box_w = max(4.0, x1 - x0)
    box_h = max(4.0, y1 - y0)
    inset = min(10.0, box_w * 0.12, box_h * 0.12)
    mid_x = (x0 + x1) / 2
    mid_y = (y0 + y1) / 2
    handles = {
        "tl": (x0 + inset, y0 + inset),
        "tr": (x1 - inset, y0 + inset),
        "bl": (x0 + inset, y1 - inset),
        "br": (x1 - inset, y1 - inset),
    }
    if not corners_only:
        handles.update(
            {
                "tm": (mid_x, y0 + inset),
                "bm": (mid_x, y1 - inset),
                "ml": (x0 + inset, mid_y),
                "mr": (x1 - inset, mid_y),
            }
        )
    return handles


def hit_crop_handle(
    x: float,
    y: float,
    box: tuple[int, int, int, int],
    scale: float,
    offset_x: float,
    offset_y: float,
    handle_size: float = CROP_HANDLE_HIT_RADIUS,
    corners_only: bool = False,
) -> str | None:
    handles = crop_handle_canvas_positions(box, scale, offset_x, offset_y, corners_only)
    half = handle_size
    for name, (cx, cy) in handles.items():
        if abs(x - cx) <= half and abs(y - cy) <= half:
            return name
    left, top, right, bottom = box
    canvas_left = offset_x + left * scale
    canvas_top = offset_y + top * scale
    canvas_right = offset_x + right * scale
    canvas_bottom = offset_y + bottom * scale
    if canvas_left <= x <= canvas_right and canvas_top <= y <= canvas_bottom:
        return "move"
    return None


def move_crop_box(
    box: tuple[int, int, int, int],
    dx: float,
    dy: float,
    image_width: int,
    image_height: int,
) -> tuple[int, int, int, int]:
    left, top, right, bottom = box
    width = right - left
    height = bottom - top
    left = max(0, min(int(round(left + dx)), image_width - width))
    top = max(0, min(int(round(top + dy)), image_height - height))
    return left, top, left + width, top + height


ROTATE_WHEEL_TICK_STEP = 45
ROTATE_SNAP_THRESHOLD = 7.0
ROTATE_HANDLE_VISUAL_RADIUS = 7
ROTATE_HANDLE_HIT_RADIUS = 12


def rotate_wheel_geometry(
    offset_x: float,
    offset_y: float,
    display_w: float,
    display_h: float,
) -> tuple[float, float, float]:
    center_x = offset_x + display_w / 2
    center_y = offset_y + display_h / 2
    radius = max(20.0, min(display_w, display_h) * 0.27)
    return center_x, center_y, radius


def rotate_pointer_angle_from_top(center_x: float, center_y: float, x: float, y: float) -> float:
    return math.degrees(math.atan2(x - center_x, -(y - center_y)))


def rotate_angle_delta_degrees(start: float, current: float) -> float:
    delta = current - start
    while delta > 180:
        delta -= 360
    while delta < -180:
        delta += 360
    return delta


def snap_rotate_angle(
    angle: float,
    step: int = ROTATE_WHEEL_TICK_STEP,
    threshold: float = ROTATE_SNAP_THRESHOLD,
) -> float:
    snapped = round(angle / step) * step
    if abs(angle - snapped) <= threshold:
        return snapped
    return angle


def rotate_point_on_wheel(
    center_x: float,
    center_y: float,
    radius: float,
    angle_from_top_deg: float,
) -> tuple[float, float]:
    radians = math.radians(angle_from_top_deg)
    return (
        center_x + radius * math.sin(radians),
        center_y - radius * math.cos(radians),
    )


def rotate_wheel_tick_angles() -> list[int]:
    return list(range(0, 360, ROTATE_WHEEL_TICK_STEP))


def hit_rotate_handle(
    x: float,
    y: float,
    center_x: float,
    center_y: float,
    radius: float,
    handle_angle_deg: float,
    hit_radius: float = ROTATE_HANDLE_HIT_RADIUS,
) -> bool:
    handle_x, handle_y = rotate_point_on_wheel(center_x, center_y, radius, handle_angle_deg)
    return (x - handle_x) ** 2 + (y - handle_y) ** 2 <= hit_radius**2
