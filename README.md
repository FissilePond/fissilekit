# FissileKit

Toolkit de escritorio para creadores: descarga videos y audio de YouTube, busca imagenes y arma lotes listos para editar.

Desarrollado por [FissilePond](https://www.fissilepond.com/).

Nota: Añadiré mas cosas en el futuro cercano, quiro que sea la herramienta definitiva para acompañar un editor de video. Hecho originalmente para mi uso personal

![Python](https://img.shields.io/badge/Python-3.10%2B-blue)
![Platform](https://img.shields.io/badge/Platform-Windows-lightgrey)
![License](https://img.shields.io/badge/License-MIT-green)

## Que hace

- **Videos:** descarga un link o un lote completo en video o audio, con calidad configurable.
- **Imagenes:** lista unificada con preview, busqueda (Pexels/Flickr), portapapeles, formato y calidad al exportar.
- **Lotes:** agrega, quita, reemplaza y descarga todo en una carpeta.
- **Tecla global:** captura rapida del portapapeles sin estar pegando a mano todo el tiempo.
- **Interfaz:** tema oscuro/claro e idioma espanol/ingles.

## Requisitos

- Windows (recomendado; la tecla global y deteccion de escritura usan APIs de Windows)
- Python 3.10 o superior
- Dependencias: ver `requirements.txt`
- Opcional: [ffmpeg](https://ffmpeg.org/) para MP4/MP3 con mejor calidad

## Instalacion

```powershell
git clone https://github.com/FissilePond/fissilekit.git
cd fissilekit
py -m pip install -r requirements.txt
py main.py
```

O usa `iniciar.bat` si ya tienes Python en el PATH.

## Configuracion

Abre **Configuracion** (icono de engranaje en la barra superior) para:

| Opcion | Descripcion |
|--------|-------------|
| Tema | Claro (por defecto) o oscuro |
| Idioma | Espanol o ingles |
| API key de Pexels | Solo si usas busqueda en Pexels ([obtener clave gratis](https://www.pexels.com/api/)) |
| Tecla global | Atajo para mandar portapapeles al lote activo |

La configuracion se guarda en `settings.json` en la carpeta del programa. Ese archivo **no se sube al repositorio**; cada usuario usa el suyo. Puedes copiar `settings.json.example` como base.

## Uso rapido

### Videos

1. Pega un link y pulsa **Descargar**, o agrega varios al lote y usa **Descargar lote**.
2. Elige **Video** o **Audio** y la calidad.
3. Los archivos se guardan en `Downloads/FissileKit/Videos` (o la carpeta que elijas).

### Imagenes

1. Agrega terminos o links a la lista (o carga un `.txt`).
2. Pulsa **Buscar imagenes**, o pega imagenes directo al lote con la tecla global.
3. Selecciona una foto en la lista para ver el preview; quita o cambia con **Quitar** / **Otra**.
4. Elige formato y calidad en el panel lateral.
5. **Descargar lote** guarda en `Downloads/FissileKit/Imagenes` (con conversion silenciosa si cambias formato).

### Ayuda

El boton **i** abre `instructivo.html` con mas detalle.

## API keys y privacidad

- **No hay claves incluidas en este repositorio.** La API de Pexels la configuras tu en la app; se guarda solo en tu `settings.json` local.
- **Flickr Public** no requiere API key.
- No subas tu `settings.json` a Git ni lo compartas; ya esta en `.gitignore`.

## Aviso legal

Usa FissileKit solo con contenido que tengas derecho a descargar o usar. YouTube, Pexels, Flickr y otros servicios tienen sus propios terminos. El autor no se hace responsable del uso que le des a la herramienta.

## Estructura del proyecto

```
fissilekit/
  main.py              # Aplicacion principal
  requirements.txt
  instructivo.html     # Guia de uso
  iniciar.bat          # Atajo para Windows
  settings.json.example
  fissilepondlogo.png
```

## Donaciones

Si te sirve el proyecto: [Ko-fi — FissilePond](https://ko-fi.com/fissilepond)

## Compilar ejecutable e instalador (Windows)

Ver [BUILD.md](BUILD.md).

1. `build_exe.bat` → genera `dist\FissileKit\FissileKit.exe`
2. Instala [Inno Setup 6](https://jrsoftware.org/isinfo.php)
3. `build_installer.bat` → genera `dist\FissileKit-Setup-1.0.0.exe`

## Licencia

MIT — ver [LICENSE](LICENSE) en el repositorio.
