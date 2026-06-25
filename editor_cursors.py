"""Tool cursors for the editor canvas (XBM, works on Windows Tk)."""

from __future__ import annotations

from pathlib import Path

_CURSOR_VERSION = 3
_CACHE_DIR = Path(__file__).resolve().parent / "assets" / "cursors"
_CACHE: dict[str, str] = {}

# 16x16 grids: 1 = opaque pixel
_PENCIL = (
    "......####.......",
    ".....######......",
    "....########.....",
    "...##########....",
    "..############...",
    ".##############..",
    "##############...",
    ".#############...",
    "..############...",
    "...###########...",
    "....#########....",
    ".....#######.....",
    "......#####......",
    ".......###.......",
    "........#........",
    "................",
)

_ERASER = (
    "................",
    "..##########....",
    "..##########....",
    "..##########....",
    "..##########....",
    "..##########....",
    "..##########....",
    "..##########....",
    "..##########....",
    "..##########....",
    "..##########....",
    "..##########....",
    "................",
    "................",
    "................",
    "................",
)

_EYEDROPPER = (
    ".....######.....",
    "....########....",
    "...##########...",
    "..###......##...",
    ".###........##..",
    "###..........##.",
    ".##..........##.",
    "..##........##..",
    "...##......##...",
    "....##....##....",
    ".....##..##.....",
    "......####......",
    ".......##.......",
    "........#.......",
    "................",
    "................",
)

_BUCKET = (
    "................",
    "..###..#####....",
    "..###.#######...",
    "..###.#######...",
    "..###..#####....",
    "......#####.....",
    ".......###......",
    "........#.......",
    "................",
    "................",
    "................",
    "................",
    "................",
    "................",
    "................",
    "................",
)

_SPECS: dict[str, tuple[tuple[str, ...], tuple[int, int]]] = {
    "pencil": (_PENCIL, (1, 14)),
    "eraser": (_ERASER, (8, 8)),
    "eyedropper": (_EYEDROPPER, (8, 13)),
    "bucket": (_BUCKET, (10, 7)),
}

_FALLBACK = {
    "pencil": "crosshair",
    "eraser": "circle",
    "eyedropper": "crosshair",
    "bucket": "crosshair",
}


def _rows_to_bytes(rows: tuple[str, ...]) -> list[int]:
    values: list[int] = []
    for row in rows:
        value = 0
        for index, cell in enumerate(row[:16]):
            if cell != ".":
                value |= 1 << index
        values.append(value & 0xFF)
        values.append((value >> 8) & 0xFF)
    return values


def _write_xbm(path: Path, name: str, rows: tuple[str, ...], hotspot: tuple[int, int]) -> None:
    bytes_list = _rows_to_bytes(rows)
    hex_lines = ", ".join(f"0x{b:02x}" for b in bytes_list)
    hot_x, hot_y = hotspot
    path.write_text(
        f"#define {name}_width 16\n"
        f"#define {name}_height 16\n"
        f"#define {name}_x_hot {hot_x}\n"
        f"#define {name}_y_hot {hot_y}\n"
        f"static unsigned char {name}_bits[] = {{\n  {hex_lines}\n}};\n",
        encoding="utf-8",
    )


def _ensure_cursor(tool: str) -> str | None:
    cache_key = f"{tool}_v{_CURSOR_VERSION}"
    if cache_key in _CACHE:
        return _CACHE[cache_key]
    spec = _SPECS.get(tool)
    if spec is None:
        return None
    rows, hotspot = spec
    _CACHE_DIR.mkdir(parents=True, exist_ok=True)
    bit_path = _CACHE_DIR / f"{tool}_v{_CURSOR_VERSION}.xbm"
    mask_path = _CACHE_DIR / f"{tool}_v{_CURSOR_VERSION}_mask.xbm"
    _write_xbm(bit_path, tool, rows, hotspot)
    _write_xbm(mask_path, f"{tool}_mask", rows, hotspot)
    cursor_ref = f"@{bit_path} @{mask_path}"
    _CACHE[cache_key] = cursor_ref
    return cursor_ref


def apply_draw_cursor(canvas, tool: str) -> None:
    try:
        cursor_ref = _ensure_cursor(tool)
        if cursor_ref is not None:
            canvas.configure(cursor=cursor_ref)
            return
    except Exception:
        pass
    fallback = _FALLBACK.get(tool, "crosshair")
    try:
        canvas.configure(cursor=fallback)
    except Exception:
        canvas.configure(cursor="crosshair")
