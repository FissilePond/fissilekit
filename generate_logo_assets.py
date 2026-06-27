"""Sync FissileKit logo SVG and build a sharp multi-size Windows .ico."""

from __future__ import annotations

import shutil
import sys
from pathlib import Path

from PIL import Image

import conversion_preview

ROOT = Path(__file__).resolve().parent
SVG_SOURCES = (
    ROOT / "logos para las herramientas" / "FissileKit-Logo.svg",
    ROOT / "assets" / "fissilekit_logo.svg",
)
SVG_DEST = ROOT / "assets" / "fissilekit_logo.svg"
ICO_DEST = ROOT / "installer" / "fissilekit.ico"
ICO_SIZES = (16, 20, 24, 32, 40, 48, 64, 128, 256)


def _render_icon_size(svg_path: Path, size: int) -> Image.Image | None:
    rendered = conversion_preview.load_raster_image(
        svg_path,
        output_size=(size, size),
        supersample=4,
    )
    return rendered


def main() -> int:
    source = next((path for path in SVG_SOURCES if path.is_file()), None)
    if source is None:
        print("No se encontro FissileKit-Logo.svg", file=sys.stderr)
        return 1

    SVG_DEST.parent.mkdir(parents=True, exist_ok=True)
    if source.resolve() != SVG_DEST.resolve():
        shutil.copy2(source, SVG_DEST)

    icons: list[Image.Image] = []
    for size in ICO_SIZES:
        rendered = _render_icon_size(SVG_DEST, size)
        if rendered is None:
            print(f"No se pudo rasterizar el icono de {size}px.", file=sys.stderr)
            return 1
        icons.append(rendered.convert("RGBA"))

    ICO_DEST.parent.mkdir(parents=True, exist_ok=True)
    icons.sort(key=lambda image: image.width, reverse=True)
    icons[0].save(
        ICO_DEST,
        format="ICO",
        sizes=[(icon.width, icon.height) for icon in icons],
        append_images=icons[1:],
    )
    print(f"Logo actualizado: {SVG_DEST.name} -> {ICO_DEST.name}")
    portable_ico = ROOT / "fissilekit.ico"
    shutil.copy2(ICO_DEST, portable_ico)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
