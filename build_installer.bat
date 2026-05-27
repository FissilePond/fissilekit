@echo off
setlocal
cd /d "%~dp0"

if not exist "dist\FissileKit\FissileKit.exe" (
    echo Primero ejecuta build_exe.bat
    exit /b 1
)

set "ISCC="
if exist "%ProgramFiles(x86)%\Inno Setup 6\ISCC.exe" set "ISCC=%ProgramFiles(x86)%\Inno Setup 6\ISCC.exe"
if exist "%ProgramFiles%\Inno Setup 6\ISCC.exe" set "ISCC=%ProgramFiles%\Inno Setup 6\ISCC.exe"

if "%ISCC%"=="" (
    echo Inno Setup 6 no esta instalado.
    echo Descargalo de: https://jrsoftware.org/isinfo.php
    echo Luego ejecuta de nuevo este archivo.
    exit /b 1
)

echo [FissileKit] Creando instalador...
"%ISCC%" "installer\fissilekit.iss"
if errorlevel 1 goto :error

echo.
echo Instalador listo:
echo   dist\FissileKit-Setup-1.0.0.exe
goto :eof

:error
echo Fallo la creacion del instalador.
exit /b 1
