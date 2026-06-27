# PyInstaller spec for FissileKit (Windows)
# Build: py -m PyInstaller fissilekit.spec --noconfirm

import sys
from pathlib import Path

from PyInstaller.utils.hooks import collect_all

block_cipher = None
root = Path(SPECPATH)

ffmpeg_bundle = root / "third_party" / "ffmpeg"
if not (ffmpeg_bundle / "bin" / "ffmpeg.exe").is_file():
    raise SystemExit(
        "FFmpeg embebido no encontrado. Ejecuta: py ensure_ffmpeg.py"
    )

datas = [
    (str(root / "instructivo.html"), "."),
    (str(root / "fissilepondlogo.png"), "."),
    (str(root / "Fissilepond logo png.png"), "."),
    (str(root / "settings.json.example"), "."),
    (str(root / "assets" / "conversion_icons"), "assets/conversion_icons"),
    (str(root / "assets" / "editor_icons"), "assets/editor_icons"),
    (str(root / "assets" / "fissilekit_logo.svg"), "assets"),
    (str(root / "installer" / "fissilekit.ico"), "installer"),
    (str(ffmpeg_bundle), "ffmpeg"),
]

binaries = []
hiddenimports = [
    "PIL._tkinter_finder",
    "keyboard",
    "uiautomation",
    "editor_ops",
    "editor_icons",
    "conversion_image_audio",
    "numpy",
    "fitz",
]

for pkg in ("yt_dlp", "keyboard", "uiautomation"):
    try:
        tmp_ret = collect_all(pkg)
        datas += tmp_ret[0]
        binaries += tmp_ret[1]
        hiddenimports += tmp_ret[2]
    except Exception:
        pass

a = Analysis(
    [str(root / "main.py")],
    pathex=[str(root)],
    binaries=binaries,
    datas=datas,
    hiddenimports=hiddenimports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name="FissileKit",
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=False,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=str(root / "installer" / "fissilekit.ico"),
)

coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=["ffmpeg.exe", "ffprobe.exe", "python*.dll"],
    name="FissileKit",
)
