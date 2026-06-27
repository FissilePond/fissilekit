"""Image editor session and folder scanning for FissileKit."""

from __future__ import annotations

import subprocess
import sys
import tempfile
from pathlib import Path

from PIL import Image, ImageChops, ImageDraw, ImageFont

import conversion
import editor_ops
import editor_text
import editor_video

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


def fit_image_for_display(
    image: Image.Image,
    display_width: float,
    display_height: float,
    *,
    resample: Image.Resampling = Image.Resampling.LANCZOS,
) -> Image.Image:
    target_w = max(1, int(round(display_width)))
    target_h = max(1, int(round(display_height)))
    if image.size == (target_w, target_h):
        return image
    return image.resize((target_w, target_h), resample)


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


def canvas_to_image_clamped(
    x: float,
    y: float,
    canvas_width: int,
    canvas_height: int,
    image_width: int,
    image_height: int,
) -> tuple[float, float] | None:
    if image_width <= 0 or image_height <= 0:
        return None
    scale, offset_x, offset_y, display_w, display_h = display_metrics(
        canvas_width, canvas_height, image_width, image_height
    )
    if scale <= 0:
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


def _load_video_preview(path: Path, ffmpeg_location: str | None, time_seconds: float = 0.0) -> Image.Image:
    return editor_video.extract_frame(path, time_seconds, ffmpeg_location)


def conversion_preview_placeholder(kind: str) -> Image.Image:
    import conversion_preview

    return conversion_preview.placeholder_for_kind(kind)


class EditorSession:
    def __init__(self) -> None:
        self.source_path: Path | None = None
        self.media_kind = "unknown"
        self.image: Image.Image | None = None
        self.stroke_layer: Image.Image | None = None
        self.text_objects: list[editor_text.TextObject] = []
        self.undo_stack: list[
            tuple[
                Image.Image,
                Image.Image | None,
                list[editor_text.TextObject],
                Path | None,
                float,
                float,
                int,
                float,
            ]
        ] = []
        self.redo_stack: list[
            tuple[
                Image.Image,
                Image.Image | None,
                list[editor_text.TextObject],
                Path | None,
                float,
                float,
                int,
                float,
            ]
        ] = []
        self.heal_reference: Image.Image | None = None
        self.video_duration = 0.0
        self.video_fps = 24.0
        self.video_time = 0.0
        self.video_frame_count = 0
        self._temp_video_paths: list[Path] = []

    def _clear_temp_video_paths(self) -> None:
        for path in self._temp_video_paths:
            if path.is_file():
                path.unlink(missing_ok=True)
        self._temp_video_paths.clear()

    def _register_temp_video(self, path: Path) -> None:
        self._temp_video_paths.append(path)

    def clear(self) -> None:
        self.source_path = None
        self.media_kind = "unknown"
        self.image = None
        self.stroke_layer = None
        self.text_objects = []
        self.undo_stack.clear()
        self.redo_stack.clear()
        self.video_duration = 0.0
        self.video_fps = 24.0
        self.video_time = 0.0
        self.video_frame_count = 0
        self._clear_temp_video_paths()

    def _reset_stroke_layer(self) -> None:
        if self.image is None:
            self.stroke_layer = None
            return
        self.stroke_layer = Image.new("RGBA", self.image.size, (0, 0, 0, 0))

    def composite(self, *, exclude_text_ids: set[str] | None = None) -> Image.Image | None:
        if self.image is None:
            return None
        base = self.image.convert("RGBA")
        if self.stroke_layer is not None:
            base = Image.alpha_composite(base, self.stroke_layer)
        text_layer = editor_text.render_text_layer(
            self.text_objects,
            self.image.size,
            exclude_ids=exclude_text_ids,
        )
        if text_layer is not None:
            base = Image.alpha_composite(base, text_layer)
        return base

    def is_editable_image(self) -> bool:
        return self.image is not None and self.media_kind == "image"

    def is_raster_editable(self) -> bool:
        return self.image is not None and self.media_kind in {"image", "video"}

    def is_video(self) -> bool:
        return self.media_kind == "video" and self.source_path is not None

    def current_video_frame(self) -> int:
        if self.video_fps <= 0:
            return 0
        return max(0, min(self.video_frame_count - 1, int(round(self.video_time * self.video_fps))))

    def seek_video(self, time_seconds: float, ffmpeg_location: str | None = None) -> None:
        if not self.is_video() or self.source_path is None:
            return
        clamped = max(0.0, min(float(time_seconds), max(self.video_duration, 0.001)))
        self.video_time = clamped
        self.image = _load_video_preview(self.source_path, ffmpeg_location, clamped)

    def is_cropable(self) -> bool:
        return self.image is not None and self.media_kind in {"image", "video"}

    def load(self, path: Path, ffmpeg_location: str | None = None) -> None:
        path = Path(path)
        if not path.is_file():
            raise ValueError("El archivo no existe.")
        kind = conversion.detect_media_kind(path)
        if kind == "unknown":
            raise ValueError("Tipo de archivo no soportado en el editor.")
        self.source_path = path
        self.media_kind = kind
        self._clear_temp_video_paths()
        self.undo_stack.clear()
        self.redo_stack.clear()
        self.text_objects = []
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
            info = editor_video.probe_video(path, ffmpeg_location)
            self.video_duration = info.duration
            self.video_fps = info.fps
            self.video_frame_count = info.frame_count
            self.video_time = 0.0
            self.image = _load_video_preview(path, ffmpeg_location, 0.0)
            self._reset_stroke_layer()
        else:
            self.image = conversion_preview_placeholder("audio")
            self._reset_stroke_layer()

    def _pack_undo_state(
        self,
    ) -> tuple[Image.Image, Image.Image | None, list[editor_text.TextObject], Path | None, float, float, int, float]:
        layer = self.stroke_layer.copy() if self.stroke_layer is not None else None
        texts = editor_text.copy_text_objects(self.text_objects)
        return (
            self.image.copy(),
            layer,
            texts,
            self.source_path,
            self.video_duration,
            self.video_fps,
            self.video_frame_count,
            self.video_time,
        )

    def _apply_undo_state(
        self,
        state: tuple[Image.Image, Image.Image | None, list[editor_text.TextObject], Path | None, float, float, int, float],
    ) -> None:
        image, layer, texts, source_path, duration, fps, frame_count, video_time = state
        self.image = image
        self.stroke_layer = layer.copy() if layer is not None else None
        self.text_objects = editor_text.copy_text_objects(texts)
        if self.is_video():
            self.source_path = source_path
            self.video_duration = duration
            self.video_fps = fps
            self.video_frame_count = frame_count
            self.video_time = video_time

    def snapshot(self) -> None:
        if self.image is None:
            return
        if not self.is_raster_editable():
            return
        self.undo_stack.append(self._pack_undo_state())
        if len(self.undo_stack) > MAX_UNDO:
            self.undo_stack.pop(0)
        self.redo_stack.clear()

    def undo(self) -> bool:
        if not self.undo_stack or not self.is_raster_editable():
            return False
        self.redo_stack.append(self._pack_undo_state())
        self._apply_undo_state(self.undo_stack.pop())
        return True

    def redo(self) -> bool:
        if not self.redo_stack or not self.is_raster_editable():
            return False
        self.undo_stack.append(self._pack_undo_state())
        self._apply_undo_state(self.redo_stack.pop())
        return True

    def _replace_video_source(self, new_path: Path, ffmpeg_location: str | None = None) -> None:
        self._register_temp_video(new_path)
        self.source_path = new_path
        info = editor_video.probe_video(new_path, ffmpeg_location)
        self.video_duration = info.duration
        self.video_fps = info.fps
        self.video_frame_count = info.frame_count
        self.video_time = min(self.video_time, max(self.video_duration - 0.001, 0.0))
        self.image = _load_video_preview(new_path, ffmpeg_location, self.video_time)

    def rotate(self, degrees: int | float = 90, ffmpeg_location: str | None = None) -> None:
        if self.is_video() and self.source_path is not None:
            self.snapshot()
            old_w, old_h = self.image.size
            new_path = editor_video.rotate_video_file(self.source_path, float(degrees), ffmpeg_location)
            self._replace_video_source(new_path, ffmpeg_location)
            if self.stroke_layer is not None:
                self.stroke_layer = editor_ops.rotate_free(self.stroke_layer, float(degrees))
            editor_text.rotate_text_objects(self.text_objects, old_w, old_h, float(degrees))
            return
        if not self.is_raster_editable():
            return
        self.snapshot()
        old_w, old_h = self.image.size
        self.image, self.stroke_layer = editor_ops.rotate_image_and_stroke(
            self.image,
            self.stroke_layer,
            float(degrees),
        )
        editor_text.rotate_text_objects(self.text_objects, old_w, old_h, float(degrees))

    def flip_horizontal(self, ffmpeg_location: str | None = None) -> None:
        if self.is_video() and self.source_path is not None:
            self.snapshot()
            width, _height = self.image.size
            new_path = editor_video.flip_video_file(self.source_path, "horizontal", ffmpeg_location)
            self._replace_video_source(new_path, ffmpeg_location)
            if self.stroke_layer is not None:
                self.stroke_layer = editor_ops.flip_horizontal(self.stroke_layer)
            editor_text.flip_text_objects_horizontal(self.text_objects, width)
            return
        if not self.is_raster_editable():
            return
        self.snapshot()
        width, height = self.image.size
        self.image = editor_ops.flip_horizontal(self.image)
        if self.stroke_layer is not None:
            self.stroke_layer = editor_ops.flip_horizontal(self.stroke_layer)
        editor_text.flip_text_objects_horizontal(self.text_objects, width)

    def flip_vertical(self, ffmpeg_location: str | None = None) -> None:
        if self.is_video() and self.source_path is not None:
            self.snapshot()
            _width, height = self.image.size
            new_path = editor_video.flip_video_file(self.source_path, "vertical", ffmpeg_location)
            self._replace_video_source(new_path, ffmpeg_location)
            if self.stroke_layer is not None:
                self.stroke_layer = editor_ops.flip_vertical(self.stroke_layer)
            editor_text.flip_text_objects_vertical(self.text_objects, height)
            return
        if not self.is_raster_editable():
            return
        self.snapshot()
        width, height = self.image.size
        self.image = editor_ops.flip_vertical(self.image)
        if self.stroke_layer is not None:
            self.stroke_layer = editor_ops.flip_vertical(self.stroke_layer)
        editor_text.flip_text_objects_vertical(self.text_objects, height)

    def resize_preset(
        self,
        preset: str,
        custom_width: int | None = None,
        custom_height: int | None = None,
    ) -> None:
        if not self.is_raster_editable():
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

    def resize_scale(
        self,
        target_width: int,
        target_height: int,
        lock_aspect: bool = True,
        ffmpeg_location: str | None = None,
    ) -> None:
        if self.is_video() and self.source_path is not None:
            self.snapshot()
            old_w, old_h = self.image.size
            new_w, new_h = editor_ops.resolve_scale_dimensions(
                old_w,
                old_h,
                target_width,
                target_height,
                lock_aspect=lock_aspect,
            )
            new_path = editor_video.scale_video_file(self.source_path, new_w, new_h, ffmpeg_location)
            self._replace_video_source(new_path, ffmpeg_location)
            if self.stroke_layer is not None:
                self.stroke_layer = editor_ops.resize_scale_image(
                    self.stroke_layer,
                    new_w,
                    new_h,
                    lock_aspect=False,
                )
            if old_w > 0 and old_h > 0:
                editor_text.scale_text_objects(
                    self.text_objects,
                    new_w / old_w,
                    new_h / old_h,
                )
            return
        if not self.is_raster_editable():
            return
        self.snapshot()
        old_w, old_h = self.image.size
        self.image = editor_ops.resize_scale_image(
            self.image,
            target_width,
            target_height,
            lock_aspect=lock_aspect,
        )
        if self.stroke_layer is not None:
            self.stroke_layer = editor_ops.resize_scale_image(
                self.stroke_layer,
                target_width,
                target_height,
                lock_aspect=lock_aspect,
            )
        new_w, new_h = self.image.size
        if old_w > 0 and old_h > 0:
            editor_text.scale_text_objects(
                self.text_objects,
                new_w / old_w,
                new_h / old_h,
            )

    def apply_canvas_layout(
        self,
        canvas_width: int,
        canvas_height: int,
        placement_x: float,
        placement_y: float,
        content_scale: float,
        source_image: Image.Image | None = None,
        source_stroke: Image.Image | None = None,
    ) -> None:
        if not self.is_editable_image():
            return
        self.snapshot()
        base_image = source_image if source_image is not None else self.image
        stroke_image = source_stroke if source_stroke is not None else self.stroke_layer
        self.image, self.stroke_layer = editor_ops.compose_canvas_layout(
            base_image,
            stroke_image,
            canvas_width,
            canvas_height,
            placement_x,
            placement_y,
            content_scale,
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
        if not self.is_raster_editable() or not points:
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
        if not self.is_raster_editable():
            return
        if self.stroke_layer is None:
            self._reset_stroke_layer()
        composite = self.composite()
        if composite is None:
            return
        self.snapshot()
        color = editor_ops.hex_to_rgba(color_hex, opacity)
        editor_ops.bucket_fill_stroke_from_composite(
            self.stroke_layer,
            composite,
            int(x),
            int(y),
            color,
            tolerance,
        )

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
        if not self.is_raster_editable():
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
            editor_ops.erase_manual_stroke(self.image, points, size)
        elif mode == "manual_stroke":
            if self.stroke_layer is None:
                return
            editor_ops.erase_manual_stroke(self.stroke_layer, points, size)
        elif mode == "heal":
            if self.heal_reference is None:
                return
            editor_ops.heal_stroke(self.image, self.heal_reference, points, size)

    def crop(self, box: tuple[int, int, int, int], ffmpeg_location: str | None = None) -> None:
        if not self.is_cropable():
            return
        left, top, right, bottom = box
        left = max(0, min(left, self.image.width))
        top = max(0, min(top, self.image.height))
        right = max(left + 1, min(right, self.image.width))
        bottom = max(top + 1, min(bottom, self.image.height))
        if right - left >= self.image.width and bottom - top >= self.image.height and left == 0 and top == 0:
            return
        self.snapshot()
        if self.media_kind == "video":
            if self.source_path is None:
                raise ValueError("No hay video de origen.")
            new_path = editor_video.crop_video_file(self.source_path, (left, top, right, bottom), ffmpeg_location)
            self._replace_video_source(new_path, ffmpeg_location)
            if self.stroke_layer is not None:
                self.stroke_layer = self.stroke_layer.crop((left, top, right, bottom))
            self.text_objects = editor_text.crop_text_objects(self.text_objects, left, top)
            return
        if self.image.mode != "RGBA":
            self.image = self.image.convert("RGBA")
        self.image = self.image.crop((left, top, right, bottom))
        if self.stroke_layer is not None:
            self.stroke_layer = self.stroke_layer.crop((left, top, right, bottom))
        self.text_objects = editor_text.crop_text_objects(self.text_objects, left, top)

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
        if not self.is_raster_editable() or len(points) < 2:
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

    def draw_shape_form(
        self,
        kind: str,
        start: tuple[float, float],
        end: tuple[float, float] | None = None,
        curve_points: list[tuple[float, float]] | None = None,
        *,
        fill_enabled: bool = False,
        fill_hex: str = "#ffffff",
        fill_opacity: int = 100,
        stroke_enabled: bool = True,
        stroke_hex: str = "#ffffff",
        stroke_opacity: int = 100,
        stroke_width: int = 3,
    ) -> None:
        if not self.is_raster_editable():
            return
        self.snapshot()
        if self.stroke_layer is None:
            self._reset_stroke_layer()
        fill_rgba = editor_ops.hex_to_rgba(fill_hex, fill_opacity) if fill_enabled else (0, 0, 0, 0)
        stroke_rgba = editor_ops.hex_to_rgba(stroke_hex, stroke_opacity) if stroke_enabled else (0, 0, 0, 0)
        editor_ops.render_shape(
            self.stroke_layer,
            kind,
            start,
            end,
            curve_points,
            fill_enabled=fill_enabled,
            fill_rgba=fill_rgba,
            stroke_enabled=stroke_enabled,
            stroke_rgba=stroke_rgba,
            stroke_width=stroke_width,
        )

    def draw_shape(
        self,
        shape: str,
        start: tuple[float, float],
        end: tuple[float, float],
        color: tuple[int, int, int, int],
        width: int = 3,
    ) -> None:
        if not self.is_raster_editable():
            return
        red, green, blue = color[0], color[1], color[2]
        opacity = int(color[3] * 100 / 255) if len(color) > 3 else 100
        self.draw_shape_form(
            "rectangle" if shape == "rectangle" else shape,
            start,
            end,
            fill_enabled=False,
            stroke_enabled=True,
            stroke_hex=f"#{red:02x}{green:02x}{blue:02x}",
            stroke_opacity=opacity,
            stroke_width=width,
        )

    def add_text_object(self, obj: editor_text.TextObject) -> None:
        if not self.is_raster_editable():
            return
        self.snapshot()
        self.text_objects.append(obj)

    def update_text_object(self, obj_id: str, **fields) -> None:
        if not self.is_raster_editable():
            return
        for obj in self.text_objects:
            if obj.id == obj_id:
                for key, value in fields.items():
                    setattr(obj, key, value)
                return

    def remove_text_object(self, obj_id: str) -> None:
        if not self.is_raster_editable():
            return
        self.snapshot()
        self.text_objects = [obj for obj in self.text_objects if obj.id != obj_id]

    def get_text_object(self, obj_id: str) -> editor_text.TextObject | None:
        for obj in self.text_objects:
            if obj.id == obj_id:
                return obj
        return None

    def add_text(
        self,
        position: tuple[float, float],
        text: str,
        color: tuple[int, int, int, int] = (255, 255, 255, 255),
        size: int = 28,
    ) -> None:
        if not self.is_raster_editable() or not text.strip():
            return
        red, green, blue = color[0], color[1], color[2]
        self.add_text_object(
            editor_text.new_text_object(
                position[0],
                position[1],
                text=text.strip(),
                font_size=float(size),
                color=f"#{red:02x}{green:02x}{blue:02x}",
            )
        )

    def render_overlay_layer(self) -> Image.Image | None:
        if self.image is None:
            return None
        overlay = Image.new("RGBA", self.image.size, (0, 0, 0, 0))
        if self.stroke_layer is not None:
            overlay = Image.alpha_composite(overlay, self.stroke_layer)
        text_layer = editor_text.render_text_layer(self.text_objects, self.image.size)
        if text_layer is not None:
            overlay = Image.alpha_composite(overlay, text_layer)
        if overlay.getbbox() is None:
            return None
        return overlay

    def save_video(self, output_path: Path, ffmpeg_location: str | None = None) -> Path:
        if not self.is_video() or self.source_path is None:
            raise ValueError("No hay video para guardar.")
        output_path = Path(output_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        overlay = self.render_overlay_layer()
        if overlay is None:
            return editor_video.copy_video_file(self.source_path, output_path)
        with tempfile.NamedTemporaryFile(suffix=".png", delete=False) as handle:
            overlay_path = Path(handle.name)
        try:
            overlay.save(overlay_path)
            return editor_video.export_video_with_overlay(
                self.source_path,
                overlay_path,
                output_path,
                ffmpeg_location,
            )
        finally:
            if overlay_path.exists():
                overlay_path.unlink(missing_ok=True)

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
