@echo off
setlocal
cd /d "%~dp0"

echo [FissileKit] Compilando ejecutable...
call build_exe.bat
if errorlevel 1 exit /b 1

echo.
echo [FissileKit] Generando icono del instalador...
py -c "from PIL import Image; from pathlib import Path; p=Path('fissilepondlogo.png'); img=Image.open(p).convert('RGBA'); img.thumbnail((256,256), Image.Resampling.LANCZOS); img.save(Path('installer/fissilekit.ico'), format='ICO', sizes=[(256,256),(48,48),(32,32),(16,16)])"
if errorlevel 1 (
    echo No se pudo crear fissilekit.ico; el instalador puede fallar si falta el icono.
)

echo.
echo [FissileKit] Creando instalador...
call build_installer.bat
exit /b %ERRORLEVEL%
