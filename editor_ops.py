"""Advanced image operations for the FissileKit editor."""

from __future__ import annotations

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


def rotate_free(image: Image.Image, degrees: float) -> Image.Image:
    return image.rotate(
        -degrees,
        expand=True,
        resample=Image.Resampling.BICUBIC,
        fillcolor=(0, 0, 0, 0),
    )


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
    target = data[y, x, :3].astype(np.int16)
    fill = np.array(fill_rgba, dtype=np.uint8)
    height, width = data.shape[:2]
    visited = np.zeros((height, width), dtype=bool)
    stack = [(x, y)]
    while stack:
        cx, cy = stack.pop()
        if cx < 0 or cy < 0 or cx >= width or cy >= height or visited[cy, cx]:
            continue
        if np.max(np.abs(data[cy, cx, :3].astype(np.int16) - target)) > tolerance:
            continue
        visited[cy, cx] = True
        data[cy, cx] = fill
        stack.extend([(cx + 1, cy), (cx - 1, cy), (cx, cy + 1), (cx, cy - 1)])
    image.paste(Image.fromarray(data))


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
    layer = Image.new("RGBA", image.size, (0, 0, 0, 0))
    draw = ImageDraw.Draw(layer)
    radius = max(1, size // 2)
    if len(points) >= 2:
        draw.line(points, fill=color, width=max(1, size), joint="curve")
    else:
        x, y = points[0]
        draw.ellipse([x - radius, y - radius, x + radius, y + radius], fill=color)
    image.alpha_composite(layer)


def erase_manual_stroke(image: Image.Image, points: list[tuple[float, float]], size: int) -> None:
    mask = Image.new("L", image.size, 0)
    draw = ImageDraw.Draw(mask)
    if len(points) >= 2:
        draw.line(points, fill=255, width=max(1, size), joint="curve")
    elif points:
        radius = max(1, size // 2)
        x, y = points[0]
        draw.ellipse([x - radius, y - radius, x + radius, y + radius], fill=255)
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


def hit_crop_handle(
    x: float,
    y: float,
    box: tuple[int, int, int, int],
    scale: float,
    offset_x: float,
    offset_y: float,
    handle_size: float = 10.0,
) -> str | None:
    left, top, right, bottom = box
    corners = {
        "tl": (offset_x + left * scale, offset_y + top * scale),
        "tr": (offset_x + right * scale, offset_y + top * scale),
        "bl": (offset_x + left * scale, offset_y + bottom * scale),
        "br": (offset_x + right * scale, offset_y + bottom * scale),
    }
    half = handle_size
    for name, (cx, cy) in corners.items():
        if abs(x - cx) <= half and abs(y - cy) <= half:
            return name
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
