# FissileKit

Toolkit de escritorio para creadores: descarga videos y audio de YouTube, busca imagenes, convierte archivos y edita imagenes en un solo lugar.

Desarrollado por [FissilePond](https://www.fissilepond.com/).

> Añadiré mas cosas con el tiempo; quiero que sea la herramienta que acompañe a un editor de video. Hecho originalmente para mi uso personal.

![Python](https://img.shields.io/badge/Python-3.10%2B-blue)
![Platform](https://img.shields.io/badge/Platform-Windows-lightgrey)
![License](https://img.shields.io/badge/License-MIT-green)
![Version](https://img.shields.io/badge/Version-1.1.0-informational)

## Que hace

| Pestaña | Funciones |
|---------|-----------|
| **Videos** | Descarga un link o un lote en video o audio, con calidad configurable. |
| **Imagenes** | Lista unificada con preview, busqueda (Pexels/Flickr), portapapeles, formato y calidad al exportar. |
| **Conversion** | Convierte entre imagenes, video y audio; lote con barra de progreso; imagen→audio (grid color→frecuencia), imagen→video con duracion/calidad, SVG, etc. |
| **Editor** | Historial local (Imagenes/Videos/Audios), recorte con mascara, rotar, redimensionar, lapiz, cubeta, borrador manual, formas y texto. |

Ademas:

- **Lotes** en videos e imagenes: agrega, quita, reemplaza y descarga todo en una carpeta.
- **Tecla global:** captura rapida del portapapeles sin pegar a mano.
- **Interfaz:** tema oscuro/claro e idioma espanol/ingles.

## Requisitos

- Windows (recomendado; la tecla global y deteccion de escritura usan APIs de Windows)
- Python 3.10 o superior **o** el instalador `.exe` precompilado
- Dependencias Python: ver `requirements.txt`
- Opcional: [ffmpeg](https://ffmpeg.org/) en el PATH (MP4/MP3, conversiones, previews de video/SVG en el editor)

## Instalacion

### Opcion A — Instalador (recomendado)

1. Descarga `FissileKit-Setup-1.1.0.exe` desde [Releases](https://github.com/FissilePond/fissilekit/releases) (o compila con `build_all.bat`).
2. Ejecuta el instalador y sigue el asistente.
3. Opcional: icono en el escritorio durante la instalacion.

Los archivos quedan en `%LocalAppData%\Programs\FissileKit` (sin pedir admin).

### Opcion B — Desde codigo

```powershell
git clone https://github.com/FissilePond/fissilekit.git
cd fissilekit
py -m pip install -r requirements.txt
py main.py
```

O usa `iniciar.bat` si ya tienes Python en el PATH.

### Opcion C — Portable

Compila o descarga la carpeta `dist\FissileKit`, copiala donde quieras y ejecuta `FissileKit.exe`.

## Configuracion

Abre **Configuracion** (engranaje en la barra superior) para:

| Opcion | Descripcion |
|--------|-------------|
| Tema | Claro (por defecto) o oscuro |
| Idioma | Espanol o ingles |
| API key de Pexels | Solo si usas busqueda en Pexels ([clave gratis](https://www.pexels.com/api/)) |
| Tecla global | Atajo para mandar portapapeles al lote activo |
| Carpeta del editor | Donde el editor busca imagenes, videos y audios (por defecto `Downloads/FissileKit`) |

La configuracion se guarda en `settings.json` en la carpeta del programa. **No se sube al repositorio**; copia `settings.json.example` como base.

## Uso rapido

### Videos

1. Pega un link y pulsa **Descargar**, o agrega varios al lote y usa **Descargar lote**.
2. Elige **Video** o **Audio** y la calidad.
3. Los archivos se guardan en `Downloads/FissileKit/Videos` (o la carpeta que elijas).

### Imagenes

1. Agrega terminos o links a la lista (o carga un `.txt`).
2. Pulsa **Buscar imagenes**, o pega imagenes al lote con la tecla global.
3. Selecciona una foto para el preview; quita o cambia con **Quitar** / **Otra**.
4. Elige formato y calidad en el panel lateral.
5. **Descargar lote** guarda en `Downloads/FissileKit/Imagenes`.

### Conversion

1. Trae un archivo o un lote (**Elegir lote...**).
2. Elige formato de destino (imagen, video o audio).
3. Para imagen→video: duracion y calidad.
4. **Convertir** o convierte todo el lote; abre el resultado o revisa el lote con **Ver lote**.

Salida por defecto: `Downloads/FissileKit/Conversiones`.

### Editor

1. Abre la pestaña **Editor**; el historial muestra archivos de tu carpeta FissileKit.
2. Selecciona una imagen en el arbol o haz clic en el lienzo para abrir otra.
3. Herramientas con iconos: recorte, rotar, redimensionar, dibujar (lapiz/cubeta), borrador, formas, texto.
4. **Guardar** exporta una copia (PNG recomendado si usaste transparencia o recorte con mascara).

### Ayuda

El boton **?** abre `instructivo.html` con mas detalle.

## API keys y privacidad

- **No hay claves incluidas en el repositorio.** Pexels la configuras tu en la app; se guarda solo en tu `settings.json` local.
- **Flickr Public** no requiere API key.
- No subas tu `settings.json` a Git ni lo compartas; ya esta en `.gitignore`.

## Aviso legal

Usa FissileKit solo con contenido que tengas derecho a descargar o usar. YouTube, Pexels, Flickr y otros servicios tienen sus propios terminos. El autor no se hace responsable del uso que le des a la herramienta.

## Estructura del proyecto

```
fissilekit/
  main.py                  # Aplicacion principal
  conversion.py            # Motor de conversion
  conversion_preview.py    # Previews e iconos de conversion
  conversion_image_audio.py
  editor.py                # Sesion del editor
  editor_ui.py             # Interfaz del editor
  editor_ops.py            # Operaciones de imagen
  editor_icons.py          # Iconos de herramientas
  assets/conversion_icons/ # Iconos empaquetados
  installer/fissilekit.iss # Script Inno Setup
  requirements.txt
  instructivo.html
  build_exe.bat
  build_installer.bat
  build_all.bat
  iniciar.bat
  settings.json.example
  fissilepondlogo.png
```

## Donaciones

Si te sirve el proyecto: [Ko-fi — FissilePond](https://ko-fi.com/fissilepond)

## Compilar ejecutable e instalador (Windows)

Ver [BUILD.md](BUILD.md).

```powershell
.\build_all.bat
```

Salidas:

- `dist\FissileKit\FissileKit.exe` — portable
- `dist\FissileKit-Setup-1.1.0.exe` — instalador

Requisito extra para el instalador: [Inno Setup 6](https://jrsoftware.org/isinfo.php).

## Licencia

MIT — ver [LICENSE](LICENSE).
