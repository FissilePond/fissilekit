@echo off
setlocal
cd /d "%~dp0"

echo [FissileKit] Compilando ejecutable...
call build_exe.bat
if errorlevel 1 exit /b 1

echo.
echo [FissileKit] Generando icono del instalador...
py generate_logo_assets.py
if errorlevel 1 (
    echo No se pudo crear fissilekit.ico; el instalador puede fallar si falta el icono.
)

echo [FissileKit] Preparando FFmpeg embebido...
py ensure_ffmpeg.py
if errorlevel 1 (
    echo No se pudo descargar FFmpeg embebido.
)

echo.
echo [FissileKit] Creando instalador...
call build_installer.bat
exit /b %ERRORLEVEL%
