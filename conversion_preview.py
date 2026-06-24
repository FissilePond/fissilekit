"""Preview thumbnails and vector-style placeholders for conversion UI."""

from __future__ import annotations

import subprocess
import sys
import tempfile
from pathlib import Path

from PIL import Image

import conversion

PREVIEW_SIZE = (200, 130)
ICON_KINDS = ("file", "image", "video", "audio")


def _icons_dir() -> Path:
    if getattr(sys, "frozen", False):
        bundled = Path(sys._MEIPASS) / "assets" / "conversion_icons"
        if bundled.is_dir():
            return bundled
    return Path(__file__).resolve().parent / "assets" / "conversion_icons"


def _fit_preview(image: Image.Image, size: tuple[int, int] = PREVIEW_SIZE) -> Image.Image:
    canvas = Image.new("RGBA", size, (0, 0, 0, 0))
    thumb = image.copy()
    if thumb.mode not in ("RGB", "RGBA"):
        thumb = thumb.convert("RGBA")
    thumb.thumbnail(size, Image.Resampling.LANCZOS)
    offset = ((size[0] - thumb.width) // 2, (size[1] - thumb.height) // 2)
    if thumb.mode == "RGBA":
        canvas.paste(thumb, offset, thumb)
    else:
        canvas.paste(thumb, offset)
    return canvas


def _transparent_canvas(size: tuple[int, int] = PREVIEW_SIZE) -> Image.Image:
    return Image.new("RGBA", size, (0, 0, 0, 0))


def _tint_icon_white(icon: Image.Image) -> Image.Image:
    tinted = icon.convert("RGBA")
    pixels = tinted.load()
    width, height = tinted.size
    for y in range(height):
        for x in range(width):
            red, green, blue, alpha = pixels[x, y]
            if alpha > 0:
                pixels[x, y] = (255, 255, 255, alpha)
    return tinted


def _compose_kind_icon(kind: str) -> Image.Image:
    kind = (kind or "file").lower()
    if kind not in ICON_KINDS:
        kind = "file"

    canvas = _transparent_canvas()
    icon_path = _icons_dir() / f"{kind}.png"
    if not icon_path.is_file():
        return canvas

    with Image.open(icon_path) as icon:
        icon_rgba = icon.convert("RGBA")
    if kind == "file":
        icon_rgba = _tint_icon_white(icon_rgba)
    icon_rgba.thumbnail((108, 88), Image.Resampling.LANCZOS)
    offset = (
        (PREVIEW_SIZE[0] - icon_rgba.width) // 2,
        (PREVIEW_SIZE[1] - icon_rgba.height) // 2,
    )
    canvas.paste(icon_rgba, offset, icon_rgba)
    return canvas


def placeholder_for_kind(kind: str) -> Image.Image:
    return _compose_kind_icon(kind)


def ui_icon(name: str, size: tuple[int, int] = (20, 20)) -> Image.Image:
    icon_path = _icons_dir() / f"{name}.png"
    if not icon_path.is_file():
        return Image.new("RGBA", size, (0, 0, 0, 0))
    with Image.open(icon_path) as icon:
        icon_rgba = icon.convert("RGBA")
    icon_rgba.thumbnail(size, Image.Resampling.LANCZOS)
    return icon_rgba


def _extract_video_thumbnail(path: Path, ffmpeg: str) -> Image.Image | None:
    with tempfile.NamedTemporaryFile(suffix=".jpg", delete=False) as handle:
        output_path = Path(handle.name)
    command = [
        ffmpeg,
        "-y",
        "-hide_banner",
        "-loglevel",
        "error",
        "-ss",
        "0.5",
        "-i",
        str(path),
        "-frames:v",
        "1",
        "-vf",
        f"scale={PREVIEW_SIZE[0]}:{PREVIEW_SIZE[1]}:force_original_aspect_ratio=decrease",
        str(output_path),
    ]
    creationflags = subprocess.CREATE_NO_WINDOW if sys.platform == "win32" else 0
    try:
        result = subprocess.run(
            command,
            capture_output=True,
            text=True,
            creationflags=creationflags,
        )
        if result.returncode != 0 or not output_path.is_file():
            return None
        with Image.open(output_path) as frame:
            return _fit_preview(frame.convert("RGBA"))
    finally:
        if output_path.exists():
            output_path.unlink(missing_ok=True)


def _load_image_preview(path: Path, ffmpeg_location: str | None) -> Image.Image:
    if path.suffix.lower() == ".svg":
        ffmpeg = conversion.find_ffmpeg(ffmpeg_location)
        if ffmpeg:
            with tempfile.NamedTemporaryFile(suffix=".png", delete=False) as handle:
                raster_path = Path(handle.name)
            try:
                command = [
                    ffmpeg,
                    "-y",
                    "-hide_banner",
                    "-loglevel",
                    "error",
                    "-i",
                    str(path),
                    str(raster_path),
                ]
                creationflags = subprocess.CREATE_NO_WINDOW if sys.platform == "win32" else 0
                result = subprocess.run(
                    command,
                    capture_output=True,
                    text=True,
                    creationflags=creationflags,
                )
                if result.returncode == 0 and raster_path.is_file():
                    with Image.open(raster_path) as frame:
                        return _fit_preview(frame.convert("RGBA"))
            finally:
                if raster_path.exists():
                    raster_path.unlink(missing_ok=True)
        return placeholder_for_kind("image")

    with Image.open(path) as opened:
        if getattr(opened, "n_frames", 1) > 1:
            opened.seek(0)
        frame = opened.convert("RGBA")
        return _fit_preview(frame)


def load_preview(path: Path | str, ffmpeg_location: str | None = None) -> Image.Image:
    source = Path(path)
    if not source.is_file():
        return placeholder_for_kind("file")

    kind = conversion.detect_media_kind(source)
    try:
        if kind == "image":
            return _load_image_preview(source, ffmpeg_location)
        if kind == "video":
            ffmpeg = conversion.find_ffmpeg(ffmpeg_location)
            if ffmpeg:
                thumbnail = _extract_video_thumbnail(source, ffmpeg)
                if thumbnail is not None:
                    return thumbnail
            return placeholder_for_kind("video")
        if kind == "audio":
            return placeholder_for_kind("audio")
    except Exception:
        if kind in ICON_KINDS:
            return placeholder_for_kind(kind)
    return placeholder_for_kind("file")
