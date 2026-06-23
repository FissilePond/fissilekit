import io
import json
import mimetypes
import os
import queue
import re
import shutil
import sys
import threading
import urllib.error
import urllib.parse
import urllib.request
import ctypes
import webbrowser
from pathlib import Path
import tkinter as tk
from tkinter import filedialog, messagebox
from ctypes import wintypes

from PIL import Image, ImageGrab, ImageTk
from yt_dlp import DownloadError, YoutubeDL

try:
    import keyboard
except ImportError:
    keyboard = None

try:
    import uiautomation as ui_auto
except ImportError:
    ui_auto = None


APP_TITLE = "FissileKit"


def _bundle_dir():
    if getattr(sys, "frozen", False):
        return Path(sys._MEIPASS)
    return Path(__file__).resolve().parent


def _writable_dir():
    if getattr(sys, "frozen", False):
        return Path(sys.executable).resolve().parent
    return Path(__file__).resolve().parent


BUNDLE_DIR = _bundle_dir()
WRITABLE_DIR = _writable_dir()
SETTINGS_FILE = WRITABLE_DIR / "settings.json"
HELP_FILE = BUNDLE_DIR / "instructivo.html"
SITE_URL = "https://www.fissilepond.com/"
DONATION_URL = "https://ko-fi.com/fissilepond"
BRAND_LOGO_FILE = BUNDLE_DIR / "fissilepondlogo.png"
DONATION_LOGO_FILE = BUNDLE_DIR / "Fissilepond logo png.png"
DEFAULT_FISSILEKIT_ROOT = Path.home() / "Downloads" / "FissileKit"
DEFAULT_YOUTUBE_FOLDER = DEFAULT_FISSILEKIT_ROOT / "Videos"
DEFAULT_IMAGE_FOLDER = DEFAULT_FISSILEKIT_ROOT / "Imagenes"
IMAGE_EXPORT_FORMATS = ("auto", "PNG", "JPEG", "WEBP")
IMAGE_QUALITY_LEVELS = ("baja", "media", "alta")
IMAGE_QUALITY_MAX_PX = {"baja": 640, "media": 1280, "alta": 2560}
YOUTUBE_BATCH_FORMATS = ("mp4", "webm", "mkv")
PEXELS_SEARCH_URL = "https://api.pexels.com/v1/search"
FLICKR_FEED_URL = "https://www.flickr.com/services/feeds/photos_public.gne"
SEARCH_SOURCES = ("Pexels", "Flickr Public")
DEFAULT_CAPTURE_HOTKEY = "x"
DEFAULT_THEME = "light"
DEFAULT_LANGUAGE = "es"

THEME_PALETTES = {
    "light": {
        "desktop": "#ececec",
        "face": "#ffffff",
        "light": "#fafafa",
        "dark": "#6b6b6b",
        "black": "#111111",
        "blue": "#111111",
        "white": "#ffffff",
        "edge": "#d4d4d4",
        "button": "#ffffff",
        "button_active": "#f3f3f3",
        "tab_idle": "#ffffff",
        "tab_active": "#111111",
        "title_text": "#ffffff",
        "glass_top": "#ffffff",
        "glass_mid": "#111111",
        "glass_bottom": "#111111",
        "status_top": "#fafafa",
        "status_bottom": "#fafafa",
        "link": "#111111",
        "accent_text": "#ffffff",
        "disabled": "#a3a3a3",
        "header_button": "#2a2a2a",
        "header_button_active": "#404040",
        "focus": "#111111",
    },
    "dark": {
        "desktop": "#0a0a0a",
        "face": "#141414",
        "light": "#1c1c1c",
        "dark": "#8a8a8a",
        "black": "#f2f2f2",
        "blue": "#f2f2f2",
        "white": "#1c1c1c",
        "edge": "#3a3a3a",
        "button": "#1c1c1c",
        "button_active": "#2a2a2a",
        "tab_idle": "#1c1c1c",
        "tab_active": "#f2f2f2",
        "title_text": "#0a0a0a",
        "glass_top": "#141414",
        "glass_mid": "#f2f2f2",
        "glass_bottom": "#e5e5e5",
        "status_top": "#141414",
        "status_bottom": "#141414",
        "link": "#d4d4d4",
        "accent_text": "#0a0a0a",
        "disabled": "#666666",
        "header_button": "#e5e5e5",
        "header_button_active": "#d0d0d0",
        "focus": "#f2f2f2",
    },
}

TRANSLATIONS = {
    "es": {
        "app_title": "FissileKit",
        "list_placeholder": "Escribe o pega una entrada por linea. Puedes mezclar terminos y links.",
        "youtube_batch_placeholder": "Un enlace por linea. Misma calidad para todos.",
        "ready": "Listo.",
        "welcome_log": "Bienvenido.",
        "hotkey_preparing": "Captura rapida global: preparando...",
        "hotkey_status_unavailable": "Tecla: no disponible",
        "hotkey_status_disabled": "Tecla: desactivada",
        "hotkey_status_format": "Tecla: {hotkey}",
        "tab_youtube": "Videos",
        "tab_images": "Imagenes",
        "status_label": "Estado:",
        "last_label": "Ultima:",
        "last_empty": "Ninguna accion reciente.",
        "paste": "Pegar",
        "send_batch": "Enviar",
        "batch_link_label": "Link de video",
        "batch_format_label": "Formato",
        "change_folder": "Cambiar",
        "folder_prefix": "Carpeta:",
        "image_link_label": "Link de imagen o nombre",
        "preview_label": "Preview",
        "quality_baja": "Baja",
        "quality_media": "Media",
        "quality_alta": "Alta",
        "format_auto": "Automatico",
        "video_item_label": "Video {index}",
        "photo_item_label": "Foto {index}",
        "log_group": "Registro",
        "brand_credit": "Desarrollado por FissilePond",
        "donations_link": "Donaciones",
        "youtube_data_group": "Datos",
        "youtube_options_group": "Opciones",
        "youtube_single_group": "1. Un enlace",
        "youtube_step_hint": "Elige formato y carpeta arriba. Un enlace: descarga directo. Varios: agregalos al lote.",
        "images_step_hint": "Arma la lista, busca o pega imagenes, revisa el lote a la derecha y descarga abajo.",
        "youtube_link_label": "Enlace",
        "youtube_add_batch": "Al lote",
        "youtube_batch_group": "2. Varios enlaces (opcional)",
        "youtube_hotkey_toggle": "Tecla global envia al lote de esta pestana",
        "load_txt": "Cargar .txt",
        "clear_batch": "Limpiar lote",
        "clear_list": "Limpiar lista",
        "clear_image_batch": "Limpiar lote",
        "download_batch": "Descargar lote",
        "format_group": "Formato",
        "quality_group": "Calidad",
        "quality_best": "Mejor disponible",
        "output_folder": "Carpeta de salida",
        "browse": "Buscar...",
        "open_folder": "Abrir carpeta",
        "download": "Descargar enlace",
        "how_to_use": "Como usar",
        "youtube_how_to_use_text": "Uno: pega un link y descarga.\nVarios: agregalos al lote y descarga todo.",
        "search_group": "1. Lista de busqueda",
        "search_header_text": "Buscador, lista y lote.",
        "source_label": "Fuente",
        "add_to_list": "Agregar termino o URL",
        "add": "Agregar",
        "current_list": "Terminos y links",
        "search_images": "Buscar imagenes",
        "quick_paste_group": "2. Agregar al lote",
        "paste_now": "Pegar ahora",
        "final_image_batch": "3. Lote final",
        "final_batch_text": "Revisa, quita o cambia el lote.",
        "save_group": "Guardado",
        "replace_button": "Otra",
        "remove_button": "Quitar",
        "empty_batch_text": "El lote esta vacio. Agrega links, imagenes pegadas o resultados de busqueda.",
        "clipboard_image_title": "Imagen pegada {position}",
        "clipboard_subtitle": "Portapapeles",
        "direct_url_subtitle": "URL directa",
        "settings_title": "Configuracion",
        "settings_button": "Configuracion",
        "settings_group": "Ajustes",
        "appearance_group": "Apariencia",
        "theme_label": "Tema",
        "theme_dark": "Oscuro",
        "theme_light": "Claro",
        "language_label": "Idioma",
        "language_es": "Espanol",
        "language_en": "Ingles",
        "search_settings_group": "Buscadores",
        "search_settings_info_default": "Pexels usa API key. Flickr Public funciona sin clave.",
        "pexels_api_label": "API key de Pexels",
        "save": "Guardar",
        "clear": "Borrar",
        "hotkey_label": "Tecla rapida global",
        "hotkey_info_missing_keyboard": "Instala keyboard para usar una tecla global.",
        "hotkey_info_help": "Ejemplos: x, f8, ctrl+shift+x. Si estas escribiendo en un campo de texto, no captura.",
        "search_source_info_pexels": "Pexels usa API key. Guardala aqui y quedara oculta del panel principal.",
        "search_source_info_flickr": "Flickr Public no necesita API key. Puedes cambiar a Pexels cuando quieras.",
        "search_source_detail_pexels": "Buscando con Pexels. Esta fuente requiere API key.",
        "search_source_detail_flickr": "Buscando con Flickr Public. Esta fuente no requiere API key.",
        "section_ready_youtube": "Pega un enlace arriba o arma un lote para descargar varios.",
        "section_ready_images": "Agrega terminos a la lista, busca o pega, y revisa el lote antes de descargar.",
        "youtube_batch_summary": "Lote YouTube: {total} link(s)",
        "image_batch_summary": "Lote final: {total} elemento(s) | URLs: {urls} | Portapapeles: {clipboard} | Busqueda: {searches}",
        "missing_help_file": "No se encontro el instructivo: {name}",
        "hotkey_dependency_warning": "La captura global requiere la dependencia keyboard.",
        "hotkey_register_error": "No se pudo registrar la tecla: {error}",
        "hotkey_save_empty": "Escribe primero una tecla o combinacion.",
        "hotkey_saved_status": "Tecla guardada.",
        "hotkey_saved_detail": "Captura rapida lista con {hotkey}.",
        "hotkey_disabled_status": "Tecla desactivada.",
        "hotkey_disabled_detail": "La captura rapida global fue desactivada.",
        "hotkey_registered_log": "Tecla global registrada: {hotkey}",
        "hotkey_configured_log": "Captura rapida global configurada con: {hotkey}",
        "hotkey_disabled_log": "Se desactivo la captura rapida global.",
        "autopaste_enabled_detail": "Envio al lote con la tecla global activado para {section}.",
        "autopaste_disabled_detail": "Envio al lote con la tecla global desactivado para {section}.",
        "pexels_key_empty": "Escribe primero tu API key de Pexels.",
        "key_saved_status": "Clave guardada.",
        "key_saved_detail": "API key guardada en {name}.",
        "key_saved_log": "La API key de Pexels se guardo en configuracion local.",
        "key_cleared_status": "Clave borrada.",
        "key_cleared_detail": "La API key guardada se elimino de la configuracion local.",
        "key_cleared_log": "La API key guardada de Pexels fue eliminada.",
        "youtube_missing_link": "Pega primero un link de YouTube.",
        "youtube_link_added_log": "Se agrego un link al lote de YouTube.",
        "clipboard_no_text": "No se encontro texto util en el portapapeles.",
        "clipboard_no_data": "No se encontro una imagen ni texto util en el portapapeles.",
        "file_read_error": "No se pudo leer el archivo: {error}",
        "file_empty": "El archivo esta vacio.",
        "search_entries_missing": "Agrega al menos un termino o link a la lista.",
        "load_queries_title": "Cargar consultas",
        "load_youtube_title": "Cargar links de YouTube",
        "text_files": "Archivos de texto",
        "all_files": "Todos los archivos",
        "queries_loaded_log": "Se cargaron consultas desde: {path}",
        "youtube_links_loaded_log": "Se cargaron links de YouTube desde: {path}",
        "operation_busy": "Ya hay una operacion en proceso.",
        "preparing_batch": "Preparando lote...",
        "preparing_download": "Preparando descarga...",
        "preparing_images": "Preparando imagenes...",
        "searching_images": "Buscando imagenes...",
        "searching_replacement": "Buscando reemplazo...",
        "clipboard_images_added_log": "Se agregaron {count} imagen(es) desde el portapapeles.",
        "image_added_status": "Imagen agregada.",
        "image_added_detail": "Lote actualizado con {count} imagen(es) pegadas.",
        "list_updated_status": "Lista actualizada.",
        "list_updated_detail": "El texto o link pegado se agrego a la lista.",
        "clipboard_list_log": "Se agrego texto del portapapeles a la lista.",
        "youtube_batch_updated_status": "Lote actualizado.",
        "youtube_batch_updated_detail": "Se agregaron {count} link(s) de YouTube al lote.",
        "youtube_batch_updated_text_detail": "El texto pegado se agrego al lote de YouTube.",
        "youtube_batch_updated_log": "Se agregaron {count} link(s) al lote de YouTube.",
        "youtube_batch_updated_text_log": "Se agrego texto del portapapeles al lote de YouTube.",
        "youtube_batch_empty_warning": "Agrega al menos un link al lote de YouTube.",
        "youtube_audio_no_ffmpeg_info": (
            "Sin FFmpeg en el PATH solo se descargan pistas de audio puras "
            "(M4A/WebM/Opus), no MP3. Instala FFmpeg para convertir a MP3."
        ),
        "youtube_audio_retry_log": "Formato no disponible, probando otra opcion de audio...",
        "youtube_audio_error_need_ffmpeg": (
            "YouTube no ofrecio una pista solo-audio para este video.\n\n"
            "Instala FFmpeg y agregalo al PATH para extraer MP3, o actualiza "
            "FissileKit (yt-dlp reciente lo necesita para YouTube)."
        ),
        "image_batch_empty_warning": "El lote esta vacio.",
        "theme_changed_status": "Tema actualizado.",
        "theme_changed_log": "Tema cambiado a {theme}.",
        "language_changed_status": "Idioma actualizado.",
        "language_changed_log": "Idioma cambiado a {language}.",
        "saved_items_count": "Elementos a guardar: {count}",
        "hotkey_youtube_detail": "Tecla global {hotkey} enviada al lote de YouTube.",
        "hotkey_images_detail": "Tecla global {hotkey} enviada al lote de Imagenes.",
        "operation_failed_status": "La operacion fallo.",
        "operation_failed_detail": "Revisa los datos e intenta de nuevo.",
        "removed_from_batch_log": "Se elimino del lote: {title}",
        "images_batch_cleared_log": "Se limpio el lote final de imagenes.",
        "replaced_image_log": "Se reemplazo la imagen de: {title}",
    },
    "en": {
        "app_title": "FissileKit",
        "list_placeholder": "Write or paste one entry per line. You can mix search terms and links.",
        "youtube_batch_placeholder": "One link per line. Same quality for all.",
        "ready": "Ready.",
        "welcome_log": "Welcome.",
        "hotkey_preparing": "Global quick capture: preparing...",
        "hotkey_status_unavailable": "Key: unavailable",
        "hotkey_status_disabled": "Key: disabled",
        "hotkey_status_format": "Key: {hotkey}",
        "tab_youtube": "Videos",
        "tab_images": "Images",
        "status_label": "Status:",
        "last_label": "Last:",
        "last_empty": "No recent action.",
        "paste": "Paste",
        "send_batch": "Send",
        "batch_link_label": "Video link",
        "batch_format_label": "Format",
        "change_folder": "Change",
        "folder_prefix": "Folder:",
        "image_link_label": "Image link or name",
        "preview_label": "Preview",
        "quality_baja": "Low",
        "quality_media": "Medium",
        "quality_alta": "High",
        "format_auto": "Automatic",
        "video_item_label": "Video {index}",
        "photo_item_label": "Photo {index}",
        "log_group": "Log",
        "brand_credit": "Built by FissilePond",
        "donations_link": "Donations",
        "youtube_data_group": "Data",
        "youtube_options_group": "Options",
        "youtube_single_group": "1. Single link",
        "youtube_step_hint": "Pick format and folder above. One link: download directly. Many: add them to the batch.",
        "images_step_hint": "Build the list, search or paste images, review the batch on the right, then download below.",
        "youtube_link_label": "Link",
        "youtube_add_batch": "To batch",
        "youtube_batch_group": "2. Multiple links (optional)",
        "youtube_hotkey_toggle": "Global hotkey sends to this tab's batch",
        "load_txt": "Load .txt",
        "clear_batch": "Clear batch",
        "clear_list": "Clear list",
        "clear_image_batch": "Clear batch",
        "download_batch": "Download batch",
        "format_group": "Format",
        "quality_group": "Quality",
        "quality_best": "Best available",
        "output_folder": "Output folder",
        "browse": "Browse...",
        "open_folder": "Open folder",
        "download": "Download link",
        "how_to_use": "How to use",
        "youtube_how_to_use_text": "Single: paste a link and download.\nMultiple: add them to the batch and download all.",
        "search_group": "1. Search list",
        "search_header_text": "Search, list, and batch.",
        "source_label": "Source",
        "add_to_list": "Add term or URL",
        "add": "Add",
        "current_list": "Terms and links",
        "search_images": "Search images",
        "quick_paste_group": "2. Add to batch",
        "paste_now": "Paste now",
        "final_image_batch": "3. Final batch",
        "final_batch_text": "Review, remove, or swap items in the batch.",
        "save_group": "Save",
        "replace_button": "Next",
        "remove_button": "Remove",
        "empty_batch_text": "The batch is empty. Add links, pasted images, or search results.",
        "clipboard_image_title": "Pasted image {position}",
        "clipboard_subtitle": "Clipboard",
        "direct_url_subtitle": "Direct URL",
        "settings_title": "Settings",
        "settings_button": "Settings",
        "settings_group": "Preferences",
        "appearance_group": "Appearance",
        "theme_label": "Theme",
        "theme_dark": "Dark",
        "theme_light": "Light",
        "language_label": "Language",
        "language_es": "Spanish",
        "language_en": "English",
        "search_settings_group": "Search Providers",
        "search_settings_info_default": "Pexels uses an API key. Flickr Public works without one.",
        "pexels_api_label": "Pexels API key",
        "save": "Save",
        "clear": "Clear",
        "hotkey_label": "Global hotkey",
        "hotkey_info_missing_keyboard": "Install keyboard to use a global hotkey.",
        "hotkey_info_help": "Examples: x, f8, ctrl+shift+x. If you are typing in a text field, it will not capture.",
        "search_source_info_pexels": "Pexels uses an API key. Save it here and it will stay hidden from the main panel.",
        "search_source_info_flickr": "Flickr Public does not need an API key. You can switch back to Pexels anytime.",
        "search_source_detail_pexels": "Searching with Pexels. This source requires an API key.",
        "search_source_detail_flickr": "Searching with Flickr Public. This source does not require an API key.",
        "section_ready_youtube": "Paste a link above or build a batch to download several at once.",
        "section_ready_images": "Add terms to the list, search or paste, then review the batch before downloading.",
        "youtube_batch_summary": "YouTube batch: {total} link(s)",
        "image_batch_summary": "Final batch: {total} item(s) | URLs: {urls} | Clipboard: {clipboard} | Search: {searches}",
        "missing_help_file": "Help file not found: {name}",
        "hotkey_dependency_warning": "Global capture requires the keyboard dependency.",
        "hotkey_register_error": "Could not register the key: {error}",
        "hotkey_save_empty": "Enter a key or key combination first.",
        "hotkey_saved_status": "Key saved.",
        "hotkey_saved_detail": "Quick capture is ready with {hotkey}.",
        "hotkey_disabled_status": "Key disabled.",
        "hotkey_disabled_detail": "Global quick capture was disabled.",
        "hotkey_registered_log": "Global key registered: {hotkey}",
        "hotkey_configured_log": "Global quick capture configured with: {hotkey}",
        "hotkey_disabled_log": "Global quick capture was disabled.",
        "autopaste_enabled_detail": "Batch send with global hotkey enabled for {section}.",
        "autopaste_disabled_detail": "Batch send with global hotkey disabled for {section}.",
        "pexels_key_empty": "Enter your Pexels API key first.",
        "key_saved_status": "Key saved.",
        "key_saved_detail": "API key saved in {name}.",
        "key_saved_log": "The Pexels API key was saved locally.",
        "key_cleared_status": "Key cleared.",
        "key_cleared_detail": "The saved API key was removed from local settings.",
        "key_cleared_log": "The saved Pexels API key was removed.",
        "youtube_missing_link": "Paste a YouTube link first.",
        "youtube_link_added_log": "A link was added to the YouTube batch.",
        "clipboard_no_text": "No useful text was found in the clipboard.",
        "clipboard_no_data": "No useful image or text was found in the clipboard.",
        "file_read_error": "Could not read the file: {error}",
        "file_empty": "The file is empty.",
        "search_entries_missing": "Add at least one term or link to the list.",
        "load_queries_title": "Load queries",
        "load_youtube_title": "Load YouTube links",
        "text_files": "Text files",
        "all_files": "All files",
        "queries_loaded_log": "Queries loaded from: {path}",
        "youtube_links_loaded_log": "YouTube links loaded from: {path}",
        "operation_busy": "There is already an operation in progress.",
        "preparing_batch": "Preparing batch...",
        "preparing_download": "Preparing download...",
        "preparing_images": "Preparing images...",
        "searching_images": "Searching images...",
        "searching_replacement": "Searching replacement...",
        "clipboard_images_added_log": "{count} image(s) added from the clipboard.",
        "image_added_status": "Image added.",
        "image_added_detail": "Batch updated with {count} pasted image(s).",
        "list_updated_status": "List updated.",
        "list_updated_detail": "The pasted text or link was added to the list.",
        "clipboard_list_log": "Clipboard text was added to the list.",
        "youtube_batch_updated_status": "Batch updated.",
        "youtube_batch_updated_detail": "{count} YouTube link(s) added to the batch.",
        "youtube_batch_updated_text_detail": "The pasted text was added to the YouTube batch.",
        "youtube_batch_updated_log": "{count} link(s) added to the YouTube batch.",
        "youtube_batch_updated_text_log": "Clipboard text was added to the YouTube batch.",
        "youtube_batch_empty_warning": "Add at least one YouTube link to the batch.",
        "youtube_audio_no_ffmpeg_info": (
            "Without FFmpeg in PATH only pure audio tracks are downloaded "
            "(M4A/WebM/Opus), not MP3. Install FFmpeg to convert to MP3."
        ),
        "youtube_audio_retry_log": "Format not available, trying another audio option...",
        "youtube_audio_error_need_ffmpeg": (
            "YouTube did not expose an audio-only track for this video.\n\n"
            "Install FFmpeg and add it to PATH to extract MP3, or update "
            "FissileKit (recent yt-dlp is required for YouTube)."
        ),
        "image_batch_empty_warning": "The batch is empty.",
        "theme_changed_status": "Theme updated.",
        "theme_changed_log": "Theme changed to {theme}.",
        "language_changed_status": "Language updated.",
        "language_changed_log": "Language changed to {language}.",
        "saved_items_count": "Items to save: {count}",
        "hotkey_youtube_detail": "Global key {hotkey} sent content to the YouTube batch.",
        "hotkey_images_detail": "Global key {hotkey} sent content to the Images batch.",
        "operation_failed_status": "The operation failed.",
        "operation_failed_detail": "Check the data and try again.",
        "removed_from_batch_log": "Removed from batch: {title}",
        "images_batch_cleared_log": "The final image batch was cleared.",
        "replaced_image_log": "Replaced image: {title}",
    },
}

if os.name == "nt":
    user32 = ctypes.windll.user32

    class GUITHREADINFO(ctypes.Structure):
        _fields_ = [
            ("cbSize", wintypes.DWORD),
            ("flags", wintypes.DWORD),
            ("hwndActive", wintypes.HWND),
            ("hwndFocus", wintypes.HWND),
            ("hwndCapture", wintypes.HWND),
            ("hwndMenuOwner", wintypes.HWND),
            ("hwndMoveSize", wintypes.HWND),
            ("hwndCaret", wintypes.HWND),
            ("rcCaret", wintypes.RECT),
        ]

WIN_DESKTOP = THEME_PALETTES[DEFAULT_THEME]["desktop"]
WIN_FACE = THEME_PALETTES[DEFAULT_THEME]["face"]
WIN_LIGHT = THEME_PALETTES[DEFAULT_THEME]["light"]
WIN_DARK = THEME_PALETTES[DEFAULT_THEME]["dark"]
WIN_BLACK = THEME_PALETTES[DEFAULT_THEME]["black"]
WIN_BLUE = THEME_PALETTES[DEFAULT_THEME]["blue"]
WIN_WHITE = THEME_PALETTES[DEFAULT_THEME]["white"]
WIN_EDGE = THEME_PALETTES[DEFAULT_THEME]["edge"]
WIN_BUTTON = THEME_PALETTES[DEFAULT_THEME]["button"]
WIN_BUTTON_ACTIVE = THEME_PALETTES[DEFAULT_THEME]["button_active"]
WIN_TAB_IDLE = THEME_PALETTES[DEFAULT_THEME]["tab_idle"]
WIN_TAB_ACTIVE = THEME_PALETTES[DEFAULT_THEME]["tab_active"]
WIN_TITLE_TEXT = THEME_PALETTES[DEFAULT_THEME]["title_text"]
WIN_GLASS_TOP = THEME_PALETTES[DEFAULT_THEME]["glass_top"]
WIN_GLASS_MID = THEME_PALETTES[DEFAULT_THEME]["glass_mid"]
WIN_GLASS_BOTTOM = THEME_PALETTES[DEFAULT_THEME]["glass_bottom"]
WIN_STATUS_TOP = THEME_PALETTES[DEFAULT_THEME]["status_top"]
WIN_STATUS_BOTTOM = THEME_PALETTES[DEFAULT_THEME]["status_bottom"]
WIN_LINK = THEME_PALETTES[DEFAULT_THEME]["link"]
WIN_ACCENT_TEXT = THEME_PALETTES[DEFAULT_THEME]["accent_text"]
WIN_DISABLED = THEME_PALETTES[DEFAULT_THEME]["disabled"]
WIN_HEADER_BUTTON = THEME_PALETTES[DEFAULT_THEME]["header_button"]
WIN_HEADER_BUTTON_ACTIVE = THEME_PALETTES[DEFAULT_THEME]["header_button_active"]
WIN_FOCUS = THEME_PALETTES[DEFAULT_THEME]["focus"]

FONT_NORMAL = ("Segoe UI", 10)
FONT_BOLD = ("Segoe UI", 10, "bold")
FONT_TITLE = ("Segoe UI", 12)
FONT_SMALL = ("Segoe UI", 9)
FONT_CAPTION = ("Segoe UI", 8)

VIDEO_QUALITY_KEYS = [
    ("quality_best", "best"),
    ("2160p (4K)", "2160"),
    ("1440p", "1440"),
    ("1080p", "1080"),
    ("720p", "720"),
    ("480p", "480"),
    ("360p", "360"),
]

AUDIO_QUALITY_KEYS = [
    ("quality_best", "best"),
    ("320 kbps", "320"),
    ("256 kbps", "256"),
    ("192 kbps", "192"),
    ("128 kbps", "128"),
    ("96 kbps", "96"),
]


def format_bytes(value):
    if not value:
        return "0 B"

    size = float(value)
    for unit in ("B", "KB", "MB", "GB", "TB"):
        if size < 1024 or unit == "TB":
            return f"{size:.1f} {unit}"
        size /= 1024
    return f"{size:.1f} TB"


def is_ffmpeg_available():
    if shutil.which("ffmpeg"):
        return True
    if getattr(sys, "frozen", False):
        for name in ("ffmpeg.exe", "ffmpeg"):
            if (Path(sys.executable).parent / name).exists():
                return True
    return False


def ffmpeg_location():
    found = shutil.which("ffmpeg")
    if found:
        return found
    if getattr(sys, "frozen", False):
        for name in ("ffmpeg.exe", "ffmpeg"):
            candidate = Path(sys.executable).parent / name
            if candidate.exists():
                return str(candidate)
    return None


ANSI_ESCAPE_RE = re.compile(r"\x1b\[[0-9;]*m")


def strip_ansi(text):
    return ANSI_ESCAPE_RE.sub("", str(text))


def is_format_unavailable_error(error):
    message = strip_ansi(error).lower()
    return "requested format is not available" in message


def youtube_dl_extra_options():
    options = {}
    deno = shutil.which("deno")
    node = shutil.which("node")
    if deno:
        options["js_runtimes"] = {"deno": {}}
    elif node:
        options["js_runtimes"] = {"node": {}}
    return options


def audio_format_candidates(has_ffmpeg):
    candidates = [
        "bestaudio[ext=m4a]/bestaudio[ext=webm]/bestaudio",
        "140/251/250/139/bestaudio",
        "bestaudio",
    ]
    if has_ffmpeg:
        candidates.append("bestaudio/best")
    return candidates


def format_speed(value):
    if not value:
        return "-"
    return f"{format_bytes(value)}/s"


def sanitize_filename(name):
    invalid_chars = '<>:"/\\|?*'
    clean = "".join("_" if ch in invalid_chars or ord(ch) < 32 else ch for ch in name)
    clean = clean.strip(" .")
    return clean[:120] or "archivo"


def ensure_unique_path(path):
    if not path.exists():
        return path

    stem = path.stem
    suffix = path.suffix
    index = 2
    while True:
        candidate = path.with_name(f"{stem} ({index}){suffix}")
        if not candidate.exists():
            return candidate
        index += 1


def guess_image_extension(url, content_type):
    parsed_path = urllib.parse.unquote(urllib.parse.urlparse(url).path)
    suffix = Path(parsed_path).suffix.lower()
    if suffix:
        return suffix

    main_type = (content_type or "").split(";")[0].strip().lower()
    if main_type == "image/jpeg":
        return ".jpg"

    guessed = mimetypes.guess_extension(main_type)
    return guessed or ".jpg"


class DownloaderApp(tk.Tk):
    def __init__(self):
        super().__init__()

        self.settings = self._load_settings()
        saved_theme = self._setting("ui_theme", DEFAULT_THEME)
        if saved_theme not in THEME_PALETTES:
            saved_theme = DEFAULT_THEME

        saved_language = self._setting("ui_language", DEFAULT_LANGUAGE)
        if saved_language not in TRANSLATIONS:
            saved_language = DEFAULT_LANGUAGE

        self.theme_var = tk.StringVar(value=saved_theme)
        self.language_var = tk.StringVar(value=saved_language)
        self._apply_theme_palette(saved_theme)

        self.title(self._app_title())
        self.geometry("1080x740")
        self.minsize(860, 600)
        self.configure(bg=WIN_DESKTOP)

        saved_search_source = self._setting("image_search_source", "Pexels")
        if saved_search_source not in SEARCH_SOURCES:
            saved_search_source = "Flickr Public" if saved_search_source == "Wikimedia Commons" else "Pexels"
        saved_capture_hotkey = self._normalize_hotkey(
            self._setting("capture_hotkey", DEFAULT_CAPTURE_HOTKEY)
        )

        self.section_var = tk.StringVar(value="youtube")
        self.url_var = tk.StringVar()
        self.batch_url_var = tk.StringVar()
        self.mode_var = tk.StringVar(value="Video")
        self.quality_var = tk.StringVar()
        self.batch_quality_var = tk.StringVar()
        self.batch_format_var = tk.StringVar(value="mp4")
        saved_video_folder = self._setting("video_output_folder", str(DEFAULT_YOUTUBE_FOLDER))
        saved_image_folder = self._setting("image_output_folder", str(DEFAULT_IMAGE_FOLDER))
        self.output_var = tk.StringVar(value=saved_video_folder)
        self.image_output_var = tk.StringVar(value=saved_image_folder)
        self.image_format_var = tk.StringVar(value=self._setting("image_export_format", "auto"))
        self.image_quality_var = tk.StringVar(value=self._setting("image_export_quality", "media"))
        self.pexels_key_var = tk.StringVar(value=self.settings.get("pexels_api_key", ""))
        self.search_source_var = tk.StringVar(value=saved_search_source)
        self.list_entry_var = tk.StringVar()
        self.youtube_batch_urls = []
        self.youtube_autopaste_var = tk.BooleanVar(
            value=bool(self._setting("youtube_autopaste_enabled", False))
        )
        self.images_autopaste_var = tk.BooleanVar(
            value=bool(self._setting("images_autopaste_enabled", False))
        )
        self.capture_hotkey_var = tk.StringVar(value=saved_capture_hotkey)
        self.capture_status_var = tk.StringVar(value=self._t("hotkey_preparing"))
        self.status_var = tk.StringVar(value=self._t("ready"))
        self.detail_var = tk.StringVar(value=self._t("section_ready_youtube"))
        self.last_action_var = tk.StringVar(value=self._t("last_empty"))
        self.batch_summary_var = tk.StringVar(
            value=self._t("image_batch_summary", total=0, urls=0, clipboard=0, searches=0)
        )
        self.image_preview_photo = None
        self.selected_image_index = None

        self.worker_queue = queue.Queue()
        self.active_thread = None
        self.current_quality_map = {}
        self.current_progress = 0.0

        self.image_items = []
        self.next_item_id = 1
        self.settings_window = None
        self.settings_info_label = None
        self.settings_key_entry = None
        self.settings_save_button = None
        self.settings_clear_button = None
        self.settings_hotkey_info_label = None
        self.settings_hotkey_entry = None
        self.settings_hotkey_save_button = None
        self.settings_hotkey_clear_button = None
        self.capture_hotkey_handle = None
        self.capture_hotkey_kind = None
        self.is_closing = False
        self.ui_photo_refs = []

        self._build_ui()
        self._update_quality_options("Video")
        self._set_section("youtube")
        self.protocol("WM_DELETE_WINDOW", self._on_close)
        self.bind("<Return>", self._handle_enter)
        self.bind("<Control-v>", self._handle_global_paste)
        self.bind("<Control-V>", self._handle_global_paste)
        self._apply_capture_hotkey(startup=True)
        self.after(100, self._process_queue)

    def _build_ui(self):
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(0, weight=1)

        app = tk.Frame(self, bg=WIN_FACE, bd=1, relief="solid", highlightbackground=WIN_EDGE)
        app.grid(row=0, column=0, sticky="nsew", padx=12, pady=12)
        app.grid_columnconfigure(0, weight=1)
        app.grid_rowconfigure(1, weight=1)

        title_bar = tk.Frame(app, bg=WIN_BLUE, height=40, bd=0)
        title_bar.grid(row=0, column=0, sticky="ew")
        title_bar.grid_columnconfigure(1, weight=1)
        title_bar.grid_propagate(False)

        tk.Label(
            title_bar,
            text="FK",
            bg=WIN_BLUE,
            fg=WIN_TITLE_TEXT,
            font=("Segoe UI", 9, "bold"),
            width=3,
        ).grid(row=0, column=0, padx=(12, 8), pady=8)

        tk.Label(
            title_bar,
            text=self._app_title(),
            bg=WIN_BLUE,
            fg=WIN_TITLE_TEXT,
            font=FONT_TITLE,
        ).grid(row=0, column=1, sticky="w")

        title_links = tk.Frame(title_bar, bg=WIN_BLUE)
        title_links.grid(row=0, column=2, sticky="e", padx=(0, 8))
        self._make_title_link(title_links, self._t("brand_credit"), SITE_URL).grid(
            row=0, column=0, padx=(0, 10)
        )
        self._make_title_link(title_links, self._t("donations_link"), DONATION_URL).grid(
            row=0, column=1
        )

        self.help_button = tk.Button(
            title_bar,
            text="?",
            command=self._open_help_file,
            width=3,
            bg=WIN_HEADER_BUTTON,
            fg=WIN_TITLE_TEXT,
            activebackground=WIN_HEADER_BUTTON_ACTIVE,
            activeforeground=WIN_TITLE_TEXT,
            relief="flat",
            bd=0,
            font=FONT_BOLD,
            cursor="hand2",
        )
        self.help_button.grid(row=0, column=3, sticky="e", padx=(6, 4), pady=6)

        self.settings_button = tk.Button(
            title_bar,
            text=self._t("settings_button"),
            command=self._open_search_settings,
            bg=WIN_HEADER_BUTTON,
            fg=WIN_TITLE_TEXT,
            activebackground=WIN_HEADER_BUTTON_ACTIVE,
            activeforeground=WIN_TITLE_TEXT,
            relief="flat",
            bd=0,
            font=FONT_NORMAL,
            padx=10,
            pady=4,
            cursor="hand2",
        )
        self.settings_button.grid(row=0, column=4, sticky="e", padx=(0, 12), pady=6)

        self.main_paned = tk.PanedWindow(
            app,
            orient=tk.VERTICAL,
            sashwidth=5,
            sashrelief=tk.FLAT,
            bg=WIN_EDGE,
            bd=0,
            showhandle=True,
            opaqueresize=True,
        )
        self.main_paned.grid(row=1, column=0, sticky="nsew", padx=12, pady=(0, 12))

        body = tk.Frame(self.main_paned, bg=WIN_FACE)
        body.grid_columnconfigure(0, weight=1)
        body.grid_rowconfigure(1, weight=1)

        tabs = tk.Frame(body, bg=WIN_FACE)
        tabs.grid(row=0, column=0, sticky="w", padx=12, pady=(12, 10))

        self.youtube_tab_button = self._make_button(
            tabs, self._t("tab_youtube"), lambda: self._set_section("youtube"), width=14
        )
        self.youtube_tab_button.grid(row=0, column=0, padx=(0, 6))

        self.images_tab_button = self._make_button(
            tabs, self._t("tab_images"), lambda: self._set_section("imagenes"), width=14
        )
        self.images_tab_button.grid(row=0, column=1)

        self.content = tk.Frame(body, bg=WIN_WHITE, bd=1, relief="solid", highlightbackground=WIN_EDGE)
        self.content.grid(row=1, column=0, sticky="nsew", padx=12, pady=(0, 12))
        self.content.grid_columnconfigure(0, weight=1)
        self.content.grid_rowconfigure(0, weight=1)

        self.youtube_frame = self._build_youtube_panel(self.content)
        self.youtube_frame.grid(row=0, column=0, sticky="nsew", padx=10, pady=10)

        self.images_frame = self._build_images_panel(self.content)
        self.images_frame.grid(row=0, column=0, sticky="nsew", padx=10, pady=10)

        bottom = tk.Frame(self.main_paned, bg=WIN_STATUS_TOP, bd=1, relief="solid", highlightbackground=WIN_EDGE)
        self.main_paned.add(body, minsize=260)
        self.main_paned.add(bottom, minsize=168)

        bottom.grid_columnconfigure(0, weight=1)
        bottom.grid_rowconfigure(4, weight=1)

        status_top = tk.Frame(bottom, bg=WIN_STATUS_TOP)
        status_top.grid(row=0, column=0, sticky="ew", padx=10, pady=(8, 2))
        status_top.grid_columnconfigure(1, weight=1)

        tk.Label(
            status_top,
            text=self._t("status_label"),
            bg=WIN_STATUS_TOP,
            fg=WIN_DARK,
            font=FONT_CAPTION,
        ).grid(row=0, column=0, sticky="w")

        tk.Label(
            status_top,
            textvariable=self.status_var,
            bg=WIN_WHITE,
            fg=WIN_BLACK,
            relief="solid",
            bd=1,
            highlightbackground=WIN_EDGE,
            font=FONT_NORMAL,
            anchor="w",
            padx=6,
            pady=2,
        ).grid(row=0, column=1, sticky="ew", padx=(8, 8))

        self.status_hotkey_label = tk.Label(
            status_top,
            textvariable=self.capture_status_var,
            bg=WIN_STATUS_TOP,
            fg=WIN_DARK,
            font=FONT_CAPTION,
            anchor="e",
        )
        self.status_hotkey_label.grid(row=0, column=2, sticky="e")

        self.detail_label = tk.Label(
            bottom,
            textvariable=self.detail_var,
            bg=WIN_STATUS_TOP,
            fg=WIN_DARK,
            anchor="w",
            justify="left",
            font=FONT_CAPTION,
            wraplength=700,
        )
        self.detail_label.grid(row=1, column=0, sticky="ew", padx=10, pady=(0, 2))

        self.batch_summary_label = tk.Label(
            bottom,
            textvariable=self.batch_summary_var,
            bg=WIN_STATUS_TOP,
            fg=WIN_BLACK,
            anchor="w",
            font=FONT_CAPTION,
            wraplength=700,
        )
        self.batch_summary_label.grid(row=2, column=0, sticky="ew", padx=10, pady=(0, 2))

        last_row = tk.Frame(bottom, bg=WIN_STATUS_TOP)
        last_row.grid(row=3, column=0, sticky="ew", padx=10, pady=(0, 4))
        tk.Label(
            last_row,
            text=self._t("last_label"),
            bg=WIN_STATUS_TOP,
            fg=WIN_DARK,
            font=FONT_CAPTION,
        ).grid(row=0, column=0, sticky="w")
        tk.Label(
            last_row,
            textvariable=self.last_action_var,
            bg=WIN_STATUS_TOP,
            fg=WIN_BLACK,
            anchor="w",
            font=FONT_CAPTION,
            wraplength=700,
        ).grid(row=0, column=1, sticky="ew", padx=(8, 0))
        last_row.grid_columnconfigure(1, weight=1)

        log_group = self._make_group(bottom, self._t("log_group"))
        log_group.grid(row=4, column=0, sticky="nsew", padx=10, pady=(4, 8))
        log_group.grid_columnconfigure(0, weight=1)
        log_group.grid_rowconfigure(0, weight=1)

        log_frame = tk.Frame(log_group, bg=WIN_FACE)
        log_frame.grid(row=0, column=0, sticky="nsew", padx=8, pady=8)
        log_frame.grid_columnconfigure(0, weight=1)
        log_frame.grid_rowconfigure(0, weight=1)

        self.log_scrollbar = tk.Scrollbar(log_frame, orient="vertical")
        self.log_scrollbar.grid(row=0, column=1, sticky="ns")

        self.log_box = tk.Text(
            log_frame,
            height=3,
            bg=WIN_WHITE,
            fg=WIN_BLACK,
            relief="solid",
            bd=1,
            highlightbackground=WIN_EDGE,
            highlightthickness=1,
            wrap="word",
            font=FONT_SMALL,
            insertbackground=WIN_BLACK,
            yscrollcommand=self.log_scrollbar.set,
        )
        self.log_box.grid(row=0, column=0, sticky="nsew")
        self.log_scrollbar.configure(command=self.log_box.yview)
        self.log_box.insert("end", f"{self._t('welcome_log')}\n")
        self.log_box.configure(state="disabled")

        self.progress_canvas = tk.Canvas(bottom, width=1, height=1, highlightthickness=0, bd=0)
        self.progress_fill = self.progress_canvas.create_rectangle(
            0, 0, 0, 1, fill=WIN_BLACK, outline=""
        )
        self.progress_text = self.progress_canvas.create_text(
            0, 0, text="0%", anchor="w", fill=WIN_BLACK, font=FONT_SMALL
        )

        self.bind("<Configure>", self._on_root_configure, add="+")
        self.after(150, self._position_main_paned)

    def _on_root_configure(self, event):
        if event.widget is not self:
            return
        wrap = max(event.width - 96, 240)
        for label in (
            getattr(self, "detail_label", None),
            getattr(self, "batch_summary_label", None),
        ):
            if label is not None and label.winfo_exists():
                label.configure(wraplength=wrap)

    def _position_main_paned(self):
        paned = getattr(self, "main_paned", None)
        if paned is None or not paned.winfo_exists():
            return
        try:
            paned.update_idletasks()
            height = paned.winfo_height()
            if height > 220:
                paned.sash_place(0, 0, max(height - 190, 260))
        except tk.TclError:
            pass

    def _make_title_link(self, parent, text, url):
        label = tk.Label(
            parent,
            text=text,
            bg=WIN_BLUE,
            fg=WIN_TITLE_TEXT,
            font=FONT_CAPTION,
            cursor="hand2",
        )
        label.bind("<Button-1>", lambda _event, target=url: self._open_external_url(target))
        return label

    def _make_button(self, parent, text, command, width=12, primary=False):
        if primary:
            bg = WIN_TAB_ACTIVE
            fg = WIN_ACCENT_TEXT
            active_bg = WIN_BLACK
            active_fg = WIN_ACCENT_TEXT
        else:
            bg = WIN_BUTTON
            fg = WIN_BLACK
            active_bg = WIN_BUTTON_ACTIVE
            active_fg = WIN_BLACK

        return tk.Button(
            parent,
            text=text,
            command=command,
            width=width,
            bg=bg,
            fg=fg,
            activebackground=active_bg,
            activeforeground=active_fg,
            disabledforeground=WIN_DISABLED,
            relief="solid",
            bd=1,
            highlightthickness=1,
            highlightbackground=WIN_EDGE,
            highlightcolor=WIN_EDGE,
            font=FONT_NORMAL,
            padx=8,
            pady=4,
            cursor="hand2",
        )

    def _make_group(self, parent, title):
        return tk.LabelFrame(
            parent,
            text=f"  {title}  ",
            bg=WIN_FACE,
            fg=WIN_BLACK,
            bd=1,
            relief="solid",
            highlightbackground=WIN_EDGE,
            font=FONT_CAPTION,
            labelanchor="nw",
            padx=4,
            pady=4,
        )

    def _make_entry(self, parent, textvariable=None):
        return tk.Entry(
            parent,
            textvariable=textvariable,
            bg=WIN_WHITE,
            fg=WIN_BLACK,
            insertbackground=WIN_BLACK,
            relief="solid",
            bd=1,
            highlightthickness=1,
            highlightbackground=WIN_EDGE,
            highlightcolor=WIN_FOCUS,
            font=FONT_NORMAL,
        )

    def _make_option_menu(self, parent, variable, values, command=None):
        menu = tk.OptionMenu(parent, variable, *values, command=command)
        menu.configure(
            bg=WIN_BUTTON,
            fg=WIN_BLACK,
            activebackground=WIN_BUTTON_ACTIVE,
            relief="solid",
            bd=1,
            highlightthickness=1,
            highlightbackground=WIN_EDGE,
            font=FONT_NORMAL,
        )
        menu["menu"].configure(bg=WIN_WHITE, fg=WIN_BLACK, font=FONT_NORMAL)
        return menu

    def _make_text_box(self, parent, height):
        box = tk.Text(
            parent,
            height=height,
            bg=WIN_WHITE,
            fg=WIN_BLACK,
            insertbackground=WIN_BLACK,
            relief="solid",
            bd=1,
            highlightthickness=1,
            highlightbackground=WIN_EDGE,
            highlightcolor=WIN_FOCUS,
            wrap="word",
            font=FONT_NORMAL,
        )
        scrollbar = tk.Scrollbar(parent, orient="vertical", command=box.yview)
        box.configure(yscrollcommand=scrollbar.set)
        return box, scrollbar

    def _make_info_panel(self, parent, text):
        return tk.Label(
            parent,
            text=text,
            bg=WIN_LIGHT,
            fg=WIN_BLACK,
            justify="left",
            anchor="nw",
            relief="solid",
            bd=1,
            highlightbackground=WIN_EDGE,
            font=FONT_SMALL,
            padx=8,
            pady=8,
        )

    def _make_step_hint(self, parent, text):
        return tk.Label(
            parent,
            text=text,
            bg=WIN_LIGHT,
            fg=WIN_DARK,
            justify="left",
            anchor="w",
            relief="solid",
            bd=1,
            highlightbackground=WIN_EDGE,
            font=FONT_CAPTION,
            padx=10,
            pady=8,
        )

    def _t(self, key, **kwargs):
        language = self.language_var.get() if hasattr(self, "language_var") else DEFAULT_LANGUAGE
        base = TRANSLATIONS.get(DEFAULT_LANGUAGE, {})
        text = TRANSLATIONS.get(language, base).get(key, base.get(key, key))
        return text.format(**kwargs) if kwargs else text

    def _app_title(self):
        return self._t("app_title")

    def _theme_label(self, theme_name):
        return self._t(f"theme_{theme_name}")

    def _language_label(self, language_code):
        return self._t(f"language_{language_code}")

    def _list_placeholder(self):
        return self._t("list_placeholder")

    def _youtube_batch_placeholder(self):
        return self._t("youtube_batch_placeholder")

    def _setting(self, key, default=None):
        return self.settings.get(key, default)

    def _set_setting(self, key, value):
        self.settings[key] = value
        self._write_settings()

    def _remove_setting(self, key):
        if key in self.settings:
            del self.settings[key]
            self._write_settings()

    def _apply_theme_palette(self, theme_name):
        palette = THEME_PALETTES.get(theme_name, THEME_PALETTES[DEFAULT_THEME])
        global WIN_DESKTOP, WIN_FACE, WIN_LIGHT, WIN_DARK, WIN_BLACK, WIN_BLUE
        global WIN_WHITE, WIN_EDGE, WIN_BUTTON, WIN_BUTTON_ACTIVE, WIN_TAB_IDLE
        global WIN_TAB_ACTIVE, WIN_TITLE_TEXT, WIN_GLASS_TOP, WIN_GLASS_MID
        global WIN_GLASS_BOTTOM, WIN_STATUS_TOP, WIN_STATUS_BOTTOM, WIN_LINK
        global WIN_ACCENT_TEXT, WIN_DISABLED, WIN_HEADER_BUTTON, WIN_HEADER_BUTTON_ACTIVE
        global WIN_FOCUS

        WIN_DESKTOP = palette["desktop"]
        WIN_FACE = palette["face"]
        WIN_LIGHT = palette["light"]
        WIN_DARK = palette["dark"]
        WIN_BLACK = palette["black"]
        WIN_BLUE = palette["blue"]
        WIN_WHITE = palette["white"]
        WIN_EDGE = palette["edge"]
        WIN_BUTTON = palette["button"]
        WIN_BUTTON_ACTIVE = palette["button_active"]
        WIN_TAB_IDLE = palette["tab_idle"]
        WIN_TAB_ACTIVE = palette["tab_active"]
        WIN_TITLE_TEXT = palette["title_text"]
        WIN_GLASS_TOP = palette["glass_top"]
        WIN_GLASS_MID = palette["glass_mid"]
        WIN_GLASS_BOTTOM = palette["glass_bottom"]
        WIN_STATUS_TOP = palette["status_top"]
        WIN_STATUS_BOTTOM = palette["status_bottom"]
        WIN_LINK = palette["link"]
        WIN_ACCENT_TEXT = palette["accent_text"]
        WIN_DISABLED = palette["disabled"]
        WIN_HEADER_BUTTON = palette["header_button"]
        WIN_HEADER_BUTTON_ACTIVE = palette["header_button_active"]
        WIN_FOCUS = palette["focus"]

    def _placeholder_variants(self, key):
        return {
            TRANSLATIONS[language][key].strip()
            for language in TRANSLATIONS
            if key in TRANSLATIONS[language]
        }

    def _snapshot_text_widget(self, widget, placeholder_key=None):
        if widget is None or not widget.winfo_exists():
            return ""

        content = widget.get("1.0", "end").strip()
        if placeholder_key and content in self._placeholder_variants(placeholder_key):
            return ""
        return content

    def _restore_text_widget(self, widget, content, placeholder_key=None):
        widget.delete("1.0", "end")
        if content:
            widget.insert("end", content)
            widget.configure(fg=WIN_BLACK)
        elif placeholder_key:
            widget.insert("end", self._t(placeholder_key))
            widget.configure(fg=WIN_DARK)

    def _restore_log_text(self, content):
        self.log_box.configure(state="normal")
        self.log_box.delete("1.0", "end")
        self.log_box.insert("end", content or f"{self._t('welcome_log')}\n")
        self.log_box.configure(state="disabled")

    def _clone_image_items(self, items):
        cloned = []
        for item in items:
            copy = dict(item)
            if copy.get("image_data") is not None:
                copy["image_data"] = copy["image_data"].copy()
            if copy.get("preview_image") is not None:
                copy["preview_image"] = copy["preview_image"].copy()
            if copy.get("candidate_results") is not None:
                copy["candidate_results"] = list(copy["candidate_results"])
            cloned.append(copy)
        return cloned

    def _rebuild_ui(self):
        # Theme and language changes are applied by rebuilding the Tk layout
        # while preserving batch data, logs, and the selected section.
        active_section = self.section_var.get()
        snapshot = {
            "youtube_batch_urls": list(self.youtube_batch_urls),
            "image_items": self._clone_image_items(self.image_items),
            "log": self._snapshot_text_widget(getattr(self, "log_box", None)),
        }

        self._close_search_settings()
        for child in self.winfo_children():
            child.destroy()

        self.ui_photo_refs.clear()
        self.image_preview_photo = None
        self.selected_image_index = None

        self.title(self._app_title())
        self.configure(bg=WIN_DESKTOP)
        self._build_ui()
        self.youtube_batch_urls = list(snapshot["youtube_batch_urls"])
        self.image_items = self._clone_image_items(snapshot["image_items"])
        self._refresh_youtube_batch_listbox()
        self._refresh_image_listbox()
        self._restore_log_text(snapshot["log"])
        self._update_quality_options(self.mode_var.get())
        self._set_section(active_section)
        self._refresh_youtube_batch_summary()
        self._apply_search_source_state()

    def _hex_to_rgb(self, color):
        color = color.lstrip("#")
        return tuple(int(color[index:index + 2], 16) for index in (0, 2, 4))

    def _mix_color(self, start, end, ratio):
        start_rgb = self._hex_to_rgb(start)
        end_rgb = self._hex_to_rgb(end)
        mixed = tuple(
            int(start_channel + (end_channel - start_channel) * ratio)
            for start_channel, end_channel in zip(start_rgb, end_rgb)
        )
        return "#%02x%02x%02x" % mixed

    def _gradient_photo(self, width, height, stops):
        width = max(1, int(width))
        height = max(1, int(height))
        image = Image.new("RGB", (width, height), stops[-1][1])

        for y in range(height):
            position = y / max(height - 1, 1)
            for index, (stop_position, stop_color) in enumerate(stops):
                if position <= stop_position:
                    if index == 0:
                        color = stop_color
                    else:
                        prev_position, prev_color = stops[index - 1]
                        span = max(stop_position - prev_position, 0.0001)
                        ratio = (position - prev_position) / span
                        color = self._mix_color(prev_color, stop_color, ratio)
                    break
            else:
                color = stops[-1][1]

            image.paste(color, (0, y, width, y + 1))

        return ImageTk.PhotoImage(image)

    def _apply_gradient_to_label(self, label, width, height, stops):
        photo = self._gradient_photo(width, height, stops)
        label.configure(image=photo)
        label.image = photo

    def _bind_gradient(self, parent, label, stops):
        def refresh(event):
            self._apply_gradient_to_label(label, event.width, event.height, stops)

        parent.bind("<Configure>", refresh, add="+")

    def _load_badge_photo(self, path, max_size):
        if not path.exists():
            return None
        try:
            with Image.open(path) as image:
                badge = image.convert("RGBA")
                badge.thumbnail(max_size)
                photo = ImageTk.PhotoImage(badge)
                self.ui_photo_refs.append(photo)
                return photo
        except OSError:
            return None

    def _open_external_url(self, url):
        webbrowser.open(url)

    def _make_corner_link(self, parent, text, url, image_path, anchor):
        badge = tk.Frame(parent, bg=WIN_FACE, bd=1, relief="solid", highlightbackground=WIN_EDGE, cursor="hand2")
        badge.place(relx=0.01 if anchor == "sw" else 0.99, rely=0.99, anchor=anchor)

        image = self._load_badge_photo(image_path, (16, 16))
        if image is not None:
            tk.Label(badge, image=image, bg=WIN_FACE, cursor="hand2").grid(
                row=0, column=0, padx=(6, 4), pady=4
            )

        tk.Label(
            badge,
            text=text,
            bg=WIN_FACE,
            fg=WIN_DARK,
            font=FONT_CAPTION,
            cursor="hand2",
        ).grid(row=0, column=1, padx=(0, 8), pady=4)

        for widget in (badge, *badge.winfo_children()):
            widget.bind("<Button-1>", lambda _event, target=url: self._open_external_url(target))

        return badge

    def _set_last_action(self, text):
        self.last_action_var.set(text or self._t("last_empty"))

    def _make_listbox(self, parent, height=8):
        frame = tk.Frame(parent, bg=WIN_FACE)
        frame.grid_columnconfigure(0, weight=1)
        frame.grid_rowconfigure(0, weight=1)
        listbox = tk.Listbox(
            frame,
            height=height,
            bg=WIN_WHITE,
            fg=WIN_BLACK,
            selectbackground=WIN_TAB_ACTIVE,
            selectforeground=WIN_ACCENT_TEXT,
            relief="solid",
            bd=1,
            highlightthickness=1,
            highlightbackground=WIN_EDGE,
            font=FONT_NORMAL,
            activestyle="none",
        )
        scrollbar = tk.Scrollbar(frame, orient="vertical", command=listbox.yview)
        listbox.configure(yscrollcommand=scrollbar.set)
        listbox.grid(row=0, column=0, sticky="nsew")
        scrollbar.grid(row=0, column=1, sticky="ns")
        return listbox, scrollbar, frame

    def _paste_into_var(self, variable):
        try:
            clipboard_text = self.clipboard_get().strip()
        except tk.TclError:
            clipboard_text = ""
        if not clipboard_text:
            messagebox.showinfo(self._app_title(), self._t("clipboard_no_text"))
            return
        urls = self._extract_urls(clipboard_text)
        variable.set(urls[0] if urls else clipboard_text)

    def _refresh_youtube_batch_listbox(self):
        if not hasattr(self, "youtube_batch_listbox"):
            return
        selected = self.youtube_batch_listbox.curselection()
        self.youtube_batch_listbox.delete(0, "end")
        for index, url in enumerate(self.youtube_batch_urls, start=1):
            label = self._t("video_item_label", index=index)
            display = url if len(url) <= 72 else f"{url[:69]}..."
            self.youtube_batch_listbox.insert("end", f"{label}: {display}")
        if selected and selected[0] < self.youtube_batch_listbox.size():
            self.youtube_batch_listbox.selection_set(selected[0])
        self._refresh_youtube_batch_summary()

    def _sync_batch_quality_menu(self):
        if not hasattr(self, "batch_quality_menu"):
            return
        labels = [label for label, _value in self.current_quality_map.items()]
        if not labels:
            labels = [self._t("quality_best")]
        self.batch_quality_menu["menu"].delete(0, "end")
        for label in labels:
            self.batch_quality_menu["menu"].add_command(
                label=label,
                command=tk._setit(self.batch_quality_var, label),
            )
        if self.batch_quality_var.get() not in labels:
            self.batch_quality_var.set(self.quality_var.get() or labels[0])

    def _build_youtube_panel(self, parent):
        frame = tk.Frame(parent, bg=WIN_FACE)
        frame.grid_columnconfigure(0, weight=1)
        frame.grid_rowconfigure(1, weight=1)

        single = tk.Frame(frame, bg=WIN_FACE)
        single.grid(row=0, column=0, sticky="ew", pady=(0, 10))
        single.grid_columnconfigure(0, weight=1)

        url_row = tk.Frame(single, bg=WIN_FACE)
        url_row.grid(row=0, column=0, sticky="ew")
        url_row.grid_columnconfigure(0, weight=1)

        self.url_entry = self._make_entry(url_row, self.url_var)
        self.url_entry.grid(row=0, column=0, sticky="ew")
        self.youtube_paste_button = self._make_button(
            url_row, self._t("paste"), lambda: self._paste_into_var(self.url_var), width=8
        )
        self.youtube_paste_button.grid(row=0, column=1, padx=(6, 0))

        mode_row = tk.Frame(single, bg=WIN_FACE)
        mode_row.grid(row=1, column=0, sticky="ew", pady=(8, 0))

        tk.Label(
            mode_row,
            text=self._t("format_group"),
            bg=WIN_FACE,
            fg=WIN_DARK,
            font=FONT_CAPTION,
        ).grid(row=0, column=0, sticky="w", padx=(0, 8))

        self.video_radio = tk.Radiobutton(
            mode_row,
            text="Video",
            variable=self.mode_var,
            value="Video",
            bg=WIN_FACE,
            fg=WIN_BLACK,
            activebackground=WIN_FACE,
            activeforeground=WIN_BLACK,
            selectcolor=WIN_WHITE,
            command=lambda: self._update_quality_options("Video"),
            font=FONT_NORMAL,
        )
        self.video_radio.grid(row=0, column=1, sticky="w")

        self.audio_radio = tk.Radiobutton(
            mode_row,
            text="Audio",
            variable=self.mode_var,
            value="Audio",
            bg=WIN_FACE,
            fg=WIN_BLACK,
            activebackground=WIN_FACE,
            activeforeground=WIN_BLACK,
            selectcolor=WIN_WHITE,
            command=lambda: self._update_quality_options("Audio"),
            font=FONT_NORMAL,
        )
        self.audio_radio.grid(row=0, column=2, sticky="w", padx=(10, 0))

        tk.Label(
            mode_row,
            text=self._t("quality_group"),
            bg=WIN_FACE,
            fg=WIN_DARK,
            font=FONT_CAPTION,
        ).grid(row=0, column=3, sticky="w", padx=(18, 8))

        self.quality_menu = self._make_option_menu(
            mode_row, self.quality_var, [self._t("quality_best")]
        )
        self.quality_menu.grid(row=0, column=4, sticky="w")

        self.download_button = self._make_button(
            mode_row, self._t("download"), self._start_youtube_download, width=14, primary=True
        )
        self.download_button.grid(row=0, column=5, padx=(18, 0), sticky="e")
        mode_row.grid_columnconfigure(6, weight=1)

        batch = self._make_group(frame, self._t("youtube_batch_group"))
        batch.grid(row=1, column=0, sticky="nsew")
        batch.grid_columnconfigure(0, weight=3)
        batch.grid_columnconfigure(1, weight=1)
        batch.grid_rowconfigure(2, weight=1)

        batch_input = tk.Frame(batch, bg=WIN_FACE)
        batch_input.grid(row=0, column=0, columnspan=2, sticky="ew", padx=8, pady=(8, 4))
        batch_input.grid_columnconfigure(0, weight=1)

        self.batch_url_entry = self._make_entry(batch_input, self.batch_url_var)
        self.batch_url_entry.grid(row=0, column=0, sticky="ew")
        self.youtube_add_button = self._make_button(
            batch_input, self._t("send_batch"), self._add_batch_url_to_youtube_batch, width=10
        )
        self.youtube_add_button.grid(row=0, column=1, padx=(6, 0))

        self.youtube_autopaste_toggle = tk.Checkbutton(
            batch,
            text=self._t("youtube_hotkey_toggle"),
            variable=self.youtube_autopaste_var,
            command=lambda: self._toggle_autopaste("youtube"),
            bg=WIN_FACE,
            fg=WIN_BLACK,
            activebackground=WIN_FACE,
            activeforeground=WIN_BLACK,
            selectcolor=WIN_WHITE,
            anchor="w",
            font=FONT_CAPTION,
        )
        self.youtube_autopaste_toggle.grid(row=1, column=0, columnspan=2, sticky="w", padx=8, pady=(0, 4))

        list_wrap = tk.Frame(batch, bg=WIN_FACE)
        list_wrap.grid(row=2, column=0, sticky="nsew", padx=(8, 4), pady=(0, 8))
        list_wrap.grid_columnconfigure(0, weight=1)
        list_wrap.grid_rowconfigure(0, weight=1)
        self.youtube_batch_listbox, self.youtube_batch_scrollbar, _list_frame = self._make_listbox(
            list_wrap, height=10
        )
        _list_frame.grid(row=0, column=0, sticky="nsew")

        batch_side = tk.Frame(batch, bg=WIN_FACE)
        batch_side.grid(row=2, column=1, sticky="ns", padx=(4, 8), pady=(0, 8))

        tk.Label(
            batch_side,
            text=self._t("batch_format_label"),
            bg=WIN_FACE,
            fg=WIN_DARK,
            font=FONT_CAPTION,
        ).grid(row=0, column=0, sticky="w", pady=(0, 4))
        self.batch_format_menu = self._make_option_menu(
            batch_side, self.batch_format_var, YOUTUBE_BATCH_FORMATS
        )
        self.batch_format_menu.grid(row=1, column=0, sticky="ew", pady=(0, 10))

        tk.Label(
            batch_side,
            text=self._t("quality_group"),
            bg=WIN_FACE,
            fg=WIN_DARK,
            font=FONT_CAPTION,
        ).grid(row=2, column=0, sticky="w", pady=(0, 4))
        self.batch_quality_menu = self._make_option_menu(
            batch_side, self.batch_quality_var, [self._t("quality_best")]
        )
        self.batch_quality_menu.grid(row=3, column=0, sticky="ew")

        youtube_batch_actions = tk.Frame(batch, bg=WIN_FACE)
        youtube_batch_actions.grid(row=3, column=0, columnspan=2, sticky="ew", padx=8, pady=(0, 8))
        youtube_batch_actions.grid_columnconfigure(0, weight=1)

        folder_row = tk.Frame(batch, bg=WIN_FACE)
        folder_row.grid(row=4, column=0, columnspan=2, sticky="ew", padx=8, pady=(0, 8))
        folder_row.grid_columnconfigure(1, weight=1)

        tk.Label(
            folder_row,
            text=self._t("folder_prefix"),
            bg=WIN_FACE,
            fg=WIN_DARK,
            font=FONT_CAPTION,
        ).grid(row=0, column=0, sticky="w", padx=(0, 8))
        self.folder_entry = self._make_entry(folder_row, self.output_var)
        self.folder_entry.grid(row=0, column=1, sticky="ew")
        self.browse_button = self._make_button(
            folder_row, self._t("change_folder"), lambda: self._pick_folder("youtube"), width=12
        )
        self.browse_button.grid(row=0, column=2, padx=(6, 0))
        self.youtube_open_folder_button = self._make_button(
            folder_row, self._t("open_folder"), self._open_output_folder, width=12
        )
        self.youtube_open_folder_button.grid(row=0, column=3, padx=(6, 0))

        self.youtube_load_file_button = self._make_button(
            youtube_batch_actions, self._t("load_txt"), self._load_youtube_links_from_file, width=12
        )
        self.youtube_load_file_button.grid(row=0, column=1, padx=(6, 0))
        self.youtube_clear_button = self._make_button(
            youtube_batch_actions, self._t("clear_batch"), self._clear_youtube_batch, width=12
        )
        self.youtube_clear_button.grid(row=0, column=2, padx=(6, 0))
        self.youtube_batch_download_button = self._make_button(
            youtube_batch_actions,
            self._t("download_batch"),
            self._start_youtube_batch_download,
            width=16,
            primary=True,
        )
        self.youtube_batch_download_button.grid(row=0, column=3, padx=(6, 0))

        self._sync_batch_quality_menu()
        self._refresh_youtube_batch_listbox()
        return frame

    def _image_format_menu_values(self):
        return [
            (self._t("format_auto"), "auto"),
            ("PNG", "PNG"),
            ("JPEG", "JPEG"),
            ("WEBP", "WEBP"),
        ]

    def _image_quality_menu_values(self):
        return [
            (self._t("quality_baja"), "baja"),
            (self._t("quality_media"), "media"),
            (self._t("quality_alta"), "alta"),
        ]

    def _create_query_item(self, query):
        item_id = self.next_item_id
        self.next_item_id += 1
        return {
            "id": item_id,
            "kind": "query",
            "title": query,
            "query": query,
            "download_url": None,
            "filename_hint": sanitize_filename(query) or f"query_{item_id}",
            "preview_image": None,
            "image_data": None,
        }

    def _refresh_image_listbox(self):
        if not hasattr(self, "image_listbox"):
            return
        selected = self.image_listbox.curselection()
        self.image_listbox.delete(0, "end")
        for index, item in enumerate(self.image_items, start=1):
            label = self._t("photo_item_label", index=index)
            title = item.get("title") or item.get("query") or f"Item {index}"
            display = title if len(title) <= 48 else f"{title[:45]}..."
            self.image_listbox.insert("end", f"{label}: {display}")
        if selected and selected[0] < self.image_listbox.size():
            self.image_listbox.selection_set(selected[0])
            self._on_image_list_select()
        elif self.image_items:
            self.image_listbox.selection_set(0)
            self._on_image_list_select()
        else:
            self.selected_image_index = None
            self._update_image_preview_panel(None)
        self._refresh_batch_summary()

    def _on_image_list_select(self, _event=None):
        if not hasattr(self, "image_listbox"):
            return
        selection = self.image_listbox.curselection()
        if not selection:
            self.selected_image_index = None
            self._update_image_preview_panel(None)
            return
        index = selection[0]
        if index >= len(self.image_items):
            return
        self.selected_image_index = index
        item = self.image_items[index]
        self._update_image_preview_panel(item)
        if item.get("preview_image") is None and item.get("download_url"):
            threading.Thread(
                target=self._load_preview_for_item,
                args=(item["id"], item["download_url"]),
                daemon=True,
            ).start()

    def _load_preview_for_item(self, item_id, url):
        try:
            preview = self._load_preview_from_url(url)
            self.worker_queue.put(("preview_loaded", (item_id, preview)))
        except Exception as error:
            self.worker_queue.put(("log", f"No se pudo cargar preview: {error}"))

    def _update_image_preview_panel(self, item):
        if not hasattr(self, "image_preview_label"):
            return
        if item is None:
            self.image_preview_label.configure(image="", text=self._t("preview_label"))
            self.image_preview_photo = None
            if hasattr(self, "image_replace_button"):
                self.image_replace_button.configure(state="disabled")
            return
        preview = item.get("preview_image")
        if preview is None and item.get("image_data") is not None:
            preview = item["image_data"]
        if preview is None:
            self.image_preview_label.configure(image="", text=item.get("title", self._t("preview_label")))
            self.image_preview_photo = None
            return
        thumb = preview.copy()
        thumb.thumbnail((280, 220))
        photo = ImageTk.PhotoImage(thumb)
        self.image_preview_photo = photo
        self.ui_photo_refs.append(photo)
        self.image_preview_label.configure(image=photo, text="")
        if hasattr(self, "image_replace_button"):
            can_replace = item.get("kind") in ("pexels", "flickr")
            self.image_replace_button.configure(state="normal" if can_replace else "disabled")

    def _build_images_panel(self, parent):
        frame = tk.Frame(parent, bg=WIN_FACE)
        frame.grid_columnconfigure(0, weight=2)
        frame.grid_columnconfigure(1, weight=1)
        frame.grid_rowconfigure(1, weight=1)

        toolbar = tk.Frame(frame, bg=WIN_FACE)
        toolbar.grid(row=0, column=0, columnspan=2, sticky="ew", pady=(0, 8))
        toolbar.grid_columnconfigure(0, weight=1)

        fill_row = tk.Frame(toolbar, bg=WIN_FACE)
        fill_row.grid(row=0, column=0, columnspan=2, sticky="ew")
        fill_row.grid_columnconfigure(0, weight=1)
        tk.Label(
            fill_row,
            text=self._t("image_link_label"),
            bg=WIN_FACE,
            fg=WIN_DARK,
            font=FONT_CAPTION,
        ).grid(row=0, column=0, columnspan=2, sticky="w", pady=(0, 4))
        self.list_entry = self._make_entry(fill_row, self.list_entry_var)
        self.list_entry.grid(row=1, column=0, sticky="ew")
        self.add_list_item_button = self._make_button(
            fill_row, self._t("add"), self._add_list_entry, width=10
        )
        self.add_list_item_button.grid(row=1, column=1, padx=(6, 0))

        actions = tk.Frame(toolbar, bg=WIN_FACE)
        actions.grid(row=1, column=0, columnspan=2, sticky="ew", pady=(8, 0))
        actions.grid_columnconfigure(4, weight=1)

        self.images_autopaste_toggle = tk.Checkbutton(
            actions,
            text=self._t("youtube_hotkey_toggle"),
            variable=self.images_autopaste_var,
            command=lambda: self._toggle_autopaste("imagenes"),
            bg=WIN_FACE,
            fg=WIN_BLACK,
            activebackground=WIN_FACE,
            activeforeground=WIN_BLACK,
            selectcolor=WIN_WHITE,
            font=FONT_CAPTION,
        )
        self.images_autopaste_toggle.grid(row=0, column=0, sticky="w")

        self.clear_list_button = self._make_button(
            actions, self._t("clear_list"), self._clear_image_items, width=10
        )
        self.clear_list_button.grid(row=0, column=1, padx=(8, 0))
        self.load_query_file_button = self._make_button(
            actions, self._t("load_txt"), self._load_queries_from_file, width=12
        )
        self.load_query_file_button.grid(row=0, column=2, padx=(6, 0))
        self.search_queries_button = self._make_button(
            actions, self._t("search_images"), self._start_query_search, width=14, primary=True
        )
        self.search_queries_button.grid(row=0, column=3, padx=(6, 0))
        self.paste_now_button = self._make_button(
            actions, self._t("paste_now"), self._paste_clipboard_content, width=12
        )
        self.paste_now_button.grid(row=0, column=4, padx=(6, 0), sticky="e")

        source_row = tk.Frame(toolbar, bg=WIN_FACE)
        source_row.grid(row=2, column=0, columnspan=2, sticky="w", pady=(8, 0))
        tk.Label(
            source_row,
            text=self._t("source_label"),
            bg=WIN_FACE,
            fg=WIN_DARK,
            font=FONT_CAPTION,
        ).grid(row=0, column=0, sticky="w", padx=(0, 8))
        self.search_source_menu = self._make_option_menu(
            source_row,
            self.search_source_var,
            SEARCH_SOURCES,
            command=self._on_search_source_change,
        )
        self.search_source_menu.grid(row=0, column=1, sticky="w")

        main = tk.Frame(frame, bg=WIN_FACE)
        main.grid(row=1, column=0, columnspan=2, sticky="nsew")
        main.grid_columnconfigure(0, weight=3)
        main.grid_columnconfigure(1, weight=2)
        main.grid_rowconfigure(0, weight=1)

        list_group = self._make_group(main, self._t("search_group"))
        list_group.grid(row=0, column=0, sticky="nsew", padx=(0, 8))
        list_group.grid_columnconfigure(0, weight=1)
        list_group.grid_rowconfigure(0, weight=1)
        list_wrap = tk.Frame(list_group, bg=WIN_FACE)
        list_wrap.grid(row=0, column=0, sticky="nsew", padx=8, pady=8)
        list_wrap.grid_columnconfigure(0, weight=1)
        list_wrap.grid_rowconfigure(0, weight=1)
        self.image_listbox, self.image_list_scrollbar, _img_list_frame = self._make_listbox(
            list_wrap, height=14
        )
        _img_list_frame.grid(row=0, column=0, sticky="nsew")
        self.image_listbox.bind("<<ListboxSelect>>", self._on_image_list_select)

        preview_group = self._make_group(main, self._t("preview_label"))
        preview_group.grid(row=0, column=1, sticky="nsew")
        preview_group.grid_columnconfigure(0, weight=1)

        self.image_preview_label = tk.Label(
            preview_group,
            text=self._t("preview_label"),
            bg=WIN_LIGHT,
            fg=WIN_DARK,
            relief="solid",
            bd=1,
            highlightbackground=WIN_EDGE,
            width=36,
            height=12,
            anchor="center",
        )
        self.image_preview_label.grid(row=0, column=0, sticky="nsew", padx=8, pady=(8, 4))

        preview_opts = tk.Frame(preview_group, bg=WIN_FACE)
        preview_opts.grid(row=1, column=0, sticky="ew", padx=8, pady=(0, 4))
        tk.Label(
            preview_opts,
            text=self._t("format_group"),
            bg=WIN_FACE,
            fg=WIN_DARK,
            font=FONT_CAPTION,
        ).grid(row=0, column=0, sticky="w", pady=(0, 4))
        format_labels = [label for label, _value in self._image_format_menu_values()]
        self.image_format_menu = self._make_option_menu(
            preview_opts,
            self.image_format_var,
            format_labels,
            command=self._on_image_export_setting_change,
        )
        self.image_format_menu.grid(row=1, column=0, sticky="ew")

        tk.Label(
            preview_opts,
            text=self._t("quality_group"),
            bg=WIN_FACE,
            fg=WIN_DARK,
            font=FONT_CAPTION,
        ).grid(row=2, column=0, sticky="w", pady=(8, 4))
        quality_labels = [label for label, _value in self._image_quality_menu_values()]
        self.image_quality_menu = self._make_option_menu(
            preview_opts,
            self.image_quality_var,
            quality_labels,
            command=self._on_image_export_setting_change,
        )
        self.image_quality_menu.grid(row=3, column=0, sticky="ew", pady=(0, 4))

        preview_actions = tk.Frame(preview_group, bg=WIN_FACE)
        preview_actions.grid(row=2, column=0, sticky="ew", padx=8, pady=(0, 8))
        self.image_remove_button = self._make_button(
            preview_actions,
            self._t("remove_button"),
            self._remove_selected_image_item,
            width=10,
        )
        self.image_remove_button.grid(row=0, column=0, sticky="w")
        self.image_replace_button = self._make_button(
            preview_actions,
            self._t("replace_button"),
            self._replace_selected_image_item,
            width=10,
        )
        self.image_replace_button.grid(row=0, column=1, padx=(6, 0), sticky="w")

        footer = tk.Frame(frame, bg=WIN_FACE)
        footer.grid(row=2, column=0, columnspan=2, sticky="ew", pady=(10, 0))
        footer.grid_columnconfigure(1, weight=1)

        tk.Label(
            footer,
            text=self._t("folder_prefix"),
            bg=WIN_FACE,
            fg=WIN_DARK,
            font=FONT_CAPTION,
        ).grid(row=0, column=0, sticky="w", padx=(0, 8))
        self.image_folder_entry = self._make_entry(footer, self.image_output_var)
        self.image_folder_entry.grid(row=0, column=1, sticky="ew")
        self.image_browse_button = self._make_button(
            footer, self._t("change_folder"), lambda: self._pick_folder("imagenes"), width=12
        )
        self.image_browse_button.grid(row=0, column=2, padx=(6, 0))
        self.image_open_folder_button = self._make_button(
            footer, self._t("open_folder"), self._open_output_folder, width=12
        )
        self.image_open_folder_button.grid(row=0, column=3, padx=(6, 0))
        self.image_download_button = self._make_button(
            footer,
            self._t("download_batch"),
            self._start_image_download,
            width=16,
            primary=True,
        )
        self.image_download_button.grid(row=0, column=4, padx=(6, 0))

        self._sync_image_export_menus()
        self._refresh_image_listbox()
        self._apply_search_source_state()
        return frame

    def _sync_image_export_menus(self):
        format_map = {label: value for label, value in self._image_format_menu_values()}
        quality_map = {label: value for label, value in self._image_quality_menu_values()}
        current_format = self.image_format_var.get()
        current_quality = self.image_quality_var.get()
        if current_format not in IMAGE_EXPORT_FORMATS:
            for label, value in format_map.items():
                if value == current_format:
                    self.image_format_var.set(label)
                    break
        if current_quality not in IMAGE_QUALITY_LEVELS:
            for label, value in quality_map.items():
                if value == current_quality:
                    self.image_quality_var.set(label)
                    break

    def _on_image_export_setting_change(self, _value=None):
        format_map = {label: value for label, value in self._image_format_menu_values()}
        quality_map = {label: value for label, value in self._image_quality_menu_values()}
        selected_format = format_map.get(self.image_format_var.get(), "auto")
        selected_quality = quality_map.get(self.image_quality_var.get(), "media")
        self._set_setting("image_export_format", selected_format)
        self._set_setting("image_export_quality", selected_quality)

    def _selected_image_export_format(self):
        format_map = {label: value for label, value in self._image_format_menu_values()}
        return format_map.get(self.image_format_var.get(), "auto")

    def _selected_image_export_quality(self):
        quality_map = {label: value for label, value in self._image_quality_menu_values()}
        return quality_map.get(self.image_quality_var.get(), "media")

    def _remove_selected_image_item(self):
        if self.selected_image_index is None:
            return
        self._remove_batch_item(self.image_items[self.selected_image_index]["id"])

    def _replace_selected_image_item(self):
        if self.selected_image_index is None:
            return
        self._start_replace_item(self.image_items[self.selected_image_index]["id"])

    def _open_help_file(self):
        if not HELP_FILE.exists():
            messagebox.showerror(
                self._app_title(),
                self._t("missing_help_file", name=HELP_FILE.name),
            )
            return
        os.startfile(str(HELP_FILE))

    def _load_settings(self):
        if not SETTINGS_FILE.exists():
            return {}

        try:
            return json.loads(SETTINGS_FILE.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            return {}

    def _write_settings(self):
        SETTINGS_FILE.write_text(
            json.dumps(self.settings, indent=2, ensure_ascii=True),
            encoding="utf-8",
        )

    def _normalize_hotkey(self, value):
        hotkey = str(value or "").strip().lower()
        return re.sub(r"\s+", "", hotkey)

    def _format_hotkey_label(self, hotkey):
        normalized = self._normalize_hotkey(hotkey)
        return normalized.upper() if normalized else self._t("hotkey_status_disabled").split(": ", 1)[-1]

    def _foreground_window_handle(self):
        if os.name != "nt":
            return None
        return user32.GetForegroundWindow()

    def _our_window_handles(self):
        handles = set()
        try:
            handles.add(self.winfo_id())
        except tk.TclError:
            pass
        if self.settings_window is not None and self.settings_window.winfo_exists():
            try:
                handles.add(self.settings_window.winfo_id())
            except tk.TclError:
                pass
        return handles

    def _our_window_is_foreground(self):
        hwnd = self._foreground_window_handle()
        return hwnd in self._our_window_handles() if hwnd else False

    def _app_text_widget_has_focus(self):
        if not self._our_window_is_foreground():
            return False
        focused = self.focus_get()
        return focused in (
            self.url_entry,
            self.batch_url_entry,
            self.folder_entry,
            self.image_folder_entry,
            self.list_entry,
            getattr(self, "settings_key_entry", None),
            getattr(self, "settings_hotkey_entry", None),
        )

    def _foreground_focus_class_name(self):
        if os.name != "nt":
            return ""
        hwnd = self._foreground_window_handle()
        if not hwnd:
            return ""

        info = self._foreground_gui_thread_info(hwnd)
        if info is None:
            return ""

        target_hwnd = info.hwndFocus or hwnd
        buffer = ctypes.create_unicode_buffer(256)
        if user32.GetClassNameW(target_hwnd, buffer, 255):
            return buffer.value
        return ""

    def _foreground_gui_thread_info(self, hwnd=None):
        if os.name != "nt":
            return None
        hwnd = hwnd or self._foreground_window_handle()
        if not hwnd:
            return None

        process_id = wintypes.DWORD()
        thread_id = user32.GetWindowThreadProcessId(hwnd, ctypes.byref(process_id))
        info = GUITHREADINFO(cbSize=ctypes.sizeof(GUITHREADINFO))
        if not user32.GetGUIThreadInfo(thread_id, ctypes.byref(info)):
            return None
        return info

    def _external_text_input_active(self):
        if os.name != "nt" or self._our_window_is_foreground():
            return False
        if self._uia_external_text_input_active():
            return True
        info = self._foreground_gui_thread_info()
        class_name = self._foreground_focus_class_name().lower()
        has_caret = bool(info and info.hwndCaret)
        if has_caret:
            return True
        if not class_name:
            return False
        return (
            class_name in {"edit", "richedit20w", "richedit50w", "scintilla"}
            or "edit" in class_name
            or "omnibox" in class_name
            or "textbox" in class_name
        )

    def _uia_external_text_input_active(self):
        if os.name != "nt" or ui_auto is None or self._our_window_is_foreground():
            return False

        try:
            control = ui_auto.GetFocusedControl()
        except Exception:
            return False

        if not control:
            return False

        control_type = str(getattr(control, "ControlTypeName", "") or "").lower()
        class_name = str(getattr(control, "ClassName", "") or "").lower()
        localized_type = str(getattr(control, "LocalizedControlType", "") or "").lower()

        if control_type in {"editcontrol", "documentcontrol"}:
            return True

        if "edit" in class_name:
            return True

        if any(token in localized_type for token in ("edit", "editar", "document", "documento")):
            return True

        try:
            if control.GetValuePattern() and control_type not in {
                "slidercontrol",
                "progressbarcontrol",
                "spinnercontrol",
            }:
                return True
        except Exception:
            pass

        try:
            if control.GetTextPattern() and control_type == "documentcontrol":
                return True
        except Exception:
            pass

        return False

    def _hotkey_capture_allowed(self):
        if self._app_text_widget_has_focus():
            return False
        if self._external_text_input_active():
            return False
        return True

    def _toggle_autopaste(self, section):
        setting_key = (
            "youtube_autopaste_enabled" if section == "youtube" else "images_autopaste_enabled"
        )
        section_label = self._t("tab_youtube") if section == "youtube" else self._t("tab_images")
        enabled = (
            bool(self.youtube_autopaste_var.get())
            if section == "youtube"
            else bool(self.images_autopaste_var.get())
        )
        self._set_setting(setting_key, enabled)

        if not self._is_busy():
            if enabled:
                self.detail_var.set(self._t("autopaste_enabled_detail", section=section_label))
            else:
                self.detail_var.set(self._t("autopaste_disabled_detail", section=section_label))

    def _unregister_capture_hotkey(self):
        if keyboard is None or self.capture_hotkey_handle is None:
            self.capture_hotkey_handle = None
            self.capture_hotkey_kind = None
            return
        try:
            if self.capture_hotkey_kind == "key":
                keyboard.unhook(self.capture_hotkey_handle)
            else:
                keyboard.remove_hotkey(self.capture_hotkey_handle)
        except Exception:
            pass
        self.capture_hotkey_handle = None
        self.capture_hotkey_kind = None

    def _single_letter_hotkey(self, hotkey):
        normalized = self._normalize_hotkey(hotkey)
        return len(normalized) == 1 and normalized.isalpha()

    def _update_capture_hotkey_state(self):
        if keyboard is None:
            status_text = self._t("hotkey_status_unavailable")
        else:
            hotkey = self._normalize_hotkey(self.capture_hotkey_var.get())
            if hotkey:
                status_text = self._t("hotkey_status_format", hotkey=self._format_hotkey_label(hotkey))
            else:
                status_text = self._t("hotkey_status_disabled")
        self.capture_status_var.set(status_text)

        if getattr(self, "settings_hotkey_info_label", None) is not None:
            if keyboard is None:
                info = self._t("hotkey_info_missing_keyboard")
            else:
                info = self._t("hotkey_info_help")
            self.settings_hotkey_info_label.configure(text=info)

        state = "disabled" if self._is_busy() or keyboard is None else "normal"
        for widget in (
            getattr(self, "settings_hotkey_entry", None),
            getattr(self, "settings_hotkey_save_button", None),
            getattr(self, "settings_hotkey_clear_button", None),
        ):
            if widget is not None:
                widget.configure(state=state)

    def _queue_capture_hotkey(self):
        if not self.is_closing:
            self.worker_queue.put(("hotkey_capture", self.capture_hotkey_var.get()))

    def _apply_capture_hotkey(self, startup=False):
        hotkey = self._normalize_hotkey(self.capture_hotkey_var.get())
        self.capture_hotkey_var.set(hotkey)
        self._unregister_capture_hotkey()

        if keyboard is None:
            self._update_capture_hotkey_state()
            if not startup:
                messagebox.showwarning(
                    self._app_title(),
                    self._t("hotkey_dependency_warning"),
                )
            return False

        if not hotkey:
            self._remove_setting("capture_hotkey")
            self._update_capture_hotkey_state()
            return True

        try:
            if "+" not in hotkey and "," not in hotkey:
                self.capture_hotkey_handle = keyboard.on_release_key(
                    hotkey,
                    lambda _event: self._queue_capture_hotkey(),
                    suppress=False,
                )
                self.capture_hotkey_kind = "key"
            else:
                self.capture_hotkey_handle = keyboard.add_hotkey(
                    hotkey,
                    self._queue_capture_hotkey,
                    suppress=False,
                    trigger_on_release=True,
                )
                self.capture_hotkey_kind = "hotkey"
        except Exception as error:
            self.capture_hotkey_handle = None
            self.capture_hotkey_kind = None
            self._update_capture_hotkey_state()
            if not startup:
                messagebox.showerror(self._app_title(), self._t("hotkey_register_error", error=error))
            self._log(self._t("hotkey_register_error", error=error))
            return False

        self._set_setting("capture_hotkey", hotkey)
        self._log(self._t("hotkey_registered_log", hotkey=hotkey))
        self._update_capture_hotkey_state()
        return True

    def _save_capture_hotkey(self):
        hotkey = self._normalize_hotkey(self.capture_hotkey_var.get())
        if not hotkey:
            messagebox.showwarning(self._app_title(), self._t("hotkey_save_empty"))
            return

        self.capture_hotkey_var.set(hotkey)
        if not self._apply_capture_hotkey():
            return

        self.status_var.set(self._t("hotkey_saved_status"))
        self.detail_var.set(
            self._t("hotkey_saved_detail", hotkey=self._format_hotkey_label(hotkey))
        )
        self._log(self._t("hotkey_configured_log", hotkey=hotkey))

    def _clear_capture_hotkey(self):
        self.capture_hotkey_var.set("")
        self._unregister_capture_hotkey()
        self._remove_setting("capture_hotkey")
        self._update_capture_hotkey_state()
        self.status_var.set(self._t("hotkey_disabled_status"))
        self.detail_var.set(self._t("hotkey_disabled_detail"))
        self._log(self._t("hotkey_disabled_log"))

    def _save_pexels_key(self):
        key = self.pexels_key_var.get().strip()
        if not key:
            messagebox.showwarning(self._app_title(), self._t("pexels_key_empty"))
            return

        self._set_setting("pexels_api_key", key)
        self.status_var.set(self._t("key_saved_status"))
        self.detail_var.set(self._t("key_saved_detail", name=SETTINGS_FILE.name))
        self._log(self._t("key_saved_log"))
        self._apply_search_source_state()

    def _clear_pexels_key(self):
        self.pexels_key_var.set("")
        self._remove_setting("pexels_api_key")
        self.status_var.set(self._t("key_cleared_status"))
        self.detail_var.set(self._t("key_cleared_detail"))
        self._log(self._t("key_cleared_log"))
        self._apply_search_source_state()

    def _change_theme(self):
        if self._is_busy():
            messagebox.showinfo(self._app_title(), self._t("operation_busy"))
            self.theme_var.set(self._setting("ui_theme", DEFAULT_THEME))
            return

        selected_theme = self.theme_var.get()
        self._set_setting("ui_theme", selected_theme)
        self._apply_theme_palette(selected_theme)
        self._rebuild_ui()
        self.status_var.set(self._t("theme_changed_status"))
        self._log(self._t("theme_changed_log", theme=self._theme_label(selected_theme)))

    def _change_language(self):
        if self._is_busy():
            messagebox.showinfo(self._app_title(), self._t("operation_busy"))
            self.language_var.set(self._setting("ui_language", DEFAULT_LANGUAGE))
            return

        selected_language = self.language_var.get()
        self._set_setting("ui_language", selected_language)
        self.title(self._app_title())
        self._rebuild_ui()
        self.status_var.set(self._t("language_changed_status"))
        self._log(
            self._t("language_changed_log", language=self._language_label(selected_language))
        )

    def _open_search_settings(self):
        if self.settings_window is not None and self.settings_window.winfo_exists():
            self.settings_window.deiconify()
            self.settings_window.lift()
            self.settings_window.focus_force()
            return

        window = tk.Toplevel(self)
        window.title(self._t("settings_title"))
        window.geometry("500x390")
        window.resizable(False, False)
        window.transient(self)
        window.configure(bg=WIN_FACE)
        window.protocol("WM_DELETE_WINDOW", self._close_search_settings)

        group = self._make_group(window, self._t("settings_group"))
        group.pack(fill="both", expand=True, padx=10, pady=10)
        group.grid_columnconfigure(0, weight=1)

        appearance_group = self._make_group(group, self._t("appearance_group"))
        appearance_group.grid(row=0, column=0, columnspan=3, sticky="ew", padx=8, pady=(8, 6))
        appearance_group.grid_columnconfigure(1, weight=1)

        tk.Label(
            appearance_group,
            text=self._t("theme_label"),
            bg=WIN_FACE,
            fg=WIN_BLACK,
            font=FONT_BOLD,
        ).grid(row=0, column=0, sticky="w", padx=8, pady=(8, 4))

        theme_row = tk.Frame(appearance_group, bg=WIN_FACE)
        theme_row.grid(row=0, column=1, sticky="w", padx=8, pady=(8, 4))
        tk.Radiobutton(
            theme_row,
            text=self._t("theme_dark"),
            variable=self.theme_var,
            value="dark",
            command=self._change_theme,
            bg=WIN_FACE,
            fg=WIN_BLACK,
            activebackground=WIN_FACE,
            activeforeground=WIN_BLACK,
            selectcolor=WIN_WHITE,
            font=FONT_NORMAL,
        ).grid(row=0, column=0, sticky="w")
        tk.Radiobutton(
            theme_row,
            text=self._t("theme_light"),
            variable=self.theme_var,
            value="light",
            command=self._change_theme,
            bg=WIN_FACE,
            fg=WIN_BLACK,
            activebackground=WIN_FACE,
            activeforeground=WIN_BLACK,
            selectcolor=WIN_WHITE,
            font=FONT_NORMAL,
        ).grid(row=0, column=1, sticky="w", padx=(10, 0))

        tk.Label(
            appearance_group,
            text=self._t("language_label"),
            bg=WIN_FACE,
            fg=WIN_BLACK,
            font=FONT_BOLD,
        ).grid(row=1, column=0, sticky="w", padx=8, pady=(0, 8))

        language_row = tk.Frame(appearance_group, bg=WIN_FACE)
        language_row.grid(row=1, column=1, sticky="w", padx=8, pady=(0, 8))
        tk.Radiobutton(
            language_row,
            text=self._t("language_es"),
            variable=self.language_var,
            value="es",
            command=self._change_language,
            bg=WIN_FACE,
            fg=WIN_BLACK,
            activebackground=WIN_FACE,
            activeforeground=WIN_BLACK,
            selectcolor=WIN_WHITE,
            font=FONT_NORMAL,
        ).grid(row=0, column=0, sticky="w")
        tk.Radiobutton(
            language_row,
            text=self._t("language_en"),
            variable=self.language_var,
            value="en",
            command=self._change_language,
            bg=WIN_FACE,
            fg=WIN_BLACK,
            activebackground=WIN_FACE,
            activeforeground=WIN_BLACK,
            selectcolor=WIN_WHITE,
            font=FONT_NORMAL,
        ).grid(row=0, column=1, sticky="w", padx=(10, 0))

        self.settings_info_label = tk.Label(
            group,
            text=self._t("search_settings_info_default"),
            bg=WIN_LIGHT,
            fg=WIN_BLACK,
            justify="left",
            anchor="w",
            relief="solid",
            bd=1,
            highlightbackground=WIN_EDGE,
            font=FONT_SMALL,
            padx=8,
            pady=8,
        )
        self.settings_info_label.grid(row=1, column=0, columnspan=3, sticky="ew", padx=8, pady=(0, 6))

        tk.Label(
            group,
            text=self._t("pexels_api_label"),
            bg=WIN_FACE,
            fg=WIN_BLACK,
            font=FONT_BOLD,
        ).grid(row=2, column=0, columnspan=3, sticky="w", padx=8, pady=(0, 2))

        key_row = tk.Frame(group, bg=WIN_FACE)
        key_row.grid(row=3, column=0, columnspan=3, sticky="ew", padx=8, pady=(0, 8))
        key_row.grid_columnconfigure(0, weight=1)

        self.settings_key_entry = self._make_entry(key_row, self.pexels_key_var)
        self.settings_key_entry.grid(row=0, column=0, sticky="ew")
        self.settings_save_button = self._make_button(
            key_row, self._t("save"), self._save_pexels_key, width=10
        )
        self.settings_save_button.grid(row=0, column=1, padx=(6, 0))
        self.settings_clear_button = self._make_button(
            key_row, self._t("clear"), self._clear_pexels_key, width=10
        )
        self.settings_clear_button.grid(row=0, column=2, padx=(6, 0))

        self.settings_hotkey_info_label = tk.Label(
            group,
            text="",
            bg=WIN_LIGHT,
            fg=WIN_BLACK,
            justify="left",
            anchor="w",
            relief="solid",
            bd=1,
            highlightbackground=WIN_EDGE,
            font=FONT_SMALL,
            padx=8,
            pady=8,
        )
        self.settings_hotkey_info_label.grid(
            row=4, column=0, columnspan=3, sticky="ew", padx=8, pady=(0, 6)
        )

        tk.Label(
            group,
            text=self._t("hotkey_label"),
            bg=WIN_FACE,
            fg=WIN_BLACK,
            font=FONT_BOLD,
        ).grid(row=5, column=0, columnspan=3, sticky="w", padx=8, pady=(0, 2))

        hotkey_row = tk.Frame(group, bg=WIN_FACE)
        hotkey_row.grid(row=6, column=0, columnspan=3, sticky="ew", padx=8, pady=(0, 8))
        hotkey_row.grid_columnconfigure(0, weight=1)

        self.settings_hotkey_entry = self._make_entry(hotkey_row, self.capture_hotkey_var)
        self.settings_hotkey_entry.grid(row=0, column=0, sticky="ew")
        self.settings_hotkey_save_button = self._make_button(
            hotkey_row, self._t("save"), self._save_capture_hotkey, width=10
        )
        self.settings_hotkey_save_button.grid(row=0, column=1, padx=(6, 0))
        self.settings_hotkey_clear_button = self._make_button(
            hotkey_row, self._t("clear"), self._clear_capture_hotkey, width=10
        )
        self.settings_hotkey_clear_button.grid(row=0, column=2, padx=(6, 0))

        self.settings_window = window
        self._apply_search_source_state()

    def _close_search_settings(self):
        if self.settings_window is not None and self.settings_window.winfo_exists():
            self.settings_window.destroy()
        self.settings_window = None
        self.settings_info_label = None
        self.settings_key_entry = None
        self.settings_save_button = None
        self.settings_clear_button = None
        self.settings_hotkey_info_label = None
        self.settings_hotkey_entry = None
        self.settings_hotkey_save_button = None
        self.settings_hotkey_clear_button = None

    def _on_search_source_change(self, source):
        self._set_setting("image_search_source", source)
        self._apply_search_source_state()
        if not self._is_busy():
            if source == "Pexels":
                self.detail_var.set(self._t("search_source_detail_pexels"))
            else:
                self.detail_var.set(self._t("search_source_detail_flickr"))

    def _apply_search_source_state(self):
        if getattr(self, "settings_info_label", None) is not None:
            if self.search_source_var.get() == "Pexels":
                self.settings_info_label.configure(text=self._t("search_source_info_pexels"))
            else:
                self.settings_info_label.configure(text=self._t("search_source_info_flickr"))

        state = "normal" if self.search_source_var.get() == "Pexels" and not self._is_busy() else "disabled"
        for widget in (
            getattr(self, "settings_key_entry", None),
            getattr(self, "settings_save_button", None),
            getattr(self, "settings_clear_button", None),
        ):
            if widget is not None:
                widget.configure(state=state)
        self._update_capture_hotkey_state()

    def _quality_options_for_mode(self, mode):
        options = VIDEO_QUALITY_KEYS if mode == "Video" else AUDIO_QUALITY_KEYS
        return [(self._t(label_key), value) for label_key, value in options]

    def _set_tab_button_state(self):
        selected = self.section_var.get()
        for button, section in (
            (self.youtube_tab_button, "youtube"),
            (self.images_tab_button, "imagenes"),
        ):
            is_active = selected == section
            button.configure(
                bg=WIN_TAB_ACTIVE if is_active else WIN_TAB_IDLE,
                fg=WIN_ACCENT_TEXT if is_active else WIN_BLACK,
                activebackground=WIN_TAB_ACTIVE if is_active else WIN_BUTTON_ACTIVE,
                activeforeground=WIN_ACCENT_TEXT if is_active else WIN_BLACK,
            )

    def _set_section(self, section):
        self.section_var.set(section)
        self._set_tab_button_state()

        if section == "youtube":
            self.youtube_frame.grid()
            self.images_frame.grid_remove()
            if not self._is_busy():
                self.status_var.set(self._t("ready"))
                self.detail_var.set(self._t("section_ready_youtube"))
        else:
            self.images_frame.grid()
            self.youtube_frame.grid_remove()
            if not self._is_busy():
                self.status_var.set(self._t("ready"))
                self.detail_var.set(self._t("section_ready_images"))
        if section == "youtube":
            self._refresh_youtube_batch_summary()
        else:
            self._refresh_batch_summary()

    def _update_quality_options(self, mode):
        options = self._quality_options_for_mode(mode)
        labels = [label for label, _value in options]
        self.current_quality_map = {label: value for label, value in options}
        current = self.quality_var.get()

        self.quality_menu["menu"].delete(0, "end")
        for label in labels:
            self.quality_menu["menu"].add_command(
                label=label,
                command=tk._setit(self.quality_var, label),
            )

        if current not in labels:
            self.quality_var.set(labels[0])

        if current not in labels:
            self.quality_var.set(labels[0])
        self._sync_batch_quality_menu()

    def _batch_quality_value(self):
        label = self.batch_quality_var.get() or self.quality_var.get()
        return self.current_quality_map.get(label, self._selected_quality_value())

    def _pick_folder(self, target):
        current = self.output_var.get() if target == "youtube" else self.image_output_var.get()
        selected = filedialog.askdirectory(initialdir=current or str(DEFAULT_FISSILEKIT_ROOT))
        if not selected:
            return

        if target == "youtube":
            self.output_var.set(selected)
            self._set_setting("video_output_folder", selected)
        else:
            self.image_output_var.set(selected)
            self._set_setting("image_output_folder", selected)

    def _append_youtube_batch_urls(self, text):
        added = 0
        for line in text.splitlines():
            line = line.strip()
            if not line:
                continue
            for url in self._extract_urls(line) or [line]:
                cleaned = url.strip()
                if cleaned and cleaned not in self.youtube_batch_urls:
                    self.youtube_batch_urls.append(cleaned)
                    added += 1
        if added:
            self._refresh_youtube_batch_listbox()
        return added

    def _add_batch_url_to_youtube_batch(self):
        value = self.batch_url_var.get().strip() or self.url_var.get().strip()
        if not value:
            messagebox.showwarning(self._app_title(), self._t("youtube_missing_link"))
            return
        added = self._append_youtube_batch_urls(value)
        if added:
            self.batch_url_var.set("")
            self.url_var.set("")
            self._log(self._t("youtube_link_added_log"))
            self._set_last_action(self._t("youtube_batch_updated_detail", count=added))

    def _add_current_url_to_youtube_batch(self):
        self._add_batch_url_to_youtube_batch()

    def _clear_youtube_batch(self):
        if self._is_busy():
            return
        self.youtube_batch_urls.clear()
        self._refresh_youtube_batch_listbox()

    def _collect_youtube_batch_urls(self):
        return list(self.youtube_batch_urls)

    def _paste_clipboard_to_youtube_batch(self, show_empty_message=True):
        try:
            clipboard_text = self.clipboard_get().strip()
        except tk.TclError:
            clipboard_text = ""

        urls = self._extract_urls(clipboard_text)
        if urls:
            added = self._append_youtube_batch_urls("\n".join(urls))
            if added:
                self.status_var.set(self._t("youtube_batch_updated_status"))
                self.detail_var.set(self._t("youtube_batch_updated_detail", count=added))
                self._log(self._t("youtube_batch_updated_log", count=added))
                self._set_last_action(self._t("youtube_batch_updated_detail", count=added))
            return bool(added)

        if clipboard_text:
            added = self._append_youtube_batch_urls(clipboard_text)
            if added:
                self.status_var.set(self._t("youtube_batch_updated_status"))
                self.detail_var.set(self._t("youtube_batch_updated_text_detail"))
                self._log(self._t("youtube_batch_updated_text_log"))
                self._set_last_action(self._t("youtube_batch_updated_text_detail"))
            return bool(added)

        if show_empty_message:
            messagebox.showinfo(self._app_title(), self._t("clipboard_no_text"))
        return False

    def _refresh_youtube_batch_summary(self):
        total = len(self._collect_youtube_batch_urls())
        self.batch_summary_var.set(self._t("youtube_batch_summary", total=total))

    def _append_query_entries(self, text):
        added = 0
        for line in text.splitlines():
            line = line.strip()
            if not line:
                continue
            urls = self._extract_urls(line)
            if urls:
                for url in urls:
                    item_id = self._next_item_id()
                    item = self._create_url_batch_item(url, None)
                    item["id"] = item_id
                    self.image_items.append(item)
                    threading.Thread(
                        target=self._load_preview_for_item,
                        args=(item_id, url),
                        daemon=True,
                    ).start()
                    added += 1
            else:
                self.image_items.append(self._create_query_item(line))
                added += 1
        if added:
            self._refresh_image_listbox()
        return added

    def _add_list_entry(self):
        value = self.list_entry_var.get().strip()
        if not value:
            return
        self._append_query_entries(value)
        self.list_entry_var.set("")

    def _clear_image_items(self):
        if self._is_busy():
            return
        self.image_items.clear()
        self.selected_image_index = None
        self._refresh_image_listbox()
        self.list_entry_var.set("")

    def _collect_search_entries(self):
        return [item["query"] for item in self.image_items if item.get("kind") == "query"]

    def _load_queries_from_file(self):
        file_path = filedialog.askopenfilename(
            title=self._t("load_queries_title"),
            filetypes=[(self._t("text_files"), "*.txt"), (self._t("all_files"), "*.*")],
        )
        if not file_path:
            return

        try:
            content = Path(file_path).read_text(encoding="utf-8", errors="ignore").strip()
        except OSError as error:
            messagebox.showerror(self._app_title(), self._t("file_read_error", error=error))
            return

        if not content:
            messagebox.showinfo(self._app_title(), self._t("file_empty"))
            return

        self._append_query_entries(content)
        self._log(self._t("queries_loaded_log", path=file_path))

    def _load_youtube_links_from_file(self):
        file_path = filedialog.askopenfilename(
            title=self._t("load_youtube_title"),
            filetypes=[(self._t("text_files"), "*.txt"), (self._t("all_files"), "*.*")],
        )
        if not file_path:
            return

        try:
            content = Path(file_path).read_text(encoding="utf-8", errors="ignore").strip()
        except OSError as error:
            messagebox.showerror(self._app_title(), self._t("file_read_error", error=error))
            return

        if not content:
            messagebox.showinfo(self._app_title(), self._t("file_empty"))
            return

        self._append_youtube_batch_urls(content)
        self._log(self._t("youtube_links_loaded_log", path=file_path))

    def _log(self, message):
        self.log_box.configure(state="normal")
        self.log_box.insert("end", f"{message}\n")
        self.log_box.see("end")
        self.log_box.configure(state="disabled")

    def _current_output_folder(self):
        if self.section_var.get() == "youtube":
            return Path(self.output_var.get().strip() or DEFAULT_YOUTUBE_FOLDER)
        return Path(self.image_output_var.get().strip() or DEFAULT_IMAGE_FOLDER)

    def _open_output_folder(self):
        folder = self._current_output_folder()
        folder.mkdir(parents=True, exist_ok=True)
        os.startfile(folder)

    def _is_busy(self):
        return self.active_thread is not None and self.active_thread.is_alive()

    def _set_busy(self, busy):
        state = "disabled" if busy else "normal"

        for widget in (
            self.youtube_tab_button,
            self.images_tab_button,
            self.settings_button,
            self.download_button,
            self.youtube_add_button,
            self.youtube_load_file_button,
            self.youtube_clear_button,
            self.youtube_batch_download_button,
            self.youtube_autopaste_toggle,
            self.youtube_open_folder_button,
            self.browse_button,
            self.url_entry,
            self.folder_entry,
            self.quality_menu,
            self.video_radio,
            self.audio_radio,
            self.search_source_menu,
            self.list_entry,
            self.add_list_item_button,
            self.load_query_file_button,
            self.search_queries_button,
            self.clear_list_button,
            self.paste_now_button,
            self.images_autopaste_toggle,
            self.image_format_menu,
            self.image_quality_menu,
            self.image_remove_button,
            self.image_replace_button,
            self.image_folder_entry,
            self.image_browse_button,
            self.image_open_folder_button,
            self.image_download_button,
        ):
            widget.configure(state=state)

        if hasattr(self, "youtube_batch_listbox"):
            self.youtube_batch_listbox.configure(state=state)
        if hasattr(self, "image_listbox"):
            self.image_listbox.configure(state=state)
        if not busy:
            self._apply_search_source_state()
        else:
            self._apply_search_source_state()

    def _selected_quality_value(self):
        return self.current_quality_map.get(self.quality_var.get(), "best")

    def _handle_enter(self, _event):
        if self.section_var.get() == "youtube":
            self._start_youtube_download()
        elif self.focus_get() == self.list_entry:
            self._add_list_entry()
            return "break"

    def _set_progress(self, percent):
        self.current_progress = max(0, min(100, float(percent)))
        width = max(self.progress_canvas.winfo_width(), 1)
        fill_width = int(width * (self.current_progress / 100))
        self.progress_canvas.coords(self.progress_fill, 0, 0, fill_width, 18)
        self.progress_canvas.itemconfigure(
            self.progress_text, text=f"{self.current_progress:.0f}%"
        )

    def _start_youtube_download(self):
        url = self.url_var.get().strip()
        if not url:
            messagebox.showwarning(self._app_title(), self._t("youtube_missing_link"))
            return
        self._start_youtube_download_urls([url], batch_mode=False)

    def _start_youtube_batch_download(self):
        urls = self._collect_youtube_batch_urls()
        if not urls:
            messagebox.showwarning(self._app_title(), self._t("youtube_batch_empty_warning"))
            return
        self._start_youtube_download_urls(urls, batch_mode=True)

    def _start_youtube_download_urls(self, urls, batch_mode):
        output_folder = Path(self.output_var.get().strip() or DEFAULT_YOUTUBE_FOLDER)
        mode = self.mode_var.get()
        quality_label = self.quality_var.get()
        quality_value = self._selected_quality_value()

        if self._is_busy():
            messagebox.showinfo(self._app_title(), self._t("operation_busy"))
            return

        output_folder.mkdir(parents=True, exist_ok=True)
        self._set_progress(0)
        self._set_busy(True)

        if batch_mode:
            self.status_var.set(self._t("preparing_batch"))
            self.detail_var.set(f"{mode} | {quality_label} | Links: {len(urls)}")
            self._log(f"Inicio de lote YouTube: {len(urls)} link(s)")
            self._log(f"Modo: {mode} | Calidad: {quality_label}")
            target = self._download_youtube_batch_worker
            args = (urls, mode, quality_value, quality_label, output_folder)
        else:
            self.status_var.set(self._t("preparing_download"))
            self.detail_var.set(f"{mode} | {quality_label} | Destino: {output_folder}")
            self._log(f"Inicio de descarga YouTube: {urls[0]}")
            self._log(f"Modo: {mode} | Calidad: {quality_label}")
            target = self._download_youtube_worker
            args = (urls[0], mode, quality_value, quality_label, output_folder)

        self.active_thread = threading.Thread(target=target, args=args, daemon=True)
        self.active_thread.start()

    def _build_video_format(self, quality_value, ffmpeg_available):
        if quality_value == "best":
            if ffmpeg_available:
                return "bestvideo+bestaudio/best"
            return "best[ext=mp4]/best"

        if ffmpeg_available:
            return (
                f"bestvideo[height<={quality_value}]+bestaudio/"
                f"best[height<={quality_value}]"
            )

        return (
            f"best[height<={quality_value}][ext=mp4]/"
            f"best[height<={quality_value}]/best"
        )

    def _build_youtube_options(
        self,
        mode,
        quality_value,
        quality_label,
        output_folder,
        ffmpeg_available,
        hook,
        audio_format=None,
    ):
        options = {
            "noplaylist": True,
            "outtmpl": str(output_folder / "%(title).180B [%(id)s].%(ext)s"),
            "progress_hooks": [hook],
            "quiet": True,
            "no_warnings": True,
        }
        options.update(youtube_dl_extra_options())

        if mode == "Video":
            options["format"] = self._build_video_format(quality_value, ffmpeg_available)
            if ffmpeg_available:
                options["merge_output_format"] = "mp4"
        else:
            options["format"] = audio_format or audio_format_candidates(ffmpeg_available)[0]
            if ffmpeg_available:
                ffmpeg_path = ffmpeg_location()
                if ffmpeg_path:
                    options["ffmpeg_location"] = ffmpeg_path
                target_quality = "320" if quality_value == "best" else str(quality_value)
                options["postprocessors"] = [
                    {
                        "key": "FFmpegExtractAudio",
                        "preferredcodec": "mp3",
                        "preferredquality": target_quality,
                    }
                ]
        return options

    def _format_youtube_download_error(self, error, mode, has_ffmpeg):
        message = strip_ansi(error)
        if mode == "Audio" and is_format_unavailable_error(error) and not has_ffmpeg:
            return self._t("youtube_audio_error_need_ffmpeg")
        return message

    def _log_youtube_mode_details(self, mode, quality_value, quality_label, ffmpeg_available):
        if mode == "Video":
            if not ffmpeg_available:
                self.worker_queue.put(
                    (
                        "log",
                        "ffmpeg no esta instalado. Se usara la mejor opcion de video ya combinada.",
                    )
                )
        else:
            if ffmpeg_available:
                target_quality = "320" if quality_value == "best" else quality_value
                self.worker_queue.put(
                    ("log", f"Se convertira el audio a MP3 con calidad objetivo {quality_label}.")
                )
            else:
                self.worker_queue.put(
                    ("log", self._t("youtube_audio_no_ffmpeg_info"))
                )

    def _download_youtube_item(
        self, url, mode, quality_value, quality_label, output_folder, ffmpeg_available, hook
    ):
        if mode != "Audio":
            options = self._build_youtube_options(
                mode, quality_value, quality_label, output_folder, ffmpeg_available, hook
            )
            with YoutubeDL(options) as ydl:
                info = ydl.extract_info(url, download=True)
            return info.get("title", "Archivo")

        last_error = None
        candidates = audio_format_candidates(ffmpeg_available)
        for index, audio_format in enumerate(candidates):
            options = self._build_youtube_options(
                mode,
                quality_value,
                quality_label,
                output_folder,
                ffmpeg_available,
                hook,
                audio_format=audio_format,
            )
            try:
                with YoutubeDL(options) as ydl:
                    info = ydl.extract_info(url, download=True)
                return info.get("title", "Archivo")
            except DownloadError as error:
                last_error = error
                if not is_format_unavailable_error(error) or index >= len(candidates) - 1:
                    break
                self.worker_queue.put(("log", self._t("youtube_audio_retry_log")))

        if last_error is None:
            raise DownloadError("No se pudo descargar el audio.")
        raise DownloadError(
            self._format_youtube_download_error(last_error, mode, ffmpeg_available)
        ) from last_error

    def _download_youtube_worker(self, url, mode, quality_value, quality_label, output_folder):
        has_ffmpeg = is_ffmpeg_available()
        self._log_youtube_mode_details(mode, quality_value, quality_label, has_ffmpeg)

        def hook(data):
            status = data.get("status")

            if status == "downloading":
                total = data.get("total_bytes") or data.get("total_bytes_estimate") or 0
                downloaded = data.get("downloaded_bytes", 0)
                percent = (downloaded / total * 100) if total else 0
                speed = format_speed(data.get("speed"))
                eta = data.get("eta")
                transferred = f"{format_bytes(downloaded)} / {format_bytes(total)}"

                if eta is None:
                    detail_text = f"{transferred} | {speed}"
                else:
                    detail_text = f"{transferred} | {speed} | ETA: {int(eta)} s"

                self.worker_queue.put(("progress", percent))
                self.worker_queue.put(("status", f"Descargando... {percent:.1f}%"))
                self.worker_queue.put(("detail", detail_text))

            elif status == "finished":
                self.worker_queue.put(("progress", 100))
                self.worker_queue.put(("status", "Procesando archivo final..."))
                self.worker_queue.put(("detail", "Ya se descargo el archivo base."))

        try:
            title = self._download_youtube_item(
                url, mode, quality_value, quality_label, output_folder, has_ffmpeg, hook
            )
            self.worker_queue.put(("log", f"Descarga completada: {title}"))
            self.worker_queue.put(("status", "Descarga terminada."))
            self.worker_queue.put(
                ("detail", f"{mode} | {quality_label} | Guardado en {output_folder}")
            )
            self.worker_queue.put(("done", f"Se guardo en: {output_folder}"))
        except DownloadError as error:
            detail = self._format_youtube_download_error(error, mode, has_ffmpeg)
            self.worker_queue.put(("error", f"No se pudo descargar: {detail}"))
        except Exception as error:
            self.worker_queue.put(("error", f"Ocurrio un error inesperado: {strip_ansi(error)}"))

    def _download_youtube_batch_worker(self, urls, mode, quality_value, quality_label, output_folder):
        has_ffmpeg = is_ffmpeg_available()
        self._log_youtube_mode_details(mode, quality_value, quality_label, has_ffmpeg)

        total = len(urls)
        downloaded_count = 0
        failed = []

        try:
            for index, url in enumerate(urls, start=1):
                self.worker_queue.put(("status", f"Preparando {index}/{total}..."))
                self.worker_queue.put(("detail", url))

                def hook(data, index=index, total=total):
                    status = data.get("status")

                    if status == "downloading":
                        total_bytes = data.get("total_bytes") or data.get("total_bytes_estimate") or 0
                        downloaded = data.get("downloaded_bytes", 0)
                        percent = (downloaded / total_bytes * 100) if total_bytes else 0
                        overall = ((index - 1) + (percent / 100)) / total * 100
                        speed = format_speed(data.get("speed"))
                        eta = data.get("eta")
                        transferred = f"{format_bytes(downloaded)} / {format_bytes(total_bytes)}"

                        if eta is None:
                            detail_text = f"{transferred} | {speed}"
                        else:
                            detail_text = f"{transferred} | {speed} | ETA: {int(eta)} s"

                        self.worker_queue.put(("progress", overall))
                        self.worker_queue.put(("status", f"Descargando {index}/{total}... {percent:.1f}%"))
                        self.worker_queue.put(("detail", detail_text))
                    elif status == "finished":
                        self.worker_queue.put(("progress", index / total * 100))
                        self.worker_queue.put(("status", f"Procesando {index}/{total}..."))
                        self.worker_queue.put(("detail", "Ya se descargo el archivo base."))

                try:
                    title = self._download_youtube_item(
                        url,
                        mode,
                        quality_value,
                        quality_label,
                        output_folder,
                        has_ffmpeg,
                        hook,
                    )
                    downloaded_count += 1
                    self.worker_queue.put(("log", f"Descarga completada {index}/{total}: {title}"))
                except DownloadError as error:
                    failed.append((url, error))
                    self.worker_queue.put(("log", f"Fallo {index}/{total}: {url} | {error}"))
                    self.worker_queue.put(("progress", index / total * 100))
                except Exception as error:
                    failed.append((url, error))
                    self.worker_queue.put(("log", f"Fallo {index}/{total}: {url} | {error}"))
                    self.worker_queue.put(("progress", index / total * 100))

            if downloaded_count == 0:
                self.worker_queue.put(("error", "No se pudo descargar ningun link del lote de YouTube."))
                return

            if failed:
                self.worker_queue.put(
                    ("log", f"Se omitieron {len(failed)} link(s) del lote por error.")
                )

            self.worker_queue.put(("status", "Descarga terminada."))
            self.worker_queue.put(
                ("detail", f"{downloaded_count}/{total} link(s) guardados en {output_folder}")
            )
            self.worker_queue.put(
                ("done", f"Se descargaron {downloaded_count} link(s) en: {output_folder}")
            )
        except Exception as error:
            self.worker_queue.put(("error", f"No se pudo completar el lote de YouTube: {error}"))

    def _refresh_batch_view(self):
        self._refresh_image_listbox()

    def _refresh_batch_summary(self):
        total = len(self.image_items)
        urls = sum(1 for item in self.image_items if item["kind"] == "url")
        clips = sum(1 for item in self.image_items if item["kind"] == "clipboard")
        searches = sum(1 for item in self.image_items if item["kind"] in ("pexels", "flickr"))
        self.batch_summary_var.set(
            self._t(
                "image_batch_summary",
                total=total,
                urls=urls,
                clipboard=clips,
                searches=searches,
            )
        )

    def _next_item_id(self):
        item_id = self.next_item_id
        self.next_item_id += 1
        return item_id

    def _add_batch_items(self, items):
        for item in items:
            item["id"] = self._next_item_id()
            if item["kind"] == "clipboard" and not item.get("filename_hint"):
                item["filename_hint"] = f"portapapeles_{item['id']:03d}.png"
            self.image_items.append(item)

        self._refresh_image_listbox()

    def _find_item_index(self, item_id):
        for index, item in enumerate(self.image_items):
            if item["id"] == item_id:
                return index
        return None

    def _remove_batch_item(self, item_id):
        if self._is_busy():
            return

        index = self._find_item_index(item_id)
        if index is None:
            return

        removed = self.image_items.pop(index)
        if self.selected_image_index == index:
            self.selected_image_index = None
        elif self.selected_image_index is not None and self.selected_image_index > index:
            self.selected_image_index -= 1
        self._refresh_image_listbox()
        self._log(self._t("removed_from_batch_log", title=removed["title"]))

    def _clear_batch_items(self):
        self._clear_image_items()
        self._log(self._t("images_batch_cleared_log"))

    def _prepare_display_image(self, image):
        prepared = image.copy()
        prepared.load()
        if prepared.mode not in ("RGB", "RGBA"):
            if "A" in prepared.getbands():
                prepared = prepared.convert("RGBA")
            else:
                prepared = prepared.convert("RGB")
        return prepared

    def _download_bytes(self, url, headers=None, timeout=30):
        request = urllib.request.Request(
            url,
            headers=headers or {"User-Agent": "Mozilla/5.0"},
        )
        with urllib.request.urlopen(request, timeout=timeout) as response:
            return response.read(), response.headers

    def _load_preview_from_url(self, url):
        data, _headers = self._download_bytes(url)
        with Image.open(io.BytesIO(data)) as image:
            return self._prepare_display_image(image)

    def _create_url_batch_item(self, url, preview_image):
        parsed_path = urllib.parse.unquote(urllib.parse.urlparse(url).path)
        name = Path(parsed_path).name or "imagen_url"
        stem = sanitize_filename(Path(name).stem or "imagen_url")
        suffix = Path(name).suffix.lower() or ".jpg"

        return {
            "kind": "url",
            "title": stem,
            "subtitle": self._t("direct_url_subtitle"),
            "preview_image": preview_image,
            "download_url": url,
            "filename_hint": f"{stem}{suffix}",
            "image_data": None,
        }

    def _create_clipboard_batch_item(self, image, position):
        return {
            "kind": "clipboard",
            "title": self._t("clipboard_image_title", position=position),
            "subtitle": self._t("clipboard_subtitle"),
            "preview_image": self._prepare_display_image(image),
            "download_url": None,
            "filename_hint": "",
            "image_data": self._prepare_display_image(image),
        }

    def _build_pexels_item(self, query, photo, results, page, index):
        preview_url = (
            photo.get("src", {}).get("medium")
            or photo.get("src", {}).get("small")
            or photo.get("src", {}).get("tiny")
            or photo.get("src", {}).get("original")
        )
        preview_image = self._load_preview_from_url(preview_url)

        return {
            "kind": "pexels",
            "title": query,
            "subtitle": f"Pexels | Foto {photo.get('id', '-')}",
            "preview_image": preview_image,
            "download_url": photo.get("src", {}).get("original"),
            "filename_hint": f"pexels_{photo.get('id', 'imagen')}.jpg",
            "image_data": None,
            "query": query,
            "candidate_results": results,
            "candidate_page": page,
            "candidate_index": index,
            "search_source": "Pexels",
        }

    def _build_flickr_item(self, query, photo, results, page, index):
        preview_url = photo.get("media", {}).get("m")
        preview_image = self._load_preview_from_url(preview_url)

        title = sanitize_filename(photo.get("title") or query or "flickr_image")
        suffix = Path(urllib.parse.urlparse(preview_url).path).suffix or ".jpg"

        author = photo.get("author", "autor desconocido").replace("nobody@flickr.com ", "")

        return {
            "kind": "flickr",
            "title": query,
            "subtitle": f"Flickr | {author}",
            "preview_image": preview_image,
            "download_url": preview_url,
            "filename_hint": f"{title}{suffix}",
            "image_data": None,
            "query": query,
            "candidate_results": results,
            "candidate_page": page,
            "candidate_index": index,
            "search_source": "Flickr Public",
        }

    def _search_pexels_photos(self, api_key, query, page=1, per_page=8):
        params = urllib.parse.urlencode(
            {"query": query, "page": page, "per_page": per_page}
        )
        request = urllib.request.Request(
            f"{PEXELS_SEARCH_URL}?{params}",
            headers={
                "Authorization": api_key,
                "User-Agent": "Mozilla/5.0",
            },
        )

        try:
            with urllib.request.urlopen(request, timeout=30) as response:
                payload = json.loads(response.read().decode("utf-8"))
                return payload.get("photos", [])
        except urllib.error.HTTPError as error:
            if error.code in (401, 403):
                raise RuntimeError("La API key de Pexels es invalida o no tiene permiso.")
            if error.code == 429:
                raise RuntimeError("Pexels devolvio limite de peticiones. Intenta mas tarde.")
            raise RuntimeError(f"Pexels respondio con error HTTP {error.code}.")
        except urllib.error.URLError as error:
            raise RuntimeError(f"No se pudo conectar con Pexels: {error.reason}")

    def _search_flickr_photos(self, query, page=1, per_page=8):
        tags = ",".join(part for part in re.split(r"\s+", query.strip()) if part)
        params = urllib.parse.urlencode(
            {
                "format": "json",
                "nojsoncallback": 1,
                "tagmode": "all",
                "tags": tags or query,
            }
        )
        request = urllib.request.Request(
            f"{FLICKR_FEED_URL}?{params}",
            headers={"User-Agent": "DescargadorMultimedia/1.0 (Windows desktop app)"},
        )

        try:
            with urllib.request.urlopen(request, timeout=30) as response:
                payload = json.loads(response.read().decode("utf-8"))
        except urllib.error.URLError as error:
            raise RuntimeError(f"No se pudo conectar con Flickr: {error.reason}")

        items = payload.get("items", [])
        start = max(0, (page - 1) * per_page)
        end = start + per_page
        return items[start:end]

    def _perform_image_search(self, source, query, api_key, page=1, per_page=8):
        if source == "Pexels":
            return self._search_pexels_photos(api_key, query, page=page, per_page=per_page)
        return self._search_flickr_photos(query, page=page, per_page=per_page)

    def _build_search_item(self, source, query, result, results, page, index):
        if source == "Pexels":
            return self._build_pexels_item(query, result, results, page, index)
        return self._build_flickr_item(query, result, results, page, index)

    def _extract_urls(self, text):
        return [match.strip().rstrip(",") for match in re.findall(r"https?://\S+", text)]

    def _has_search_terms(self, entries):
        return any(not self._extract_urls(entry) for entry in entries)

    def _start_query_search(self):
        entries = self._collect_search_entries()
        source = self.search_source_var.get()
        api_key = self.pexels_key_var.get().strip()

        if source == "Pexels" and self._has_search_terms(entries) and not api_key:
            messagebox.showwarning(self._app_title(), self._t("pexels_key_empty"))
            return

        if not entries:
            messagebox.showwarning(self._app_title(), self._t("search_entries_missing"))
            return

        if self._is_busy():
            messagebox.showinfo(self._app_title(), self._t("operation_busy"))
            return

        self._set_progress(0)
        self.status_var.set(self._t("searching_images"))
        self.detail_var.set(f"Fuente: {source} | Entradas: {len(entries)}")
        self._set_busy(True)

        self.active_thread = threading.Thread(
            target=self._search_queries_worker,
            args=(entries, source, api_key),
            daemon=True,
        )
        self.active_thread.start()

    def _search_queries_worker(self, entries, source, api_key):
        added_items = []
        total = len(entries)

        try:
            for index, entry in enumerate(entries, start=1):
                self.worker_queue.put(("status", f"Procesando {index}/{total}..."))

                urls = self._extract_urls(entry)
                if urls:
                    for url in urls:
                        self.worker_queue.put(("detail", f"Link | {url}"))
                        try:
                            preview = self._load_preview_from_url(url)
                            added_items.append(self._create_url_batch_item(url, preview))
                            self.worker_queue.put(("log", f"Link agregado al lote: {url}"))
                        except Exception as error:
                            self.worker_queue.put(("log", f"Se omitio un link: {url} | {error}"))
                    self.worker_queue.put(("progress", index / total * 100))
                    continue

                query = entry
                self.worker_queue.put(("detail", f"{source} | {query}"))

                results = self._perform_image_search(source, query, api_key, page=1, per_page=8)
                if not results:
                    self.worker_queue.put(("log", f"Sin resultados en {source} para: {query}"))
                    self.worker_queue.put(("progress", index / total * 100))
                    continue

                added_items.append(self._build_search_item(source, query, results[0], results, 1, 0))
                self.worker_queue.put(("log", f"Resultado agregado desde {source} para: {query}"))
                self.worker_queue.put(("progress", index / total * 100))

            self.worker_queue.put(("add_items", added_items))
            self.worker_queue.put(
                (
                    "operation_complete",
                    f"Proceso terminado. Se agregaron {len(added_items)} elemento(s) al lote.",
                )
            )
        except Exception as error:
            self.worker_queue.put(("error", f"No se pudo completar la busqueda: {error}"))

    def _collect_clipboard_image_items(self):
        if self._is_busy():
            return None

        try:
            clipboard_data = ImageGrab.grabclipboard()
        except Exception:
            return None

        added_items = []

        if isinstance(clipboard_data, Image.Image):
            added_items.append(self._create_clipboard_batch_item(clipboard_data.copy(), 1))
        elif isinstance(clipboard_data, list):
            for index, item in enumerate(clipboard_data, start=1):
                path = Path(item)
                if not path.is_file():
                    continue

                try:
                    with Image.open(path) as image:
                        added_items.append(self._create_clipboard_batch_item(image.copy(), index))
                except OSError:
                    continue

        return added_items or None

    def _paste_clipboard_content(self, show_empty_message=True):
        if self._is_busy():
            if show_empty_message:
                messagebox.showinfo(self._app_title(), self._t("operation_busy"))
            return False

        image_items = self._collect_clipboard_image_items()
        if image_items:
            self._add_batch_items(image_items)
            self._log(self._t("clipboard_images_added_log", count=len(image_items)))
            self.status_var.set(self._t("image_added_status"))
            self.detail_var.set(self._t("image_added_detail", count=len(image_items)))
            return True

        try:
            clipboard_text = self.clipboard_get().strip()
        except tk.TclError:
            clipboard_text = ""

        if clipboard_text:
            added = self._append_query_entries(clipboard_text)
            if added:
                self._log(self._t("clipboard_list_log"))
                self.status_var.set(self._t("list_updated_status"))
                self.detail_var.set(self._t("list_updated_detail"))
            return bool(added)

        if show_empty_message:
            messagebox.showinfo(self._app_title(), self._t("clipboard_no_data"))
        return False

    def _handle_global_paste(self, _event=None):
        return None

    def _start_replace_item(self, item_id):
        if self._is_busy():
            messagebox.showinfo(self._app_title(), self._t("operation_busy"))
            return

        index = self._find_item_index(item_id)
        if index is None:
            return

        item = self.image_items[index]
        if item["kind"] not in ("pexels", "flickr"):
            return

        api_key = self.pexels_key_var.get().strip()
        source = item.get("search_source", "Pexels")
        if source == "Pexels" and not api_key:
            messagebox.showwarning(self._app_title(), self._t("pexels_key_empty"))
            return

        self._set_progress(0)
        self.status_var.set(self._t("searching_replacement"))
        self.detail_var.set(item["title"])
        self._set_busy(True)

        snapshot = {
            "id": item["id"],
            "query": item["query"],
            "candidate_results": item["candidate_results"],
            "candidate_page": item["candidate_page"],
            "candidate_index": item["candidate_index"],
            "search_source": source,
        }

        self.active_thread = threading.Thread(
            target=self._replace_item_worker,
            args=(snapshot, api_key),
            daemon=True,
        )
        self.active_thread.start()

    def _replace_item_worker(self, snapshot, api_key):
        query = snapshot["query"]
        source = snapshot["search_source"]
        results = snapshot["candidate_results"]
        page = snapshot["candidate_page"]
        index = snapshot["candidate_index"] + 1

        try:
            while True:
                if index < len(results):
                    replacement = self._build_search_item(source, query, results[index], results, page, index)
                    replacement["id"] = snapshot["id"]
                    self.worker_queue.put(("replace_item", replacement))
                    self.worker_queue.put(("progress", 100))
                    self.worker_queue.put(("operation_complete", f"Imagen reemplazada en {source} para: {query}"))
                    return

                page += 1
                results = self._perform_image_search(source, query, api_key, page=page, per_page=8)
                if not results:
                    raise RuntimeError("Ya no hay mas resultados para ese termino.")

                index = 0
        except Exception as error:
            self.worker_queue.put(("error", f"No se pudo reemplazar la imagen: {error}"))

    def _clear_text_placeholder(self, text_widget, placeholder):
        content = text_widget.get("1.0", "end").strip()
        if content == placeholder:
            text_widget.delete("1.0", "end")
            text_widget.configure(fg=WIN_BLACK)

    def _restore_text_placeholder(self, text_widget, placeholder):
        content = text_widget.get("1.0", "end").strip()
        if not content:
            text_widget.insert("end", placeholder)
            text_widget.configure(fg=WIN_DARK)

    def _resize_image_for_quality(self, image, quality):
        max_px = IMAGE_QUALITY_MAX_PX.get(quality, IMAGE_QUALITY_MAX_PX["media"])
        resized = image.copy()
        resized.thumbnail((max_px, max_px), Image.Resampling.LANCZOS)
        return resized

    def _normalize_image_format(self, value):
        normalized = (value or "").upper()
        if normalized in ("JPG", "JPEG"):
            return "JPEG"
        if normalized in ("PNG", "WEBP"):
            return normalized
        return "PNG"

    def _image_extension_for_format(self, image_format):
        return {"PNG": ".png", "JPEG": ".jpg", "WEBP": ".webp"}.get(image_format, ".png")

    def _finalize_image_file(self, file_path, export_format, export_quality):
        file_path = Path(file_path)
        with Image.open(file_path) as opened:
            image = self._prepare_display_image(opened)
            source_format = self._normalize_image_format(opened.format or file_path.suffix.lstrip("."))

        image = self._resize_image_for_quality(image, export_quality)

        if export_format == "auto":
            target_format = source_format
        else:
            target_format = export_format

        target_ext = self._image_extension_for_format(target_format)
        target_path = file_path.with_suffix(target_ext)
        if target_path != file_path:
            target_path = ensure_unique_path(target_path)

        save_image = image
        if target_format == "JPEG" and save_image.mode in ("RGBA", "LA", "P"):
            save_image = save_image.convert("RGB")

        save_kwargs = {}
        if target_format == "JPEG":
            save_kwargs["quality"] = 90
        elif target_format == "WEBP":
            save_kwargs["quality"] = 85

        save_image.save(target_path, format=target_format, **save_kwargs)
        if file_path.resolve() != target_path.resolve() and file_path.exists():
            file_path.unlink()
        return target_path

    def _save_image_item(self, item, output_folder, index, total, export_format, export_quality):
        if item["kind"] == "clipboard":
            file_path = ensure_unique_path(output_folder / item["filename_hint"])
            image_to_save = item["image_data"].copy()
            if image_to_save.mode not in ("RGB", "RGBA", "L"):
                if "A" in image_to_save.getbands():
                    image_to_save = image_to_save.convert("RGBA")
                else:
                    image_to_save = image_to_save.convert("RGB")

            image_to_save.save(file_path, format="PNG")
            file_path = self._finalize_image_file(file_path, export_format, export_quality)
            self.worker_queue.put(("progress", index / total * 100))
            self.worker_queue.put(
                ("detail", f"Guardando {index}/{total} | {item['title']}")
            )
            return file_path

        url = item["download_url"]
        request = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
        with urllib.request.urlopen(request, timeout=30) as response:
            content_type = response.headers.get("Content-Type", "")
            total_header = response.headers.get("Content-Length")
            total_bytes = int(total_header) if total_header and total_header.isdigit() else 0

            file_name = item["filename_hint"]
            if not Path(file_name).suffix:
                file_name = f"{file_name}{guess_image_extension(url, content_type)}"

            file_path = ensure_unique_path(output_folder / file_name)

            downloaded = 0
            with open(file_path, "wb") as output_file:
                while True:
                    chunk = response.read(65536)
                    if not chunk:
                        break

                    output_file.write(chunk)
                    downloaded += len(chunk)

                    if total_bytes:
                        overall = ((index - 1) + (downloaded / total_bytes)) / total * 100
                        self.worker_queue.put(("progress", overall))
                        self.worker_queue.put(
                            (
                                "detail",
                                f"Guardando {index}/{total} | {format_bytes(downloaded)} / {format_bytes(total_bytes)}",
                            )
                        )

        if not total_bytes:
            self.worker_queue.put(("progress", index / total * 100))

        return self._finalize_image_file(file_path, export_format, export_quality)

    def _start_image_download(self):
        downloadable = [item for item in self.image_items if item.get("kind") != "query"]
        if not downloadable:
            if any(item.get("kind") == "query" for item in self.image_items):
                messagebox.showwarning(
                    self._app_title(),
                    self._t("search_entries_missing"),
                )
            else:
                messagebox.showwarning(self._app_title(), self._t("image_batch_empty_warning"))
            return

        if self._is_busy():
            messagebox.showinfo(self._app_title(), self._t("operation_busy"))
            return

        output_folder = Path(self.image_output_var.get().strip() or DEFAULT_IMAGE_FOLDER)
        output_folder.mkdir(parents=True, exist_ok=True)

        snapshot = []
        for item in downloadable:
            cloned = dict(item)
            if item.get("image_data") is not None:
                cloned["image_data"] = item["image_data"].copy()
            if item.get("preview_image") is not None:
                cloned["preview_image"] = item["preview_image"].copy()
            snapshot.append(cloned)

        self._set_progress(0)
        self.status_var.set(self._t("preparing_images"))
        self.detail_var.set(self._t("saved_items_count", count=len(snapshot)))
        self._log(f"Inicio de descarga del lote final: {len(snapshot)} elemento(s)")
        self._set_busy(True)

        self.active_thread = threading.Thread(
            target=self._download_images_worker,
            args=(
                snapshot,
                output_folder,
                self._selected_image_export_format(),
                self._selected_image_export_quality(),
            ),
            daemon=True,
        )
        self.active_thread.start()

    def _download_images_worker(self, items, output_folder, export_format, export_quality):
        total = len(items)
        downloaded_count = 0
        failed = []

        try:
            for index, item in enumerate(items, start=1):
                self.worker_queue.put(("status", f"Guardando imagen {index}/{total}..."))
                self.worker_queue.put(("detail", item["title"]))

                try:
                    file_path = self._save_image_item(
                        item,
                        output_folder,
                        index,
                        total,
                        export_format,
                        export_quality,
                    )
                    downloaded_count += 1
                    self.worker_queue.put(("log", f"Guardada: {file_path.name}"))
                except Exception as error:
                    failed.append((item["title"], error))
                    self.worker_queue.put(("log", f"Fallo con {item['title']}: {error}"))
                    self.worker_queue.put(("progress", index / total * 100))

            if downloaded_count == 0:
                self.worker_queue.put(("error", "No se pudo guardar ninguna imagen del lote."))
                return

            if failed:
                self.worker_queue.put(
                    ("log", f"Se omitieron {len(failed)} elemento(s) por error.")
                )

            self.worker_queue.put(("status", "Descarga terminada."))
            self.worker_queue.put(
                ("detail", f"{downloaded_count}/{total} imagenes guardadas en {output_folder}")
            )
            self.worker_queue.put(
                ("done", f"Se guardaron {downloaded_count} imagen(es) en: {output_folder}")
            )
        except Exception as error:
            self.worker_queue.put(("error", f"No se pudo guardar el lote: {error}"))

    def _process_queue(self):
        try:
            while True:
                kind, payload = self.worker_queue.get_nowait()

                if kind == "log":
                    self._log(payload)
                elif kind == "progress":
                    self._set_progress(payload)
                elif kind == "status":
                    self.status_var.set(payload)
                elif kind == "detail":
                    self.detail_var.set(payload)
                elif kind == "add_items":
                    self._add_batch_items(payload)
                elif kind == "preview_loaded":
                    item_id, preview = payload
                    index = self._find_item_index(item_id)
                    if index is not None:
                        self.image_items[index]["preview_image"] = preview
                        if self.selected_image_index == index:
                            self._update_image_preview_panel(self.image_items[index])
                elif kind == "replace_item":
                    index = self._find_item_index(payload["id"])
                    if index is not None:
                        self.image_items[index] = payload
                        self._refresh_image_listbox()
                        self._log(self._t("replaced_image_log", title=payload["title"]))
                elif kind == "hotkey_capture":
                    if not self._hotkey_capture_allowed():
                        continue
                    if self.section_var.get() == "youtube" and self.youtube_autopaste_var.get():
                        if self._paste_clipboard_to_youtube_batch(show_empty_message=False):
                            self.status_var.set(self._t("youtube_batch_updated_status"))
                            self.detail_var.set(
                                self._t(
                                    "hotkey_youtube_detail",
                                    hotkey=self._format_hotkey_label(payload),
                                )
                            )
                    elif self.section_var.get() == "imagenes" and self.images_autopaste_var.get():
                        if self._paste_clipboard_content(show_empty_message=False):
                            self.status_var.set(self._t("image_added_status"))
                            self.detail_var.set(
                                self._t(
                                    "hotkey_images_detail",
                                    hotkey=self._format_hotkey_label(payload),
                                )
                            )
                elif kind == "operation_complete":
                    self.active_thread = None
                    self._set_busy(False)
                    self.status_var.set(self._t("ready"))
                    self.detail_var.set(payload)
                    self._log(payload)
                elif kind == "done":
                    self.active_thread = None
                    self._set_busy(False)
                    self._log(payload)
                    messagebox.showinfo(self._app_title(), payload)
                elif kind == "error":
                    self.active_thread = None
                    self._set_busy(False)
                    self.status_var.set(self._t("operation_failed_status"))
                    self.detail_var.set(self._t("operation_failed_detail"))
                    self._log(payload)
                    messagebox.showerror(self._app_title(), payload)
        except queue.Empty:
            pass

        self.after(100, self._process_queue)

    def _on_close(self):
        self.is_closing = True
        self._close_search_settings()
        self._unregister_capture_hotkey()
        self.destroy()


if __name__ == "__main__":
    DEFAULT_YOUTUBE_FOLDER.mkdir(parents=True, exist_ok=True)
    DEFAULT_IMAGE_FOLDER.mkdir(parents=True, exist_ok=True)
    app = DownloaderApp()
    app.mainloop()
