@echo off
cd /d "%~dp0"

echo [FissileKit] Modo desarrollo — reinicio con Ctrl+Shift+R, F5 o Ctrl+O
py dev.py
if errorlevel 1 pause
