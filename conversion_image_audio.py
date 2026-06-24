"""Image to audio sonification for FissileKit."""

from __future__ import annotations

import colorsys
import math
import subprocess
import sys
import tempfile
import wave
from pathlib import Path

import numpy as np
from PIL import Image

import conversion

SAMPLE_RATE = 44100
GRID_COLS = 72
GRID_ROWS = 48
SECONDS_PER_CELL = 0.035
MIN_FREQUENCY = 180.0
MAX_FREQUENCY = 3600.0


def _load_raster_rgb(path: Path, ffmpeg_location: str | None) -> Image.Image:
    if path.suffix.lower() == ".svg":
        ffmpeg = conversion.find_ffmpeg(ffmpeg_location)
        if not ffmpeg:
            raise conversion.ConversionError(
                "NO PUDE: SVG como entrada requiere FFmpeg con soporte librsvg."
            )
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
                    "-i",
                    str(path),
                    str(raster_path),
                ],
                capture_output=True,
                text=True,
                creationflags=creationflags,
            )
            if result.returncode != 0 or not raster_path.is_file():
                raise conversion.ConversionError("NO PUDE: no se pudo rasterizar SVG.")
            with Image.open(raster_path) as image:
                return image.convert("RGB")
        finally:
            if raster_path.exists():
                raster_path.unlink(missing_ok=True)

    with Image.open(path) as image:
        if getattr(image, "n_frames", 1) > 1:
            image.seek(0)
        return image.convert("RGB")


def _color_to_frequency_amplitude(red: float, green: float, blue: float) -> tuple[float, float]:
    hue, lightness, _saturation = colorsys.rgb_to_hls(red, green, blue)
    frequency = MIN_FREQUENCY + hue * (MAX_FREQUENCY - MIN_FREQUENCY)
    amplitude = 0.12 + lightness * 0.62
    return frequency, amplitude


def _write_wav(path: Path, samples: np.ndarray) -> None:
    clipped = np.clip(samples, -1.0, 1.0)
    pcm = (clipped * 32767).astype(np.int16)
    with wave.open(str(path), "wb") as handle:
        handle.setnchannels(1)
        handle.setsampwidth(2)
        handle.setframerate(SAMPLE_RATE)
        handle.writeframes(pcm.tobytes())


def _encode_audio_target(
    wav_path: Path,
    output_path: Path,
    target_format: str,
    ffmpeg: str,
) -> Path:
    target = conversion.normalize_format_name(target_format)
    if target == "wav":
        if wav_path.resolve() != output_path.resolve():
            output_path.write_bytes(wav_path.read_bytes())
        return output_path

    command = [ffmpeg, "-y", "-hide_banner", "-loglevel", "error", "-i", str(wav_path)]
    command.extend(conversion._ffmpeg_audio_args(target))
    command.append(str(output_path))
    conversion._run_ffmpeg(command)
    if not output_path.exists():
        raise conversion.ConversionError("FFmpeg termino pero no se encontro el audio de salida.")
    return output_path


def convert_image_to_audio(
    input_path: Path,
    target_format: str,
    output_path: Path,
    ffmpeg_location: str | None = None,
    progress_callback=None,
) -> Path:
    target = conversion.normalize_format_name(target_format)
    if target not in conversion.AUDIO_TARGETS:
        raise conversion.ConversionError("Formato de audio no soportado.")

    image = _load_raster_rgb(input_path, ffmpeg_location)
    resized = image.resize((GRID_COLS, GRID_ROWS), Image.Resampling.LANCZOS)
    pixels = np.asarray(resized, dtype=np.float64) / 255.0

    samples_per_cell = max(1, int(SAMPLE_RATE * SECONDS_PER_CELL))
    total_cells = GRID_COLS * GRID_ROWS
    audio = np.zeros(total_cells * samples_per_cell, dtype=np.float64)
    write_index = 0
    cell_index = 0

    for row in range(GRID_ROWS):
        for col in range(GRID_COLS):
            red, green, blue = pixels[row, col]
            frequency, amplitude = _color_to_frequency_amplitude(red, green, blue)
            time_axis = np.linspace(0.0, SECONDS_PER_CELL, samples_per_cell, endpoint=False)
            tone = amplitude * np.sin(2.0 * math.pi * frequency * time_axis)
            envelope = np.hanning(samples_per_cell)
            audio[write_index : write_index + samples_per_cell] = tone * envelope
            write_index += samples_per_cell
            cell_index += 1
            if progress_callback:
                progress_callback((cell_index / total_cells) * 100.0)

    peak = float(np.max(np.abs(audio)))
    if peak > 1e-6:
        audio = audio / peak * 0.92

    wav_path = output_path if target == "wav" else output_path.with_suffix(".wav")
    _write_wav(wav_path, audio)

    if target == "wav":
        return wav_path

    ffmpeg = conversion.find_ffmpeg(ffmpeg_location)
    if not ffmpeg:
        raise conversion.ConversionError("Esta conversion requiere FFmpeg instalado y en el PATH.")

    final_path = output_path.with_suffix(conversion.output_extension(target))
    try:
        return _encode_audio_target(wav_path, final_path, target, ffmpeg)
    finally:
        if wav_path.exists() and wav_path.resolve() != final_path.resolve():
            wav_path.unlink(missing_ok=True)
