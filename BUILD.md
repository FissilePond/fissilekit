# Compilar FissileKit (Windows)

## Requisitos

- Python 3.10+
- Dependencias de la app (`requirements.txt`)
- **PyInstaller** (se instala con `build_exe.bat`)
- **Inno Setup 6** (solo para el instalador `.exe`): https://jrsoftware.org/isinfo.php

Opcional para el usuario final: **ffmpeg** en el PATH del sistema (mejor calidad de video/audio).

## 1. Ejecutable portable

```powershell
.\build_exe.bat
```

Salida: `dist\FissileKit\FissileKit.exe` (carpeta completa; copia toda la carpeta para distribuir).

La primera vez, copia `settings.json.example` a `settings.json` junto al `.exe` si quieres valores por defecto.

## 2. Instalador

Después de compilar el exe:

```powershell
.\build_installer.bat
```

Salida: `dist\FissileKit-Setup-1.0.0.exe`

## Notas

- `settings.json` se guarda junto al ejecutable, no dentro del instalador.
- Antivirus pueden marcar falsos positivos en apps empaquetadas con PyInstaller; es comun firmar el exe con un certificado si distribuyes en serio.
- Para publicar en GitHub Releases, sube el instalador o un ZIP de `dist\FissileKit`.
