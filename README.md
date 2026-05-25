# Descargador Multimedia

Aplicacion de escritorio en Python con interfaz estilo Windows 7/Aero para descargar contenido de `YouTube` y armar lotes de `Imagenes`.

## Caracteristicas

- Descarga de `Video` o `Audio` desde un link de YouTube.
- Descarga por lote de links de YouTube usando el mismo formato y calidad.
- Lote final de imagenes combinando:
  - resultados de busqueda;
  - links directos;
  - imagenes pegadas desde el portapapeles.
- Busqueda de imagenes con `Pexels` o `Flickr Public`.
- Tecla global configurable para mandar portapapeles al lote activo.
- Bloqueo de captura mientras escribes en campos de texto, incluso en otras apps compatibles en Windows.
- Configuracion local para:
  - tema `oscuro` o `claro`;
  - idioma `espanol` o `ingles`;
  - API key de `Pexels`;
  - tecla global;
  - toggles de envio rapido por pestaña.

## Requisitos

- Python `3.10` o superior
- Dependencias del proyecto:
  - `pillow`
  - `yt-dlp`
  - `keyboard`
  - `uiautomation`
- Opcional: `ffmpeg` para mejor salida final en `MP4` y conversion a `MP3`

## Instalacion

```powershell
py -m pip install -r requirements.txt
```

## Ejecutar

```powershell
py main.py
```

Tambien puedes usar `iniciar.bat`.

## Uso rapido

### YouTube

- Pega un link y pulsa `Descargar`.
- O agrega varios links al cuadro de lote y usa `Descargar lote`.
- Puedes cambiar entre `Video` y `Audio`, y elegir calidad antes de iniciar.

### Imagenes

- Agrega texto a la lista principal o carga un `.txt` con una entrada por linea.
- Busca con `Pexels` o `Flickr Public`.
- Pega imagenes desde el portapapeles para agregarlas directo al lote final.
- Revisa el lote, quita elementos o reemplaza resultados con el boton correspondiente.

### Configuracion

- El boton `...` abre ajustes.
- Desde ahi puedes cambiar:
  - API key de `Pexels`;
  - tecla global;
  - modo `oscuro` o `claro`;
  - idioma `espanol` o `ingles`.
- El tema por defecto es `oscuro`.

## Notas

- `Flickr Public` no requiere API key.
- Si configuras una sola letra como tecla global, la app intenta ignorarla mientras detecta escritura en campos de texto.
- El boton `i` abre `instructivo.html`.
- La configuracion local se guarda en `settings.json`.
- En modo `Video`, con `ffmpeg`, la app intenta entregar un `MP4` final de mejor calidad.
- En modo `Audio`, con `ffmpeg`, la app convierte a `MP3` con la calidad elegida.
