@echo off
cd /d "%~dp0"

py -m pip install -r requirements.txt
if errorlevel 1 (
    echo.
    echo No se pudieron instalar las dependencias.
    pause
    exit /b 1
)

py main.py
if errorlevel 1 (
    echo.
    echo La aplicacion termino con error.
    pause
    exit /b 1
)
