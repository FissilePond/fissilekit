"""Image editor session and folder scanning for FissileKit."""

from __future__ import annotations

import subprocess
import sys
import tempfile
from pathlib import Path

from PIL import Image, ImageChops, ImageDraw, ImageFont

import conversion
import editor_ops

MAX_UNDO = 30
DRAW_WIDTH = 4
ERASE_WIDTH = 16


def scan_media_folder(root: Path) -> dict[str, list[Path]]:
    groups: dict[str, list[Path]] = {"image": [], "video": [], "audio": []}
    if not root.is_dir():
        return groups
    for path in sorted(root.rglob("*")):
        if not path.is_file():
            continue
        kind = conversion.detect_media_kind(path)
        if kind in groups:
            groups[kind].append(path)
    return groups


def display_metrics(
    canvas_width: int,
    canvas_height: int,
    image_width: int,
    image_height: int,
) -> tuple[float, float, float, float, float]:
    if image_width <= 0 or image_height <= 0 or canvas_width <= 0 or canvas_height <= 0:
        return 1.0, 0.0, 0.0, float(canvas_width), float(canvas_height)
    scale = min(canvas_width / image_width, canvas_height / image_height)
    display_w = image_width * scale
    display_h = image_height * scale
    offset_x = (canvas_width - display_w) / 2
    offset_y = (canvas_height - display_h) / 2
    return scale, offset_x, offset_y, display_w, display_h


def canvas_to_image(
    x: float,
    y: float,
    canvas_width: int,
    canvas_height: int,
    image_width: int,
    image_height: int,
) -> tuple[float, float] | None:
    scale, offset_x, offset_y, display_w, display_h = display_metrics(
        canvas_width, canvas_height, image_width, image_height
    )
    if x < offset_x or y < offset_y or x > offset_x + display_w or y > offset_y + display_h:
        return None
    return ((x - offset_x) / scale, (y - offset_y) / scale)


def image_to_canvas(
    x: float,
    y: float,
    canvas_width: int,
    canvas_height: int,
    image_width: int,
    image_height: int,
) -> tuple[float, float]:
    scale, offset_x, offset_y, _, _ = display_metrics(
        canvas_width, canvas_height, image_width, image_height
    )
    return (offset_x + x * scale, offset_y + y * scale)


def _load_video_preview(path: Path, ffmpeg_location: str | None) -> Image.Image:
    ffmpeg = conversion.find_ffmpeg(ffmpeg_location)
    if not ffmpeg:
        return conversion_preview_placeholder("video")
    with tempfile.NamedTemporaryFile(suffix=".png", delete=False) as handle:
        raster_path = Path(handle.name)
    creationflags = subprocess.CREATE_NO_WINDOW if sys.platform == "win32" else 0
    try:
        result = subprocess.run(
            [
                ffmpeg,
                "-y",
                "-hide_banner",
                "-loglevel",
                "error",
                "-ss",
                "0",
                "-i",
                str(path),
                "-frames:v",
                "1",
                str(raster_path),
            ],
            capture_output=True,
            text=True,
            creationflags=creationflags,
        )
        if result.returncode != 0 or not raster_path.is_file():
            return conversion_preview_placeholder("video")
        with Image.open(raster_path) as image:
            return image.convert("RGBA")
    finally:
        if raster_path.exists():
            raster_path.unlink(missing_ok=True)


def conversion_preview_placeholder(kind: str) -> Image.Image:
    import conversion_preview

    return conversion_preview.placeholder_for_kind(kind)


class EditorSession:
    def __init__(self) -> None:
        self.source_path: Path | None = None
        self.media_kind = "unknown"
        self.image: Image.Image | None = None
        self.stroke_layer: Image.Image | None = None
        self.undo_stack: list[tuple[Image.Image, Image.Image | None]] = []
        self.redo_stack: list[tuple[Image.Image, Image.Image | None]] = []
        self.heal_reference: Image.Image | None = None

    def clear(self) -> None:
        self.source_path = None
        self.media_kind = "unknown"
        self.image = None
        self.stroke_layer = None
        self.undo_stack.clear()
        self.redo_stack.clear()

    def _reset_stroke_layer(self) -> None:
        if self.image is None:
            self.stroke_layer = None
            return
        self.stroke_layer = Image.new("RGBA", self.image.size, (0, 0, 0, 0))

    def composite(self) -> Image.Image | None:
        if self.image is None:
            return None
        base = self.image.convert("RGBA")
        if self.stroke_layer is None:
            return base
        return Image.alpha_composite(base, self.stroke_layer)

    def is_editable_image(self) -> bool:
        return self.image is not None and self.media_kind == "image"

    def load(self, path: Path, ffmpeg_location: str | None = None) -> None:
        path = Path(path)
        if not path.is_file():
            raise ValueError("El archivo no existe.")
        kind = conversion.detect_media_kind(path)
        if kind == "unknown":
            raise ValueError("Tipo de archivo no soportado en el editor.")
        self.source_path = path
        self.media_kind = kind
        self.undo_stack.clear()
        self.redo_stack.clear()
        if kind == "image":
            if path.suffix.lower() == ".svg":
                ffmpeg = conversion.find_ffmpeg(ffmpeg_location)
                if not ffmpeg:
                    raise ValueError("SVG requiere FFmpeg con soporte librsvg.")
                with tempfile.NamedTemporaryFile(suffix=".png", delete=False) as handle:
                    raster_path = Path(handle.name)
                creationflags = subprocess.CREATE_NO_WINDOW if sys.platform == "win32" else 0
                try:
                    result = subprocess.run(
                        [ffmpeg, "-y", "-hide_banner", "-loglevel", "error", "-i", str(path), str(raster_path)],
                        capture_output=True,
                        text=True,
                        creationflags=creationflags,
                    )
                    if result.returncode != 0 or not raster_path.is_file():
                        raise ValueError("No se pudo rasterizar SVG.")
                    with Image.open(raster_path) as image:
                        self.image = image.convert("RGBA")
                        self._reset_stroke_layer()
                        return
                finally:
                    if raster_path.exists():
                        raster_path.unlink(missing_ok=True)
            with Image.open(path) as image:
                if getattr(image, "n_frames", 1) > 1:
                    image.seek(0)
                self.image = image.convert("RGBA")
                self._reset_stroke_layer()
        elif kind == "video":
            self.image = _load_video_preview(path, ffmpeg_location)
            self._reset_stroke_layer()
        else:
            self.image = conversion_preview_placeholder("audio")
            self._reset_stroke_layer()

    def snapshot(self) -> None:
        if not self.is_editable_image():
            return
        layer = self.stroke_layer.copy() if self.stroke_layer is not None else None
        self.undo_stack.append((self.image.copy(), layer))
        if len(self.undo_stack) > MAX_UNDO:
            self.undo_stack.pop(0)
        self.redo_stack.clear()

    def undo(self) -> bool:
        if not self.undo_stack or not self.is_editable_image():
            return False
        layer = self.stroke_layer.copy() if self.stroke_layer is not None else None
        self.redo_stack.append((self.image.copy(), layer))
        self.image, self.stroke_layer = self.undo_stack.pop()
        if self.stroke_layer is not None:
            self.stroke_layer = self.stroke_layer.copy()
        return True

    def redo(self) -> bool:
        if not self.redo_stack or not self.is_editable_image():
            return False
        layer = self.stroke_layer.copy() if self.stroke_layer is not None else None
        self.undo_stack.append((self.image.copy(), layer))
        self.image, self.stroke_layer = self.redo_stack.pop()
        if self.stroke_layer is not None:
            self.stroke_layer = self.stroke_layer.copy()
        return True

    def rotate(self, degrees: int | float = 90) -> None:
        if not self.is_editable_image():
            return
        self.snapshot()
        self.image = editor_ops.rotate_free(self.image, float(degrees))
        if self.stroke_layer is not None:
            self.stroke_layer = editor_ops.rotate_free(self.stroke_layer, float(degrees))

    def resize_preset(
        self,
        preset: str,
        custom_width: int | None = None,
        custom_height: int | None = None,
    ) -> None:
        if not self.is_editable_image():
            return
        self.snapshot()
        self.image = editor_ops.resize_to_preset(
            self.image,
            preset,
            custom_width=custom_width,
            custom_height=custom_height,
        )
        if self.stroke_layer is not None:
            self.stroke_layer = editor_ops.resize_to_preset(
                self.stroke_layer,
                preset,
                custom_width=custom_width,
                custom_height=custom_height,
            )

    def capture_heal_reference(self) -> None:
        if self.image is not None:
            self.heal_reference = self.image.copy()

    def apply_draw(
        self,
        points: list[tuple[float, float]],
        color_hex: str,
        size: int,
        opacity: int,
        mode: str,
        erase_normal: bool = False,
    ) -> None:
        if not self.is_editable_image() or not points:
            return
        if self.stroke_layer is None:
            self._reset_stroke_layer()
        color = editor_ops.hex_to_rgba(color_hex, opacity)
        editor_ops.draw_brush_stroke(self.stroke_layer, points, color, size)

    def bucket_fill_at(
        self,
        x: float,
        y: float,
        color_hex: str,
        opacity: int,
        tolerance: int = 32,
    ) -> None:
        if not self.is_editable_image():
            return
        if self.image.mode != "RGBA":
            self.image = self.image.convert("RGBA")
        self.snapshot()
        color = editor_ops.hex_to_rgba(color_hex, opacity)
        editor_ops.bucket_fill(self.image, int(x), int(y), color, tolerance)

    def apply_eraser(
        self,
        mode: str,
        x: float,
        y: float,
        points: list[tuple[float, float]],
        tolerance: int,
        size: int,
        target_color: tuple[int, int, int, int] | None = None,
    ) -> None:
        if not self.is_editable_image():
            return
        if self.image.mode != "RGBA":
            self.image = self.image.convert("RGBA")
        if mode == "global_color":
            editor_ops.remove_color_global(self.image, int(x), int(y), tolerance)
        elif mode == "flood_region":
            editor_ops.remove_color_flood(self.image, int(x), int(y), tolerance)
        elif mode == "magic_manual" and target_color is not None:
            editor_ops.remove_color_magic(self.image, points, target_color, tolerance, size)
        elif mode == "manual":
            if self.stroke_layer is None:
                return
            editor_ops.erase_manual_stroke(self.stroke_layer, points, size)
        elif mode == "heal":
            if self.heal_reference is None:
                self.capture_heal_reference()
            if self.heal_reference is not None:
                editor_ops.heal_stroke(self.image, self.heal_reference, points, size)

    def crop(self, box: tuple[int, int, int, int]) -> None:
        if not self.is_editable_image():
            return
        left, top, right, bottom = box
        left = max(0, min(left, self.image.width))
        top = max(0, min(top, self.image.height))
        right = max(left + 1, min(right, self.image.width))
        bottom = max(top + 1, min(bottom, self.image.height))
        self.snapshot()
        if self.image.mode != "RGBA":
            self.image = self.image.convert("RGBA")
        editor_ops.mask_outside_box_inplace(self.image, (left, top, right, bottom))
        if self.stroke_layer is not None:
            editor_ops.mask_outside_box_inplace(self.stroke_layer, (left, top, right, bottom))

    def resize(self, width: int, height: int) -> None:
        if not self.is_editable_image():
            return
        width = max(1, int(width))
        height = max(1, int(height))
        self.snapshot()
        self.image = self.image.resize((width, height), Image.Resampling.LANCZOS)
        if self.stroke_layer is not None:
            self.stroke_layer = self.stroke_layer.resize((width, height), Image.Resampling.LANCZOS)

    def draw_stroke(
        self,
        points: list[tuple[float, float]],
        color: tuple[int, int, int, int],
        width: int,
        erase: bool = False,
    ) -> None:
        if not self.is_editable_image() or len(points) < 2:
            return
        if erase:
            mask = Image.new("L", self.image.size, 0)
            mask_draw = ImageDraw.Draw(mask)
            mask_draw.line(points, fill=255, width=width, joint="curve")
            alpha = self.image.getchannel("A")
            self.image.putalpha(ImageChops.subtract(alpha, mask))
            return
        draw = ImageDraw.Draw(self.image, "RGBA")
        draw.line(points, fill=color, width=width, joint="curve")

    def draw_shape(
        self,
        shape: str,
        start: tuple[float, float],
        end: tuple[float, float],
        color: tuple[int, int, int, int],
        width: int = 3,
    ) -> None:
        if not self.is_editable_image():
            return
        box = editor_ops.normalize_shape_box(start, end)
        if box is None:
            return
        left, top, right, bottom = box
        draw = ImageDraw.Draw(self.image, "RGBA")
        if shape == "rectangle":
            draw.rectangle([left, top, right, bottom], outline=color, width=width)
        elif shape == "ellipse":
            draw.ellipse([left, top, right, bottom], outline=color, width=width)
        elif shape == "line":
            draw.line([start, end], fill=color, width=width)

    def add_text(
        self,
        position: tuple[float, float],
        text: str,
        color: tuple[int, int, int, int] = (255, 255, 255, 255),
        size: int = 28,
    ) -> None:
        if not self.is_editable_image() or not text.strip():
            return
        self.snapshot()
        draw = ImageDraw.Draw(self.image, "RGBA")
        try:
            font = ImageFont.truetype("arial.ttf", size=size)
        except OSError:
            font = ImageFont.load_default()
        draw.text(position, text.strip(), fill=color, font=font)

    def save_copy(self, output_path: Path) -> Path:
        if self.image is None:
            raise ValueError("No hay imagen para guardar.")
        output_path = Path(output_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        suffix = output_path.suffix.lower()
        rendered = self.composite()
        if rendered is None:
            raise ValueError("No hay imagen para guardar.")
        if suffix in (".jpg", ".jpeg"):
            rgb = Image.new("RGB", rendered.size, (255, 255, 255))
            rgb.paste(rendered, mask=rendered.split()[3] if rendered.mode == "RGBA" else None)
            rgb.save(output_path, quality=95)
        else:
            rendered.save(output_path)
        return output_path
