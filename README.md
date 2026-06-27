# FissileKit

Toolkit de escritorio para creadores: descarga videos y audio de YouTube, busca imagenes, convierte archivos y edita imagenes en un solo lugar.

Desarrollado por [FissilePond](https://www.fissilepond.com/).

> Herramienta pensada para acompanar un flujo de edicion de video: descargas, assets, conversiones y retoques rapidos en imagen, todo en una sola app.

![Python](https://img.shields.io/badge/Python-3.10%2B-blue)
![Platform](https://img.shields.io/badge/Platform-Windows-lightgrey)
![License](https://img.shields.io/badge/License-MIT-green)
![Version](https://img.shields.io/badge/Version-1.2.0-informational)

## Que hace

| Pestaña | Funciones |
|---------|-----------|
| **Videos** | Descarga un link o un lote en video o audio, con calidad configurable. |
| **Imagenes** | Lista unificada con preview, busqueda (Pexels/Flickr), portapapeles, formato y calidad al exportar. |
| **Conversion** | Convierte entre imagenes, video y audio; lote con barra de progreso; imagen→audio, imagen→video, SVG, espectrograma, etc. |
| **Editor** | Historial local, recorte con mascara, rotar, redimensionar (escala o lienzo), dibujo, formas y texto estilo Canva. |

Ademas:

- **Lotes** en videos, imagenes y conversiones: agrega, quita, reemplaza y procesa todo en carpeta.
- **Tecla global:** captura rapida del portapapeles sin pegar a mano.
- **Interfaz:** tema oscuro/claro e idioma espanol/ingles.

## Requisitos

- Windows (recomendado; la tecla global y deteccion de escritura usan APIs de Windows)
- Python 3.10 o superior **o** el instalador `.exe` precompilado
- Dependencias Python: ver `requirements.txt`
- Opcional pero recomendado: [ffmpeg](https://ffmpeg.org/) en el PATH (MP4/MP3, conversiones, previews de video/SVG en el editor)

## Instalacion

### Opcion A — Instalador (recomendado)

1. Descarga `FissileKit-Setup-1.2.0.exe` desde [Releases](https://github.com/FissilePond/fissilekit/releases) (o compila con `build_all.bat`).
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

O usa `iniciar.bat` / `dev.bat` si ya tienes Python en el PATH.

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
3. Para imagen→video: duracion y calidad. Para imagen→audio: genera audio desde colores de la imagen.
4. **Convertir** o convierte todo el lote; abre el resultado o revisa el lote con **Ver lote**.

Salida por defecto: `Downloads/FissileKit/Conversiones`.

### Editor

1. Abre la pestaña **Editor**. El historial (izquierda) muestra imagenes, videos y audios de tu carpeta FissileKit.
2. Selecciona un archivo en el arbol o haz clic en el lienzo vacio para abrir otro.
3. Usa las herramientas de la barra superior (iconos). Cada una abre su sub-barra con opciones.
4. **Guardar** (en la sub-barra): aplica los cambios en la sesion y vuelve a la barra principal **sin** guardar archivo en disco.
5. **Salir**: abandona la herramienta actual (pide confirmacion si hay cambios pendientes).
6. **Terminar** (abajo a la derecha): exporta el resultado a un archivo (PNG recomendado si usaste transparencia, recorte o dibujo).

#### Herramientas del editor

| Herramienta | Que hace |
|-------------|----------|
| **Recorte** | Area con esquinas o arrastre; proporciones 1:1, 9:16, 16:9 o libre. Fuera del recorte queda transparente (mascara). |
| **Rotar** | Rueda, 90°, grados manuales, volteo horizontal/vertical. |
| **Redimensionar** | **Escalar** la imagen o **Lienzo** (mover y escalar contenido dentro de un tamano fijo HD/FHD/4K). |
| **Dibujar** | Lapiz, borrador (solo trazos), gotero y cubeta. Tamaño, opacidad y tolerancia. |
| **Borrador PNG** | Borra la imagen dejando transparencia: manual, color total, zona, magico y reparar. |
| **Formas** | Linea, curva (clics + doble clic), rectangulo, ovalo, circulo, triangulo, pentagono, hexagono, estrella. Relleno y borde opcionales con color. Clic sin arrastrar = figura proporcional. |
| **Texto** | Clic para escribir con cursor; fuentes del sistema; negrita, cursiva, subrayado, tachado; color; borde opcional. Arrastra para mover, esquinas para escalar. |
| **Deshacer / Rehacer** | Historial de cambios en la sesion. |

Los trazos de dibujo, formas y texto viven en una capa editable: el borrador manual puede borrarlos.

### Ayuda

El boton **?** abre `instructivo.html` con la guia detallada.

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
  editor_text.py           # Objetos de texto y fuentes
  editor_icons.py          # Iconos de herramientas
  editor_cursors.py        # Cursores personalizados (dibujo)
  assets/conversion_icons/
  assets/cursors/
  installer/fissilekit.iss
  requirements.txt
  instructivo.html
  dev.py / dev.bat         # Desarrollo con recarga
  build_exe.bat
  build_installer.bat
  build_all.bat
  iniciar.bat
  settings.json.example
  fissilekit.spec
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
- `dist\FissileKit-Setup-1.2.0.exe` — instalador

Requisito extra para el instalador: [Inno Setup 6](https://jrsoftware.org/isinfo.php).

## Licencia

MIT — ver [LICENSE](LICENSE).
