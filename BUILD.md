# Compilar FissileKit (Windows)

## Requisitos

- Python 3.10+ (probado con 3.14)
- Dependencias de la app (`requirements.txt`)
- **PyInstaller** (se instala automaticamente con `build_exe.bat`)
- **Inno Setup 6** (solo para el instalador `.exe`): https://jrsoftware.org/isinfo.php

Opcional para el usuario final: **ffmpeg** en el PATH del sistema (conversion de video/audio, SVG y previews).

## Compilacion rapida (todo en uno)

```powershell
.\build_all.bat
```

Genera:

| Salida | Descripcion |
|--------|-------------|
| `dist\FissileKit\FissileKit.exe` | Carpeta portable (copia toda la carpeta) |
| `dist\FissileKit-Setup-1.1.0.exe` | Instalador para Windows |

## Pasos por separado

### 1. Ejecutable portable

```powershell
.\build_exe.bat
```

Salida: `dist\FissileKit\FissileKit.exe`

La primera vez, copia `settings.json.example` a `settings.json` junto al `.exe` si quieres valores por defecto.

### 2. Instalador

Despues de compilar el exe:

```powershell
.\build_installer.bat
```

Salida: `dist\FissileKit-Setup-1.1.0.exe`

El script de Inno Setup esta en `installer\fissilekit.iss`. El icono del instalador se genera desde `fissilepondlogo.png`.

## Que incluye el paquete

- Pestañas **Videos**, **Imagenes**, **Conversion** y **Editor**
- Iconos de conversion en `assets/conversion_icons`
- Guia `instructivo.html`
- Plantilla `settings.json.example`

## Notas

- `settings.json` se guarda junto al ejecutable despues del primer uso; no se empaqueta con datos personales.
- El instalador no requiere permisos de administrador (`PrivilegesRequired=lowest`).
- Antivirus pueden marcar falsos positivos en apps empaquetadas con PyInstaller; es comun firmar el exe con un certificado si distribuyes en serio.
- Para publicar en GitHub Releases, sube el instalador o un ZIP de `dist\FissileKit`.

## Version actual

**1.1.0** — Conversion multimedia, editor de imagenes con historial local, mejoras de rendimiento en canvas.
