"""Media conversion helpers for FissileKit."""

from __future__ import annotations

import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

from PIL import Image

try:
    from potrace import Bitmap as PotraceBitmap
except ImportError:
    PotraceBitmap = None

VIDEO_EXTENSIONS = {
    ".mp4",
    ".webm",
    ".mov",
    ".mkv",
    ".avi",
    ".mxf",
    ".wmv",
    ".flv",
    ".mpg",
    ".mpeg",
    ".m4v",
    ".ts",
}
AUDIO_EXTENSIONS = {
    ".mp3",
    ".wav",
    ".m4a",
    ".aac",
    ".flac",
    ".ogg",
    ".opus",
    ".mka",
    ".aiff",
    ".aif",
    ".wma",
}
IMAGE_EXTENSIONS = {
    ".png",
    ".jpg",
    ".jpeg",
    ".webp",
    ".gif",
    ".svg",
    ".tiff",
    ".tif",
    ".bmp",
    ".apng",
}

VIDEO_TARGETS = ("mp4", "webm", "mov", "mkv", "avi", "mxf", "wmv", "flv", "mpg")
AUDIO_TARGETS = ("mp3", "wav", "m4a", "flac", "ogg", "mka", "aiff", "wma")
IMAGE_TARGETS = ("png", "jpg", "webp", "gif", "bmp", "tiff", "apng", "svg")
SPECTROGRAM_TARGETS = ("png", "jpg", "webp")

IMAGE_STILL_VIDEO_SECONDS = 5
BLACK_VIDEO_WIDTH = 1280
BLACK_VIDEO_HEIGHT = 720
BLACK_VIDEO_SIZE = f"{BLACK_VIDEO_WIDTH}x{BLACK_VIDEO_HEIGHT}"
BLACK_VIDEO_FPS = 25

COMMON_FFMPEG_LOCATIONS = (
    Path(r"C:\ffmpeg\bin\ffmpeg.exe"),
    Path(r"C:\ffmpeg\ffmpeg.exe"),
    Path(r"C:\Program Files\Kdenlive\bin\ffmpeg.exe"),
    Path(r"C:\Program Files\ffmpeg\bin\ffmpeg.exe"),
)

ALL_INPUT_EXTENSIONS = sorted(VIDEO_EXTENSIONS | AUDIO_EXTENSIONS | IMAGE_EXTENSIONS)

FORMAT_GROUPS = {
    "image": IMAGE_TARGETS + VIDEO_TARGETS + AUDIO_TARGETS,
    "video": VIDEO_TARGETS + AUDIO_TARGETS,
    "audio": AUDIO_TARGETS + VIDEO_TARGETS + SPECTROGRAM_TARGETS,
}

VIDEO_QUALITY_PRESETS = {
    "baja": {"height": 480, "crf": 28, "label_key": "quality_baja"},
    "media": {"height": 720, "crf": 23, "label_key": "quality_media"},
    "alta": {"height": 1080, "crf": 18, "label_key": "quality_alta"},
}

OUTPUT_EXTENSION = {
    "mp4": ".mp4",
    "webm": ".webm",
    "mov": ".mov",
    "mkv": ".mkv",
    "avi": ".avi",
    "mxf": ".mxf",
    "wmv": ".wmv",
    "flv": ".flv",
    "mpg": ".mpg",
    "mpeg": ".mpg",
    "mp3": ".mp3",
    "wav": ".wav",
    "m4a": ".m4a",
    "aac": ".m4a",
    "flac": ".flac",
    "ogg": ".ogg",
    "opus": ".ogg",
    "mka": ".mka",
    "aiff": ".aiff",
    "aif": ".aiff",
    "wma": ".wma",
    "png": ".png",
    "jpg": ".jpg",
    "jpeg": ".jpg",
    "webp": ".webp",
    "gif": ".gif",
    "bmp": ".bmp",
    "tiff": ".tiff",
    "tif": ".tiff",
    "apng": ".png",
    "svg": ".svg",
}


class ConversionError(Exception):
    pass


def normalize_format_name(value: str) -> str:
    cleaned = (value or "").strip().lower().lstrip(".")
    aliases = {
        "jpeg": "jpg",
        "mpeg": "mpg",
        "aac": "m4a",
        "opus": "ogg",
        "tif": "tiff",
        "aif": "aiff",
    }
    return aliases.get(cleaned, cleaned)


def detect_media_kind(path: Path) -> str:
    extension = path.suffix.lower()
    if extension in IMAGE_EXTENSIONS:
        return "image"
    if extension in VIDEO_EXTENSIONS:
        return "video"
    if extension in AUDIO_EXTENSIONS:
        return "audio"
    return "unknown"


def target_formats_for_kind(kind: str) -> tuple[str, ...]:
    return FORMAT_GROUPS.get(kind, ())


def is_target_allowed(kind: str, target_format: str, source_path: Path | None = None) -> bool:
    target = normalize_format_name(target_format)
    if target not in target_formats_for_kind(kind):
        return False
    if kind == "audio" and target in IMAGE_TARGETS and target not in SPECTROGRAM_TARGETS:
        return False
    if target == "svg" and kind != "image":
        return False
    return True


def conversion_needs_ffmpeg(kind: str, source_path: Path | None, target_format: str) -> bool:
    target = normalize_format_name(target_format)
    if kind == "video":
        return True
    if kind == "audio":
        return target in VIDEO_TARGETS or target in SPECTROGRAM_TARGETS
    if kind == "image":
        if target in VIDEO_TARGETS or target == "apng":
            return True
        if target in AUDIO_TARGETS and target != "wav":
            return True
        if source_path is not None and source_path.suffix.lower() == ".svg" and target != "svg":
            return True
    return False


def output_extension(target_format: str) -> str:
    return OUTPUT_EXTENSION.get(normalize_format_name(target_format), f".{normalize_format_name(target_format)}")


def _known_output_suffixes() -> tuple[str, ...]:
    suffixes = {ext.lower() for ext in ALL_INPUT_EXTENSIONS}
    for fmt in IMAGE_TARGETS + VIDEO_TARGETS + AUDIO_TARGETS:
        suffixes.add(output_extension(fmt).lower())
    return tuple(sorted(suffixes, key=len, reverse=True))


def conversion_output_basename(source: Path) -> str:
    """Strip all known media extensions so IMG_5093.JPG -> webp becomes IMG_5093.webp."""
    base = source.name
    while base:
        lowered = base.lower()
        stripped = False
        for suffix in _known_output_suffixes():
            if lowered.endswith(suffix):
                base = base[: -len(suffix)]
                stripped = True
                break
        if not stripped:
            break
    base = base.strip(" .")
    invalid_chars = '<>:"/\\|?*'
    clean = "".join("_" if ch in invalid_chars or ord(ch) < 32 else ch for ch in base)
    return clean[:120] or "archivo"


def find_ffmpeg(ffmpeg_location: str | None = None) -> str | None:
    if ffmpeg_location:
        candidate = Path(ffmpeg_location)
        if candidate.is_file():
            return str(candidate)
    found = shutil.which("ffmpeg")
    if found:
        return found
    for candidate in COMMON_FFMPEG_LOCATIONS:
        if candidate.is_file():
            return str(candidate)
    for name in ("ffmpeg.exe", "ffmpeg"):
        for folder in (Path.cwd(), Path(__file__).resolve().parent):
            candidate = folder / name
            if candidate.is_file():
                return str(candidate)
    return None


def _run_ffmpeg(command: list[str]) -> None:
    creationflags = subprocess.CREATE_NO_WINDOW if sys.platform == "win32" else 0
    result = subprocess.run(
        command,
        capture_output=True,
        text=True,
        creationflags=creationflags,
    )
    if result.returncode != 0:
        details = (result.stderr or result.stdout or "").strip()
        raise ConversionError(details or "FFmpeg fallo durante la conversion.")


def _ensure_unique_path(path: Path) -> Path:
    if not path.exists():
        return path
    stem = path.stem
    suffix = path.suffix
    index = 2
    while True:
        candidate = path.with_name(f"{stem} ({index}){suffix}")
        if not candidate.exists():
            return candidate
        index += 1


def _is_animated_image(path: Path) -> bool:
    if path.suffix.lower() == ".svg":
        return False
    try:
        with Image.open(path) as image:
            return getattr(image, "n_frames", 1) > 1
    except Exception:
        return False


def _load_animated_frames(path: Path) -> tuple[list[Image.Image], list[int], str | None]:
    frames: list[Image.Image] = []
    durations: list[int] = []
    with Image.open(path) as image:
        source_format = (image.format or path.suffix.lstrip(".")).upper()
        frame_count = getattr(image, "n_frames", 1)
        for index in range(frame_count):
            image.seek(index)
            frame = image.convert("RGBA")
            frames.append(frame.copy())
            durations.append(int(image.info.get("duration", image.info.get("delay", 100)) or 100))
    return frames, durations, source_format


def _save_static_image(image: Image.Image, target_format: str, output_path: Path) -> None:
    fmt = normalize_format_name(target_format)
    pillow_format = {
        "jpg": "JPEG",
        "png": "PNG",
        "webp": "WEBP",
        "gif": "GIF",
        "bmp": "BMP",
        "tiff": "TIFF",
    }[fmt]

    save_image = image
    if fmt == "jpg" and save_image.mode in ("RGBA", "LA", "P"):
        save_image = save_image.convert("RGB")

    save_kwargs: dict = {}
    if fmt == "jpg":
        save_kwargs["quality"] = 90
    elif fmt == "webp":
        save_kwargs["quality"] = 85

    save_image.save(output_path, format=pillow_format, **save_kwargs)


def _path_to_svg_document(path, width: int, height: int) -> str:
    parts: list[str] = []
    for curve in path:
        start = curve.start_point
        if start is None:
            continue
        parts.append(f"M{start.x:.2f},{start.y:.2f}")
        for segment in curve:
            if segment.is_corner:
                end = segment.end_point
                parts.append(f"L{end.x:.2f},{end.y:.2f}")
            else:
                c1, c2, end = segment.c1, segment.c2, segment.end_point
                parts.append(
                    f"C{c1.x:.2f},{c1.y:.2f} {c2.x:.2f},{c2.y:.2f} {end.x:.2f},{end.y:.2f}"
                )
        parts.append("z")
    path_data = " ".join(parts)
    return (
        '<?xml version="1.0" encoding="UTF-8"?>\n'
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" '
        f'viewBox="0 0 {width} {height}">\n'
        f'  <path fill="#000000" stroke="none" d="{path_data}"/>\n'
        "</svg>\n"
    )


def _convert_image_to_svg(input_path: Path, output_path: Path) -> Path:
    if PotraceBitmap is None:
        raise ConversionError(
            "NO PUDE: falta la dependencia potracer. Instala requirements.txt."
        )

    with Image.open(input_path) as image:
        if _is_animated_image(input_path):
            image.seek(0)
        gray = image.convert("L")
        max_dim = 900
        if max(gray.size) > max_dim:
            gray.thumbnail((max_dim, max_dim), Image.Resampling.LANCZOS)
        width, height = gray.size
        bitmap = PotraceBitmap(gray, blacklevel=0.5)
        traced = bitmap.trace(turdsize=2)

    output_path.write_text(_path_to_svg_document(traced, width, height), encoding="utf-8")
    return output_path


def _convert_image_pillow(input_path: Path, target_format: str, output_path: Path) -> Path:
    target = normalize_format_name(target_format)
    if target == "svg":
        return _convert_image_to_svg(input_path, output_path)
    if target == "apng":
        return _convert_image_apng(input_path, output_path)

    animated = _is_animated_image(input_path)
    if animated and target in ("gif", "webp"):
        frames, durations, _source_format = _load_animated_frames(input_path)
        if target == "gif":
            rgb_frames = [frame.convert("P", palette=Image.ADAPTIVE) for frame in frames]
            rgb_frames[0].save(
                output_path,
                format="GIF",
                save_all=True,
                append_images=rgb_frames[1:],
                duration=durations,
                loop=0,
                disposal=2,
            )
            return output_path

        output_path = output_path.with_suffix(".webp")
        frames[0].save(
            output_path,
            format="WEBP",
            save_all=True,
            append_images=frames[1:],
            duration=durations,
            loop=0,
            quality=85,
            method=6,
        )
        return output_path

    if animated and target in ("png", "jpg", "bmp", "tiff"):
        frames, durations, _source_format = _load_animated_frames(input_path)
        if target == "png":
            frames[0].save(output_path, format="PNG")
            return output_path
        _save_static_image(frames[0], target, output_path)
        return output_path

    with Image.open(input_path) as image:
        if input_path.suffix.lower() == ".svg":
            raise ConversionError("NO PUDE: no se pudo rasterizar SVG con las herramientas disponibles.")
        frame = image.convert("RGBA") if target in ("png", "webp", "gif") else image
        _save_static_image(frame, target, output_path)
    return output_path


def _convert_image_apng(input_path: Path, output_path: Path) -> Path:
    ffmpeg = find_ffmpeg()
    if not ffmpeg:
        raise ConversionError("NO PUDE: APNG requiere FFmpeg instalado y en el PATH.")

    output_path = output_path.with_suffix(".png")
    command = [
        ffmpeg,
        "-y",
        "-hide_banner",
        "-loglevel",
        "error",
        "-i",
        str(input_path),
        "-plays",
        "0",
        "-f",
        "apng",
        str(output_path),
    ]
    try:
        _run_ffmpeg(command)
    except ConversionError as error:
        raise ConversionError(f"NO PUDE: no se pudo crear APNG. {error}") from error
    if not output_path.exists():
        raise ConversionError("NO PUDE: FFmpeg no genero el archivo APNG.")
    return output_path


def _convert_svg_input(
    input_path: Path,
    target_format: str,
    output_path: Path,
    ffmpeg: str,
    duration_seconds: float = IMAGE_STILL_VIDEO_SECONDS,
    quality_key: str = "media",
    ffmpeg_location: str | None = None,
    progress_callback=None,
) -> Path:
    target = normalize_format_name(target_format)
    if target == "svg":
        return shutil.copy2(input_path, output_path)

    if target in VIDEO_TARGETS:
        with tempfile.TemporaryDirectory() as temp_dir:
            raster_path = Path(temp_dir) / f"{input_path.stem}.png"
            _convert_svg_input(input_path, "png", raster_path, ffmpeg)
            return _convert_image_to_video(
                raster_path,
                target,
                output_path,
                ffmpeg,
                duration_seconds=duration_seconds,
                quality_key=quality_key,
            )

    if target in AUDIO_TARGETS:
        from conversion_image_audio import convert_image_to_audio

        with tempfile.TemporaryDirectory() as temp_dir:
            raster_path = Path(temp_dir) / f"{input_path.stem}.png"
            _convert_svg_input(input_path, "png", raster_path, ffmpeg)
            return convert_image_to_audio(
                raster_path,
                target,
                output_path,
                ffmpeg_location=ffmpeg_location or ffmpeg,
                progress_callback=progress_callback,
            )

    command = [
        ffmpeg,
        "-y",
        "-hide_banner",
        "-loglevel",
        "error",
        "-i",
        str(input_path),
        str(output_path),
    ]
    try:
        _run_ffmpeg(command)
    except ConversionError as error:
        raise ConversionError(
            f"NO PUDE: no se pudo rasterizar SVG. Asegurate de tener FFmpeg con soporte librsvg. {error}"
        ) from error
    if not output_path.exists():
        raise ConversionError("NO PUDE: no se pudo rasterizar SVG con FFmpeg.")
    if target == "apng":
        return _convert_image_apng(output_path, output_path)
    return output_path


def _still_video_filter(height: int = BLACK_VIDEO_HEIGHT) -> str:
    return (
        f"scale={BLACK_VIDEO_WIDTH}:{height}:force_original_aspect_ratio=decrease,"
        f"pad={BLACK_VIDEO_WIDTH}:{height}:(ow-iw)/2:(oh-ih)/2:black"
    )


def _video_quality_settings(quality_key: str) -> dict:
    return VIDEO_QUALITY_PRESETS.get(quality_key, VIDEO_QUALITY_PRESETS["media"])


def _image_to_video_codec_args(target_format: str, crf: int) -> list[str]:
    target = normalize_format_name(target_format)
    mapping = {
        "mp4": ["-c:v", "libx264", "-preset", "medium", "-crf", str(crf), "-movflags", "+faststart"],
        "webm": ["-c:v", "libvpx-vp9", "-crf", str(min(crf + 8, 40)), "-b:v", "0"],
        "mov": ["-c:v", "libx264", "-crf", str(crf), "-f", "mov"],
        "mkv": ["-c:v", "libx264", "-crf", str(crf), "-f", "matroska"],
        "avi": ["-c:v", "mpeg4", "-q:v", str(max(2, crf // 8))],
        "wmv": ["-c:v", "wmv2"],
        "flv": ["-c:v", "flv"],
        "mpg": ["-c:v", "mpeg2video", "-f", "vob"],
        "mxf": ["-c:v", "mpeg2video", "-f", "mxf"],
    }
    return mapping[target]


def _convert_image_to_video(
    input_path: Path,
    target_format: str,
    output_path: Path,
    ffmpeg: str,
    duration_seconds: float = IMAGE_STILL_VIDEO_SECONDS,
    quality_key: str = "media",
) -> Path:
    target = normalize_format_name(target_format)
    quality = _video_quality_settings(quality_key)
    duration = max(1.0, min(float(duration_seconds), 120.0))
    command = [
        ffmpeg,
        "-y",
        "-hide_banner",
        "-loglevel",
        "error",
        "-loop",
        "1",
        "-framerate",
        str(BLACK_VIDEO_FPS),
        "-i",
        str(input_path),
        "-t",
        str(duration),
        "-an",
        "-pix_fmt",
        "yuv420p",
        "-vf",
        _still_video_filter(quality["height"]),
    ]
    command.extend(_image_to_video_codec_args(target, quality["crf"]))
    command.append(str(output_path))
    try:
        _run_ffmpeg(command)
    except ConversionError as error:
        message = str(error)
        if target in ("wmv", "flv", "mxf"):
            raise ConversionError(f"NO PUDE: {target.upper()} depende del build de FFmpeg. {message}") from error
        raise
    if not output_path.exists():
        raise ConversionError("FFmpeg termino pero no se encontro el video de salida.")
    return output_path


def _convert_audio_to_video(input_path: Path, target_format: str, output_path: Path, ffmpeg: str) -> Path:
    target = normalize_format_name(target_format)
    command = [
        ffmpeg,
        "-y",
        "-hide_banner",
        "-loglevel",
        "error",
        "-f",
        "lavfi",
        "-i",
        f"color=c=black:s={BLACK_VIDEO_SIZE}:r={BLACK_VIDEO_FPS}",
        "-i",
        str(input_path),
        "-shortest",
        "-pix_fmt",
        "yuv420p",
        "-map",
        "0:v:0",
        "-map",
        "1:a:0",
    ]
    command.extend(_image_to_video_codec_args(target))
    if target == "mp4":
        command.extend(["-c:a", "aac", "-b:a", "192k"])
    elif target in ("webm", "mkv", "mov"):
        command.extend(["-c:a", "aac", "-b:a", "192k"])
    elif target == "avi":
        command.extend(["-c:a", "libmp3lame", "-q:a", "4"])
    elif target == "wmv":
        command.extend(["-c:a", "wmav2"])
    elif target == "flv":
        command.extend(["-c:a", "libmp3lame", "-q:a", "4"])
    elif target == "mpg":
        command.extend(["-c:a", "mp2"])
    elif target == "mxf":
        command.extend(["-c:a", "pcm_s16le"])
    command.append(str(output_path))
    try:
        _run_ffmpeg(command)
    except ConversionError as error:
        message = str(error)
        if target in ("wmv", "flv", "mxf"):
            raise ConversionError(f"NO PUDE: {target.upper()} depende del build de FFmpeg. {message}") from error
        raise
    if not output_path.exists():
        raise ConversionError("FFmpeg termino pero no se encontro el video de salida.")
    return output_path


def _convert_audio_to_spectrogram(
    input_path: Path,
    target_format: str,
    output_path: Path,
    ffmpeg: str,
) -> Path:
    target = normalize_format_name(target_format)
    png_path = output_path if target == "png" else output_path.with_suffix(".png")
    command = [
        ffmpeg,
        "-y",
        "-hide_banner",
        "-loglevel",
        "error",
        "-i",
        str(input_path),
        "-lavfi",
        "showspectrumpic=s=1920x1080:color=channel:scale=log",
        str(png_path),
    ]
    try:
        _run_ffmpeg(command)
    except ConversionError as error:
        raise ConversionError(f"NO PUDE: no se pudo generar el espectrograma. {error}") from error
    if not png_path.exists():
        raise ConversionError("NO PUDE: FFmpeg no genero la imagen del espectrograma.")

    if target == "png":
        return png_path

    final_path = output_path.with_suffix(output_extension(target))
    with Image.open(png_path) as image:
        _save_static_image(image.convert("RGB"), target, final_path)
    if png_path != final_path and png_path.exists():
        png_path.unlink()
    return final_path


def _ffmpeg_audio_args(target_format: str) -> list[str]:
    target = normalize_format_name(target_format)
    mapping = {
        "mp3": ["-vn", "-c:a", "libmp3lame", "-q:a", "2"],
        "wav": ["-vn", "-c:a", "pcm_s16le"],
        "m4a": ["-vn", "-c:a", "aac", "-b:a", "192k"],
        "flac": ["-vn", "-c:a", "flac"],
        "ogg": ["-vn", "-c:a", "libvorbis", "-q:a", "5"],
        "mka": ["-vn", "-c:a", "flac", "-f", "matroska"],
        "aiff": ["-vn", "-c:a", "pcm_s16be", "-f", "aiff"],
        "wma": ["-vn", "-c:a", "wmav2"],
    }
    return mapping[target]


def _ffmpeg_video_args(target_format: str) -> list[str]:
    target = normalize_format_name(target_format)
    mapping = {
        "mp4": ["-c:v", "libx264", "-preset", "medium", "-crf", "23", "-c:a", "aac", "-movflags", "+faststart"],
        "webm": ["-c:v", "libvpx-vp9", "-crf", "31", "-b:v", "0", "-c:a", "libopus"],
        "mov": ["-c:v", "libx264", "-c:a", "aac", "-f", "mov"],
        "mkv": ["-c:v", "libx264", "-c:a", "aac", "-f", "matroska"],
        "avi": ["-c:v", "mpeg4", "-c:a", "libmp3lame", "-q:a", "4"],
        "wmv": ["-c:v", "wmv2", "-c:a", "wmav2"],
        "flv": ["-c:v", "flv", "-c:a", "libmp3lame", "-q:a", "4"],
        "mpg": ["-c:v", "mpeg2video", "-c:a", "mp2", "-f", "vob"],
        "mxf": ["-c:v", "mpeg2video", "-c:a", "pcm_s16le", "-f", "mxf"],
    }
    return mapping[target]


def _convert_with_ffmpeg(
    input_path: Path,
    target_format: str,
    output_path: Path,
    ffmpeg: str,
    media_kind: str,
) -> Path:
    target = normalize_format_name(target_format)

    if media_kind == "audio" and target in VIDEO_TARGETS:
        return _convert_audio_to_video(input_path, target, output_path, ffmpeg)
    if media_kind == "audio" and target in SPECTROGRAM_TARGETS:
        return _convert_audio_to_spectrogram(input_path, target, output_path, ffmpeg)

    command = [ffmpeg, "-y", "-hide_banner", "-loglevel", "error", "-i", str(input_path)]

    if target in AUDIO_TARGETS:
        command.extend(_ffmpeg_audio_args(target))
    elif target in VIDEO_TARGETS:
        command.extend(_ffmpeg_video_args(target))
    else:
        raise ConversionError(f"Formato de destino no soportado: {target}")

    command.append(str(output_path))
    try:
        _run_ffmpeg(command)
    except ConversionError as error:
        message = str(error)
        if target in ("wma", "mxf", "wmv", "flv"):
            raise ConversionError(f"NO PUDE: {target.upper()} depende del build de FFmpeg. {message}") from error
        raise
    if not output_path.exists():
        raise ConversionError("FFmpeg termino pero no se encontro el archivo de salida.")
    return output_path


def convert_media(
    input_path: Path | str,
    target_format: str,
    output_dir: Path | str,
    ffmpeg_location: str | None = None,
    options: dict | None = None,
    progress_callback=None,
) -> Path:
    source = Path(input_path)
    if not source.is_file():
        raise ConversionError("El archivo de origen no existe.")

    target = normalize_format_name(target_format)
    media_kind = detect_media_kind(source)
    if media_kind == "unknown":
        raise ConversionError("Tipo de archivo no reconocido para conversion.")

    if not is_target_allowed(media_kind, target, source):
        raise ConversionError("Ese formato de destino no esta disponible para este archivo.")

    opts = options or {}
    duration_seconds = float(opts.get("video_duration", IMAGE_STILL_VIDEO_SECONDS))
    quality_key = str(opts.get("video_quality", "media"))

    output_directory = Path(output_dir)
    output_directory.mkdir(parents=True, exist_ok=True)
    output_path = _ensure_unique_path(
        output_directory / f"{conversion_output_basename(source)}{output_extension(target)}"
    )

    if media_kind == "image":
        if source.suffix.lower() == ".svg":
            ffmpeg = find_ffmpeg(ffmpeg_location)
            if not ffmpeg:
                raise ConversionError("NO PUDE: SVG como entrada requiere FFmpeg con soporte librsvg.")
            return _convert_svg_input(
                source,
                target,
                output_path,
                ffmpeg,
                duration_seconds=duration_seconds,
                quality_key=quality_key,
                ffmpeg_location=ffmpeg_location,
                progress_callback=progress_callback,
            )

        if target in AUDIO_TARGETS:
            from conversion_image_audio import convert_image_to_audio

            return convert_image_to_audio(
                source,
                target,
                output_path,
                ffmpeg_location=ffmpeg_location,
                progress_callback=progress_callback,
            )

        if target in VIDEO_TARGETS:
            ffmpeg = find_ffmpeg(ffmpeg_location)
            if not ffmpeg:
                raise ConversionError("Esta conversion requiere FFmpeg instalado y en el PATH.")
            if progress_callback:
                progress_callback(15.0)
            result = _convert_image_to_video(
                source,
                target,
                output_path,
                ffmpeg,
                duration_seconds=duration_seconds,
                quality_key=quality_key,
            )
            if progress_callback:
                progress_callback(100.0)
            return result

        if target in IMAGE_TARGETS:
            try:
                return _convert_image_pillow(source, target, output_path)
            except ConversionError:
                raise
            except Exception as error:
                raise ConversionError(f"No se pudo convertir la imagen: {error}") from error

        raise ConversionError("NO PUDE: formato de destino no soportado para imagen.")

    ffmpeg = find_ffmpeg(ffmpeg_location)
    if not ffmpeg:
        raise ConversionError("Esta conversion requiere FFmpeg instalado y en el PATH.")

    if progress_callback:
        progress_callback(50.0)
    result = _convert_with_ffmpeg(source, target, output_path, ffmpeg, media_kind)
    if progress_callback:
        progress_callback(100.0)
    return result
