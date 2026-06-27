@echo off
setlocal
cd /d "%~dp0"

echo [FissileKit] Instalando dependencias de la app...
py -m pip install -r requirements.txt
if errorlevel 1 goto :error

echo [FissileKit] Instalando PyInstaller...
py -m pip install pyinstaller
if errorlevel 1 goto :error

echo [FissileKit] Generando icono desde logo SVG...
py generate_logo_assets.py
if errorlevel 1 goto :error

echo [FissileKit] Preparando FFmpeg embebido...
py ensure_ffmpeg.py
if errorlevel 1 goto :error

echo [FissileKit] Compilando ejecutable (carpeta dist\FissileKit)...
py -m PyInstaller fissilekit.spec --noconfirm --clean
if errorlevel 1 goto :error

copy /Y "installer\fissilekit.ico" "dist\FissileKit\fissilekit.ico" >nul
if errorlevel 1 goto :error

echo.
echo Listo. Ejecutable:
echo   dist\FissileKit\FissileKit.exe
echo.
echo Siguiente paso: ejecuta build_installer.bat si tienes Inno Setup instalado.
goto :eof

:error
echo.
echo La compilacion fallo.
exit /b 1
