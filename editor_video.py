"""FFmpeg helpers for video editing in the FissileKit editor."""

from __future__ import annotations

import json
import subprocess
import sys
import tempfile
from dataclasses import dataclass
from fractions import Fraction
from pathlib import Path

from PIL import Image

import conversion


@dataclass
class VideoInfo:
    duration: float
    fps: float
    width: int
    height: int
    frame_count: int


def _creationflags() -> int:
    return subprocess.CREATE_NO_WINDOW if sys.platform == "win32" else 0


def find_ffprobe(ffmpeg_location: str | None = None) -> str | None:
    ffmpeg = conversion.find_ffmpeg(ffmpeg_location)
    if not ffmpeg:
        return None
    candidate = Path(ffmpeg).with_name("ffprobe.exe" if sys.platform == "win32" else "ffprobe")
    if candidate.is_file():
        return str(candidate)
    return "ffprobe"


def probe_video(path: Path, ffmpeg_location: str | None = None) -> VideoInfo:
    ffprobe = find_ffprobe(ffmpeg_location)
    if not ffprobe:
        raise ValueError("Se requiere FFmpeg (ffprobe) para editar video.")

    command = [
        ffprobe,
        "-v",
        "error",
        "-select_streams",
        "v:0",
        "-show_entries",
        "stream=width,height,r_frame_rate,avg_frame_rate,nb_frames,duration",
        "-show_entries",
        "format=duration",
        "-of",
        "json",
        str(path),
    ]
    result = subprocess.run(
        command,
        capture_output=True,
        text=True,
        creationflags=_creationflags(),
    )
    if result.returncode != 0:
        detail = (result.stderr or result.stdout or "").strip()
        raise ValueError(detail or "No se pudo leer el video.")

    payload = json.loads(result.stdout or "{}")
    streams = payload.get("streams") or []
    if not streams:
        raise ValueError("El archivo no contiene pista de video.")
    stream = streams[0]

    width = int(stream.get("width") or 0)
    height = int(stream.get("height") or 0)
    rate_text = stream.get("avg_frame_rate") or stream.get("r_frame_rate") or "24/1"
    try:
        fps = float(Fraction(rate_text))
    except (ValueError, ZeroDivisionError):
        fps = 24.0
    if fps <= 0:
        fps = 24.0

    duration = stream.get("duration")
    if duration in (None, "N/A"):
        duration = (payload.get("format") or {}).get("duration")
    duration = float(duration or 0.0)
    if duration <= 0:
        duration = 1.0

    frame_count = stream.get("nb_frames")
    if frame_count in (None, "N/A"):
        frame_count = max(1, int(round(duration * fps)))
    else:
        frame_count = max(1, int(frame_count))

    return VideoInfo(
        duration=duration,
        fps=fps,
        width=width,
        height=height,
        frame_count=frame_count,
    )


def extract_frame(
    path: Path,
    time_seconds: float,
    ffmpeg_location: str | None = None,
) -> Image.Image:
    ffmpeg = conversion.find_ffmpeg(ffmpeg_location)
    if not ffmpeg:
        import conversion_preview

        return conversion_preview.placeholder_for_kind("video")

    time_seconds = max(0.0, float(time_seconds))
    with tempfile.NamedTemporaryFile(suffix=".png", delete=False) as handle:
        raster_path = Path(handle.name)
    try:
        result = subprocess.run(
            [
                ffmpeg,
                "-y",
                "-hide_banner",
                "-loglevel",
                "error",
                "-ss",
                f"{time_seconds:.3f}",
                "-i",
                str(path),
                "-frames:v",
                "1",
                "-q:v",
                "2",
                str(raster_path),
            ],
            capture_output=True,
            text=True,
            creationflags=_creationflags(),
        )
        if result.returncode != 0 or not raster_path.is_file():
            import conversion_preview

            return conversion_preview.placeholder_for_kind("video")
        with Image.open(raster_path) as image:
            return image.convert("RGBA")
    finally:
        if raster_path.exists():
            raster_path.unlink(missing_ok=True)


def _transcode_video(
    input_path: Path,
    output_path: Path,
    vf_filter: str | None,
    ffmpeg_location: str | None,
) -> None:
    ffmpeg = conversion.find_ffmpeg(ffmpeg_location)
    if not ffmpeg:
        raise ValueError("Se requiere FFmpeg para editar video.")

    command = [
        ffmpeg,
        "-y",
        "-hide_banner",
        "-loglevel",
        "error",
        "-i",
        str(input_path),
    ]
    if vf_filter:
        command.extend(["-vf", vf_filter])
    command.extend(["-c:v", "libx264", "-preset", "fast", "-crf", "18", "-c:a", "copy", str(output_path)])
    result = subprocess.run(
        command,
        capture_output=True,
        text=True,
        creationflags=_creationflags(),
    )
    if result.returncode != 0 or not output_path.is_file():
        detail = (result.stderr or result.stdout or "").strip()
        raise ValueError(detail or "No se pudo procesar el video.")


def _with_temp_output(input_path: Path, suffix: str) -> tuple[Path, Path]:
    output_path = input_path.with_suffix(f".edit{suffix}")
    if output_path.exists():
        output_path.unlink(missing_ok=True)
    return input_path, output_path


def crop_video_file(
    input_path: Path,
    box: tuple[int, int, int, int],
    ffmpeg_location: str | None = None,
) -> Path:
    left, top, right, bottom = box
    crop_w = right - left
    crop_h = bottom - top
    crop_w -= crop_w % 2
    crop_h -= crop_h % 2
    if crop_w < 2 or crop_h < 2:
        raise ValueError("Area de recorte demasiado pequena para video.")
    suffix = input_path.suffix.lower() or ".mp4"
    with tempfile.NamedTemporaryFile(suffix=suffix, delete=False) as handle:
        output_path = Path(handle.name)
    _transcode_video(
        input_path,
        output_path,
        f"crop={crop_w}:{crop_h}:{left}:{top}",
        ffmpeg_location,
    )
    return output_path


def rotate_video_file(
    input_path: Path,
    degrees: float,
    ffmpeg_location: str | None = None,
) -> Path:
    angle = float(degrees) % 360.0
    if abs(angle) < 0.01:
        return input_path
    suffix = input_path.suffix.lower() or ".mp4"
    with tempfile.NamedTemporaryFile(suffix=suffix, delete=False) as handle:
        output_path = Path(handle.name)

    if abs(angle - 90.0) < 0.01:
        vf = "transpose=1"
    elif abs(angle + 90.0) < 0.01 or abs(angle - 270.0) < 0.01:
        vf = "transpose=2"
    elif abs(angle - 180.0) < 0.01:
        vf = "transpose=1,transpose=1"
    else:
        radians = angle * 3.141592653589793 / 180.0
        vf = f"rotate={radians}:fillcolor=black@0"
    _transcode_video(input_path, output_path, vf, ffmpeg_location)
    return output_path


def flip_video_file(
    input_path: Path,
    direction: str,
    ffmpeg_location: str | None = None,
) -> Path:
    vf = "hflip" if direction == "horizontal" else "vflip"
    suffix = input_path.suffix.lower() or ".mp4"
    with tempfile.NamedTemporaryFile(suffix=suffix, delete=False) as handle:
        output_path = Path(handle.name)
    _transcode_video(input_path, output_path, vf, ffmpeg_location)
    return output_path


def scale_video_file(
    input_path: Path,
    width: int,
    height: int,
    ffmpeg_location: str | None = None,
) -> Path:
    width = max(2, int(width))
    height = max(2, int(height))
    width -= width % 2
    height -= height % 2
    suffix = input_path.suffix.lower() or ".mp4"
    with tempfile.NamedTemporaryFile(suffix=suffix, delete=False) as handle:
        output_path = Path(handle.name)
    _transcode_video(
        input_path,
        output_path,
        f"scale={width}:{height}",
        ffmpeg_location,
    )
    return output_path


def export_video_with_overlay(
    video_path: Path,
    overlay_path: Path,
    output_path: Path,
    ffmpeg_location: str | None = None,
) -> Path:
    ffmpeg = conversion.find_ffmpeg(ffmpeg_location)
    if not ffmpeg:
        raise ValueError("Se requiere FFmpeg para exportar video.")

    command = [
        ffmpeg,
        "-y",
        "-hide_banner",
        "-loglevel",
        "error",
        "-i",
        str(video_path),
        "-i",
        str(overlay_path),
        "-filter_complex",
        "[0:v][1:v]overlay=0:0",
        "-c:v",
        "libx264",
        "-preset",
        "fast",
        "-crf",
        "18",
        "-c:a",
        "copy",
        str(output_path),
    ]
    result = subprocess.run(
        command,
        capture_output=True,
        text=True,
        creationflags=_creationflags(),
    )
    if result.returncode != 0 or not output_path.is_file():
        detail = (result.stderr or result.stdout or "").strip()
        raise ValueError(detail or "No se pudo exportar el video.")
    return output_path


def copy_video_file(source_path: Path, output_path: Path) -> Path:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    if source_path.resolve() == output_path.resolve():
        return output_path
    data = source_path.read_bytes()
    output_path.write_bytes(data)
    return output_path
