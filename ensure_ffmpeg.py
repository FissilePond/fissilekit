"""Download FFmpeg essentials for bundling inside FissileKit."""

from __future__ import annotations

import shutil
import sys
import tempfile
import urllib.request
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent
FFMPEG_ROOT = ROOT / "third_party" / "ffmpeg"
FFMPEG_BIN = FFMPEG_ROOT / "bin"
FFMPEG_URL = "https://www.gyan.dev/ffmpeg/builds/ffmpeg-release-essentials.zip"


def ffmpeg_ready() -> bool:
    return (FFMPEG_BIN / "ffmpeg.exe").is_file() and (FFMPEG_BIN / "ffprobe.exe").is_file()


def _copy_tree(source: Path, destination: Path) -> None:
    if destination.exists():
        shutil.rmtree(destination)
    shutil.copytree(source, destination)


def ensure_ffmpeg(force: bool = False) -> int:
    if ffmpeg_ready() and not force:
        print(f"FFmpeg listo: {FFMPEG_BIN / 'ffmpeg.exe'}")
        return 0

    print("[FissileKit] Descargando FFmpeg essentials...")
    FFMPEG_ROOT.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory() as temp_dir:
        zip_path = Path(temp_dir) / "ffmpeg.zip"
        try:
            urllib.request.urlretrieve(FFMPEG_URL, zip_path)
        except OSError as error:
            print(f"No se pudo descargar FFmpeg: {error}", file=sys.stderr)
            return 1

        with zipfile.ZipFile(zip_path) as archive:
            archive.extractall(temp_dir)

        bin_dirs = sorted(Path(temp_dir).glob("ffmpeg-*-essentials_build/bin"))
        if not bin_dirs:
            print("El ZIP de FFmpeg no contiene la carpeta bin esperada.", file=sys.stderr)
            return 1

        source_bin = bin_dirs[0]
        _copy_tree(source_bin, FFMPEG_BIN)

        license_candidates = sorted(Path(temp_dir).glob("ffmpeg-*-essentials_build/LICENSE"))
        if license_candidates:
            shutil.copy2(license_candidates[0], FFMPEG_ROOT / "LICENSE.txt")

    if not ffmpeg_ready():
        print("FFmpeg no quedo instalado correctamente.", file=sys.stderr)
        return 1

    print(f"FFmpeg instalado en: {FFMPEG_BIN}")
    return 0


if __name__ == "__main__":
    raise SystemExit(ensure_ffmpeg())
