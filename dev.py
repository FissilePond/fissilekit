#!/usr/bin/env python3
"""Launcher de desarrollo para FissileKit.

Ejecuta main.py y reinicia la app al pulsar un atajo global.

Uso:
    py dev.py
    dev.bat

Atajos (funcionan aunque la ventana no tenga el foco):
    Ctrl+Shift+R   reiniciar (recomendado)
    F5             reiniciar
    Ctrl+O         reiniciar
    Ctrl+Shift+Q   cerrar launcher y la app

Si keyboard no esta instalado:
    py -m pip install keyboard
"""

from __future__ import annotations

import subprocess
import sys
import threading
import time
from pathlib import Path

try:
    import keyboard
except ImportError:
    print("Falta la dependencia 'keyboard'.")
    print("Instala con: py -m pip install keyboard")
    sys.exit(1)

ROOT = Path(__file__).resolve().parent
MAIN = ROOT / "main.py"

# Atajos para reiniciar. Puedes editar esta lista.
RESTART_HOTKEYS = (
    "ctrl+shift+r",
    "f5",
    "ctrl+o",
    "|",  # puede variar segun teclado; edita dev.py si no funciona
)

EXIT_HOTKEY = "ctrl+shift+q"

_process: subprocess.Popen | None = None
_restart_lock = threading.Lock()
_shutting_down = False


def _log(message: str) -> None:
    print(message, flush=True)


def _start_app() -> subprocess.Popen:
    return subprocess.Popen(
        [sys.executable, str(MAIN)],
        cwd=ROOT,
    )


def _stop_app() -> None:
    global _process
    if _process is None:
        return
    if _process.poll() is not None:
        _process = None
        return
    _process.terminate()
    try:
        _process.wait(timeout=6)
    except subprocess.TimeoutExpired:
        _process.kill()
        _process.wait(timeout=3)
    _process = None


def restart_app(_event=None) -> None:
    global _process
    if _shutting_down:
        return
    if not _restart_lock.acquire(blocking=False):
        return
    try:
        _log("\n[dev] Reiniciando FissileKit...")
        _stop_app()
        _process = _start_app()
        _log("[dev] App iniciada de nuevo.")
    finally:
        _restart_lock.release()


def shutdown(_event=None) -> None:
    global _shutting_down
    _shutting_down = True
    _log("\n[dev] Cerrando...")
    _stop_app()
    keyboard.unhook_all()
    sys.exit(0)


def _register_hotkeys() -> None:
    for hotkey in RESTART_HOTKEYS:
        keyboard.add_hotkey(hotkey, restart_app, suppress=False)
    keyboard.add_hotkey(EXIT_HOTKEY, shutdown, suppress=False)


def main() -> int:
    global _process

    if not MAIN.is_file():
        _log(f"No se encontro {MAIN}")
        return 1

    _log("FissileKit — modo desarrollo")
    _log("Reiniciar: " + ", ".join(RESTART_HOTKEYS))
    _log(f"Salir del launcher: {EXIT_HOTKEY}")
    _log("Ctrl+C en esta terminal tambien cierra todo.\n")

    _process = _start_app()
    _register_hotkeys()

    try:
        while not _shutting_down:
            if _process.poll() is not None:
                code = _process.returncode
                _log(f"\n[dev] La app termino (codigo {code}). Reiniciando en 1 s...")
                time.sleep(1)
                if not _shutting_down:
                    _process = _start_app()
            time.sleep(0.25)
    except KeyboardInterrupt:
        shutdown()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
