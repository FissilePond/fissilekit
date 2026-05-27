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
DEFAULT_YOUTUBE_FOLDER = Path.home() / "Downloads" / "YouTube"
DEFAULT_IMAGE_FOLDER = Path.home() / "Downloads" / "Imagenes"
PEXELS_SEARCH_URL = "https://api.pexels.com/v1/search"
FLICKR_FEED_URL = "https://www.flickr.com/services/feeds/photos_public.gne"
SEARCH_SOURCES = ("Pexels", "Flickr Public")
DEFAULT_CAPTURE_HOTKEY = "x"
DEFAULT_THEME = "dark"
DEFAULT_LANGUAGE = "es"

THEME_PALETTES = {
    "dark": {
        "desktop": "#182635",
        "face": "#223548",
        "light": "#2d4359",
        "dark": "#9fb3c8",
        "black": "#f1f6fb",
        "blue": "#35516b",
        "white": "#24384b",
        "edge": "#5e7993",
        "button": "#36526d",
        "button_active": "#456886",
        "tab_idle": "#30485f",
        "tab_active": "#405f7d",
        "title_text": "#f5fbff",
        "glass_top": "#526f8d",
        "glass_mid": "#3f5f7e",
        "glass_bottom": "#23384c",
        "status_top": "#31495f",
        "status_bottom": "#24384b",
        "link": "#9fd0ff",
    },
    "light": {
        "desktop": "#9dc4e4",
        "face": "#edf3fb",
        "light": "#ffffff",
        "dark": "#b8c9db",
        "black": "#1a3656",
        "blue": "#dbeaf9",
        "white": "#ffffff",
        "edge": "#8da6c1",
        "button": "#e7f0fb",
        "button_active": "#d7e6f8",
        "tab_idle": "#d8e8f8",
        "tab_active": "#ffffff",
        "title_text": "#17395d",
        "glass_top": "#fdfefe",
        "glass_mid": "#d8ebfb",
        "glass_bottom": "#9cc4ea",
        "status_top": "#f8fbff",
        "status_bottom": "#dce9f8",
        "link": "#225a8e",
    },
}

TRANSLATIONS = {
    "es": {
        "app_title": "FissileKit",
        "list_placeholder": "Escribe o pega una entrada por linea. Puedes mezclar terminos y links.",
        "youtube_batch_placeholder": "Misma calidad y formato para todos.\nPega o agrega un link de YouTube por linea.",
        "ready": "Listo.",
        "welcome_log": "Bienvenido.",
        "hotkey_preparing": "Captura rapida global: preparando...",
        "hotkey_status_unavailable": "Tecla: no disponible",
        "hotkey_status_disabled": "Tecla: desactivada",
        "hotkey_status_format": "Tecla: {hotkey}",
        "tab_youtube": "YouTube",
        "tab_images": "Imagenes",
        "status_label": "Estado:",
        "log_group": "Registro",
        "brand_credit": "Desarrollado por FissilePond",
        "donations_link": "Donaciones",
        "youtube_data_group": "Datos",
        "youtube_link_label": "Link de YouTube",
        "youtube_add_batch": "Agregar al lote",
        "youtube_batch_group": "Lote de Links",
        "youtube_hotkey_toggle": "Usar tecla global para mandar al lote",
        "load_txt": "Cargar .txt",
        "clear_batch": "Limpiar lote",
        "download_batch": "Descargar lote",
        "format_group": "Formato",
        "quality_group": "Calidad",
        "quality_best": "Mejor disponible",
        "output_folder": "Carpeta de salida",
        "browse": "Buscar...",
        "open_folder": "Abrir carpeta",
        "download": "Descargar",
        "how_to_use": "Como usar",
        "youtube_how_to_use_text": "Uno: pega un link y descarga.\nVarios: agregalos al lote y descarga todo.",
        "search_group": "Buscador Online",
        "search_header_text": "Buscador, lista y lote.",
        "source_label": "Fuente",
        "add_to_list": "Agregar a la lista",
        "add": "Agregar",
        "current_list": "Lista actual",
        "search_images": "Buscar imagenes",
        "quick_paste_group": "Pegado Rapido",
        "paste_now": "Pegar ahora",
        "final_image_batch": "Lote Final de Imagenes",
        "final_batch_text": "Revisa, quita o cambia el lote.",
        "save_group": "Guardado",
        "replace_button": "Otra",
        "remove_button": "Quitar",
        "empty_batch_text": "El lote esta vacio. Agrega links, imagenes pegadas o resultados de busqueda.",
        "clipboard_image_title": "Imagen pegada {position}",
        "clipboard_subtitle": "Portapapeles",
        "direct_url_subtitle": "URL directa",
        "settings_title": "Configuracion",
        "settings_button": "⚙ Configuracion",
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
        "section_ready_youtube": "Modo YouTube listo. Pega un link para comenzar.",
        "section_ready_images": "Modo Imagenes listo. Busca, pega o arma tu lote final.",
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
        "youtube_batch_placeholder": "Same quality and format for all.\nPaste or add one YouTube link per line.",
        "ready": "Ready.",
        "welcome_log": "Welcome.",
        "hotkey_preparing": "Global quick capture: preparing...",
        "hotkey_status_unavailable": "Key: unavailable",
        "hotkey_status_disabled": "Key: disabled",
        "hotkey_status_format": "Key: {hotkey}",
        "tab_youtube": "YouTube",
        "tab_images": "Images",
        "status_label": "Status:",
        "log_group": "Log",
        "brand_credit": "Built by FissilePond",
        "donations_link": "Donations",
        "youtube_data_group": "Data",
        "youtube_link_label": "YouTube link",
        "youtube_add_batch": "Add to batch",
        "youtube_batch_group": "Link Batch",
        "youtube_hotkey_toggle": "Use global hotkey to send to batch",
        "load_txt": "Load .txt",
        "clear_batch": "Clear batch",
        "download_batch": "Download batch",
        "format_group": "Format",
        "quality_group": "Quality",
        "quality_best": "Best available",
        "output_folder": "Output folder",
        "browse": "Browse...",
        "open_folder": "Open folder",
        "download": "Download",
        "how_to_use": "How to use",
        "youtube_how_to_use_text": "Single: paste a link and download.\nMultiple: add them to the batch and download all.",
        "search_group": "Online Search",
        "search_header_text": "Search, list, and batch.",
        "source_label": "Source",
        "add_to_list": "Add to list",
        "add": "Add",
        "current_list": "Current list",
        "search_images": "Search images",
        "quick_paste_group": "Quick Paste",
        "paste_now": "Paste now",
        "final_image_batch": "Final Image Batch",
        "final_batch_text": "Review, remove, or swap items in the batch.",
        "save_group": "Save",
        "replace_button": "Next",
        "remove_button": "Remove",
        "empty_batch_text": "The batch is empty. Add links, pasted images, or search results.",
        "clipboard_image_title": "Pasted image {position}",
        "clipboard_subtitle": "Clipboard",
        "direct_url_subtitle": "Direct URL",
        "settings_title": "Settings",
        "settings_button": "⚙ Settings",
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
        "section_ready_youtube": "YouTube mode is ready. Paste a link to begin.",
        "section_ready_images": "Images mode is ready. Search, paste, or build your final batch.",
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

FONT_NORMAL = ("Segoe UI", 10)
FONT_BOLD = ("Segoe UI", 10, "bold")
FONT_TITLE = ("Segoe UI", 12, "bold")
FONT_SMALL = ("Segoe UI", 9)

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
        self.minsize(1040, 700)
        self.configure(bg=WIN_DESKTOP)

        saved_search_source = self._setting("image_search_source", "Pexels")
        if saved_search_source not in SEARCH_SOURCES:
            saved_search_source = "Flickr Public" if saved_search_source == "Wikimedia Commons" else "Pexels"
        saved_capture_hotkey = self._normalize_hotkey(
            self._setting("capture_hotkey", DEFAULT_CAPTURE_HOTKEY)
        )

        self.section_var = tk.StringVar(value="youtube")
        self.url_var = tk.StringVar()
        self.mode_var = tk.StringVar(value="Video")
        self.quality_var = tk.StringVar()
        self.output_var = tk.StringVar(value=str(DEFAULT_YOUTUBE_FOLDER))
        self.image_output_var = tk.StringVar(value=str(DEFAULT_IMAGE_FOLDER))
        self.pexels_key_var = tk.StringVar(value=self.settings.get("pexels_api_key", ""))
        self.search_source_var = tk.StringVar(value=saved_search_source)
        self.list_entry_var = tk.StringVar()
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
        self.batch_summary_var = tk.StringVar(
            value=self._t("image_batch_summary", total=0, urls=0, clipboard=0, searches=0)
        )

        self.worker_queue = queue.Queue()
        self.active_thread = None
        self.current_quality_map = {}
        self.current_progress = 0.0

        self.image_items = []
        self.next_item_id = 1
        self.card_photo_refs = []
        self.batch_canvas_window = None
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

        app = tk.Frame(self, bg=WIN_FACE, bd=1, relief="solid")
        app.grid(row=0, column=0, sticky="nsew", padx=8, pady=8)
        app.grid_columnconfigure(0, weight=1)
        app.grid_rowconfigure(2, weight=1)

        title_bar = tk.Frame(app, bg=WIN_BLUE, height=34, bd=1, relief="solid")
        title_bar.grid(row=0, column=0, sticky="ew", padx=3, pady=(3, 0))
        title_bar.grid_columnconfigure(1, weight=1)
        title_bar.grid_propagate(False)
        title_bar_bg = tk.Label(title_bar, bd=0, highlightthickness=0)
        title_bar_bg.place(x=0, y=0, relwidth=1, relheight=1)
        title_bar_bg.lower()
        self._bind_gradient(
            title_bar,
            title_bar_bg,
            (
                (0.0, WIN_GLASS_TOP),
                (0.35, WIN_GLASS_MID),
                (1.0, WIN_GLASS_BOTTOM),
            ),
        )
        tk.Frame(title_bar, bg=WIN_LIGHT, height=1).place(relx=0, rely=0, relwidth=1)

        icon = tk.Canvas(
            title_bar,
            width=16,
            height=16,
            bg=WIN_GLASS_MID,
            bd=0,
            highlightthickness=0,
        )
        icon.grid(row=0, column=0, padx=(8, 6), pady=6)
        icon.create_rectangle(2, 2, 7, 7, outline="", fill="#f35325")
        icon.create_rectangle(9, 2, 14, 7, outline="", fill="#81bc06")
        icon.create_rectangle(2, 9, 7, 14, outline="", fill="#05a6f0")
        icon.create_rectangle(9, 9, 14, 14, outline="", fill="#ffba08")

        tk.Label(
            title_bar,
            text=self._app_title(),
            bg=WIN_GLASS_MID,
            fg=WIN_TITLE_TEXT,
            font=FONT_TITLE,
        ).grid(row=0, column=1, sticky="w")

        self.help_button = tk.Button(
            title_bar,
            text="i",
            command=self._open_help_file,
            width=3,
            bg=WIN_BUTTON,
            fg=WIN_BLACK,
            activebackground=WIN_BUTTON_ACTIVE,
            activeforeground=WIN_BLACK,
            relief="solid",
            bd=1,
            font=FONT_BOLD,
        )
        self.help_button.grid(row=0, column=2, sticky="e", padx=(6, 4), pady=4)

        self.settings_button = tk.Button(
            title_bar,
            text=self._t("settings_button"),
            command=self._open_search_settings,
            bg=WIN_BUTTON,
            fg=WIN_BLACK,
            activebackground=WIN_BUTTON_ACTIVE,
            activeforeground=WIN_BLACK,
            relief="solid",
            bd=1,
            font=FONT_BOLD,
            padx=8,
            pady=2,
        )
        self.settings_button.grid(row=0, column=3, sticky="e", padx=(0, 8), pady=4)

        body = tk.Frame(app, bg=WIN_FACE)
        body.grid(row=1, column=0, sticky="nsew", padx=6, pady=6)
        body.grid_columnconfigure(0, weight=1)
        body.grid_rowconfigure(1, weight=1)
        body_bg = tk.Label(body, bd=0, highlightthickness=0)
        body_bg.place(x=0, y=0, relwidth=1, relheight=1)
        body_bg.lower()
        self._bind_gradient(
            body,
            body_bg,
            (
                (0.0, WIN_GLASS_TOP),
                (0.20, "#eef5fd"),
                (1.0, WIN_FACE),
            ),
        )

        tabs = tk.Frame(body, bg=WIN_FACE)
        tabs.grid(row=0, column=0, sticky="w", pady=(0, 6))

        self.youtube_tab_button = self._make_button(
            tabs, self._t("tab_youtube"), lambda: self._set_section("youtube"), width=14
        )
        self.youtube_tab_button.grid(row=0, column=0, padx=(0, 4))

        self.images_tab_button = self._make_button(
            tabs, self._t("tab_images"), lambda: self._set_section("imagenes"), width=14
        )
        self.images_tab_button.grid(row=0, column=1)

        self.content = tk.Frame(body, bg=WIN_WHITE, bd=1, relief="solid")
        self.content.grid(row=1, column=0, sticky="nsew")
        self.content.grid_columnconfigure(0, weight=1)
        self.content.grid_rowconfigure(0, weight=1)

        self.youtube_frame = self._build_youtube_panel(self.content)
        self.youtube_frame.grid(row=0, column=0, sticky="nsew", padx=8, pady=8)

        self.images_frame = self._build_images_panel(self.content)
        self.images_frame.grid(row=0, column=0, sticky="nsew", padx=8, pady=8)

        bottom = tk.Frame(app, bg=WIN_FACE, bd=1, relief="solid")
        bottom.grid(row=2, column=0, sticky="nsew", padx=6, pady=(0, 6))
        bottom.grid_columnconfigure(0, weight=1)
        bottom.grid_rowconfigure(2, weight=1)
        bottom_bg = tk.Label(bottom, bd=0, highlightthickness=0)
        bottom_bg.place(x=0, y=0, relwidth=1, relheight=1)
        bottom_bg.lower()
        self._bind_gradient(
            bottom,
            bottom_bg,
            (
                (0.0, WIN_STATUS_TOP),
                (1.0, WIN_STATUS_BOTTOM),
            ),
        )

        status_top = tk.Frame(bottom, bg=WIN_FACE)
        status_top.grid(row=0, column=0, sticky="ew", padx=8, pady=(8, 2))
        status_top.grid_columnconfigure(3, weight=1)

        tk.Label(
            status_top,
            text=self._t("status_label"),
            bg=WIN_FACE,
            fg=WIN_BLACK,
            font=FONT_BOLD,
        ).grid(
            row=0, column=0, sticky="w"
        )
        tk.Label(
            status_top,
            textvariable=self.status_var,
            bg=WIN_WHITE,
            fg=WIN_BLACK,
            relief="solid",
            bd=1,
            font=FONT_BOLD,
            width=22,
            anchor="w",
        ).grid(row=0, column=1, sticky="w", padx=(8, 8))

        self.status_hotkey_label = tk.Label(
            status_top,
            textvariable=self.capture_status_var,
            bg=WIN_FACE,
            fg=WIN_BLACK,
            font=FONT_BOLD,
            anchor="w",
        )
        self.status_hotkey_label.grid(row=0, column=2, sticky="w", padx=(0, 8))

        tk.Label(
            bottom,
            textvariable=self.batch_summary_var,
            bg=WIN_FACE,
            fg=WIN_BLACK,
            anchor="w",
            font=FONT_BOLD,
        ).grid(row=1, column=0, sticky="ew", padx=8)

        log_group = self._make_group(bottom, self._t("log_group"))
        log_group.grid(row=2, column=0, sticky="nsew", padx=8, pady=(6, 8))
        log_group.grid_columnconfigure(0, weight=1)
        log_group.grid_rowconfigure(0, weight=1)

        self.log_box = tk.Text(
            log_group,
            height=6,
            bg=WIN_WHITE,
            fg=WIN_BLACK,
            relief="solid",
            bd=1,
            wrap="word",
            font=FONT_SMALL,
            insertbackground=WIN_BLACK,
        )
        self.log_box.grid(row=0, column=0, sticky="nsew", padx=8, pady=8)
        self.log_box.insert("end", f"{self._t('welcome_log')}\n")
        self.log_box.configure(state="disabled")

        # Canvas oculto para conservar la logica de progreso sin mostrar barras.
        self.progress_canvas = tk.Canvas(bottom, width=1, height=1, highlightthickness=0, bd=0)
        self.progress_fill = self.progress_canvas.create_rectangle(
            0, 0, 0, 1, fill=WIN_BLUE, outline=""
        )
        self.progress_text = self.progress_canvas.create_text(
            0, 0, text="0%", anchor="w", fill=WIN_WHITE, font=FONT_SMALL
        )

        self._make_corner_link(
            app,
            self._t("brand_credit"),
            SITE_URL,
            BRAND_LOGO_FILE,
            "sw",
        )
        self._make_corner_link(
            app,
            self._t("donations_link"),
            DONATION_URL,
            DONATION_LOGO_FILE,
            "se",
        )

    def _make_button(self, parent, text, command, width=12):
        return tk.Button(
            parent,
            text=text,
            command=command,
            width=width,
            bg=WIN_BUTTON,
            fg=WIN_BLACK,
            activebackground=WIN_BUTTON_ACTIVE,
            activeforeground=WIN_BLACK,
            disabledforeground="#7f8da0",
            relief="solid",
            bd=1,
            font=FONT_NORMAL,
            padx=4,
            pady=2,
        )

    def _make_group(self, parent, title):
        return tk.LabelFrame(
            parent,
            text=title,
            bg=WIN_LIGHT,
            fg=WIN_BLACK,
            bd=1,
            relief="solid",
            font=FONT_BOLD,
            labelanchor="nw",
            padx=2,
            pady=2,
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
            highlightcolor="#5b9dd9",
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
            font=FONT_NORMAL,
            highlightthickness=0,
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
            highlightcolor="#5b9dd9",
            wrap="word",
            font=FONT_NORMAL,
        )
        scrollbar = tk.Scrollbar(parent, orient="vertical", command=box.yview)
        box.configure(yscrollcommand=scrollbar.set)
        return box, scrollbar

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

    def _rebuild_ui(self):
        # Theme and language changes are applied by rebuilding the Tk layout
        # while preserving the current text boxes, logs, and selected section.
        active_section = self.section_var.get()
        snapshot = {
            "youtube_batch": self._snapshot_text_widget(
                getattr(self, "youtube_batch_box", None),
                "youtube_batch_placeholder",
            ),
            "list": self._snapshot_text_widget(getattr(self, "list_box", None), "list_placeholder"),
            "log": self._snapshot_text_widget(getattr(self, "log_box", None)),
        }

        self._close_search_settings()
        for child in self.winfo_children():
            child.destroy()

        self.ui_photo_refs.clear()
        self.card_photo_refs.clear()
        self.batch_canvas_window = None

        self.title(self._app_title())
        self.configure(bg=WIN_DESKTOP)
        self._build_ui()
        self._restore_text_widget(self.youtube_batch_box, snapshot["youtube_batch"], "youtube_batch_placeholder")
        self._restore_text_widget(self.list_box, snapshot["list"], "list_placeholder")
        self._restore_log_text(snapshot["log"])
        self._update_quality_options(self.mode_var.get())
        self._set_section(active_section)
        self._refresh_batch_view()
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
        badge = tk.Frame(parent, bg=WIN_GLASS_TOP, bd=1, relief="solid", cursor="hand2")
        badge.place(relx=0.01 if anchor == "sw" else 0.99, rely=0.99, anchor=anchor)

        image = self._load_badge_photo(image_path, (20, 20))
        if image is not None:
            tk.Label(badge, image=image, bg=WIN_GLASS_TOP, cursor="hand2").grid(
                row=0, column=0, padx=(5, 4), pady=3
            )

        tk.Label(
            badge,
            text=text,
            bg=WIN_GLASS_TOP,
            fg=WIN_LINK,
            font=FONT_SMALL,
            cursor="hand2",
        ).grid(row=0, column=1, padx=(0, 6), pady=3)

        for widget in (badge, *badge.winfo_children()):
            widget.bind("<Button-1>", lambda _event, target=url: self._open_external_url(target))

        return badge

    def _build_youtube_panel(self, parent):
        frame = tk.Frame(parent, bg=WIN_FACE)
        frame.grid_columnconfigure(0, weight=1)
        frame.grid_rowconfigure(0, weight=1)

        form = tk.Frame(frame, bg=WIN_FACE)
        form.grid(row=0, column=0, sticky="nsew")
        form.grid_columnconfigure(0, weight=3)
        form.grid_columnconfigure(1, weight=2)
        form.grid_rowconfigure(0, weight=1)

        left = self._make_group(form, self._t("youtube_data_group"))
        left.grid(row=0, column=0, rowspan=3, sticky="nsew", padx=(0, 6))
        left.grid_columnconfigure(0, weight=1)

        tk.Label(
            left,
            text=self._t("youtube_link_label"),
            bg=WIN_FACE,
            fg=WIN_BLACK,
            font=FONT_BOLD,
        ).grid(row=0, column=0, sticky="w", padx=8, pady=(8, 2))
        url_row = tk.Frame(left, bg=WIN_FACE)
        url_row.grid(row=1, column=0, sticky="ew", padx=8, pady=(0, 8))
        url_row.grid_columnconfigure(0, weight=1)

        self.url_entry = self._make_entry(url_row, self.url_var)
        self.url_entry.grid(row=0, column=0, sticky="ew")
        self.youtube_add_button = self._make_button(
            url_row, self._t("youtube_add_batch"), self._add_current_url_to_youtube_batch, width=16
        )
        self.youtube_add_button.grid(row=0, column=1, padx=(6, 0))

        youtube_batch_group = self._make_group(left, self._t("youtube_batch_group"))
        youtube_batch_group.grid(row=2, column=0, sticky="ew", padx=8, pady=(0, 8))
        youtube_batch_group.grid_columnconfigure(0, weight=1)

        self.youtube_autopaste_toggle = tk.Checkbutton(
            youtube_batch_group,
            text=self._t("youtube_hotkey_toggle"),
            variable=self.youtube_autopaste_var,
            command=lambda: self._toggle_autopaste("youtube"),
            bg=WIN_FACE,
            fg=WIN_BLACK,
            activebackground=WIN_FACE,
            activeforeground=WIN_BLACK,
            selectcolor=WIN_WHITE,
            anchor="w",
            font=FONT_NORMAL,
        )
        self.youtube_autopaste_toggle.grid(row=0, column=0, columnspan=2, sticky="w", padx=8, pady=(8, 6))

        self.youtube_batch_box, self.youtube_batch_scrollbar = self._make_text_box(
            youtube_batch_group, 7
        )
        self.youtube_batch_box.grid(row=1, column=0, sticky="nsew", padx=(8, 0))
        self.youtube_batch_scrollbar.grid(row=1, column=1, sticky="ns", padx=(0, 8))
        self.youtube_batch_box.insert("end", self._youtube_batch_placeholder())
        self.youtube_batch_box.configure(fg=WIN_DARK)
        self.youtube_batch_box.bind(
            "<FocusIn>",
            lambda _event: self._clear_text_placeholder(
                self.youtube_batch_box, self._youtube_batch_placeholder()
            ),
        )
        self.youtube_batch_box.bind(
            "<FocusOut>",
            lambda _event: self._restore_text_placeholder(
                self.youtube_batch_box, self._youtube_batch_placeholder()
            ),
        )

        youtube_batch_actions = tk.Frame(youtube_batch_group, bg=WIN_FACE)
        youtube_batch_actions.grid(row=2, column=0, columnspan=2, sticky="ew", padx=8, pady=8)
        youtube_batch_actions.grid_columnconfigure(0, weight=1)

        self.youtube_load_file_button = self._make_button(
            youtube_batch_actions, self._t("load_txt"), self._load_youtube_links_from_file, width=12
        )
        self.youtube_load_file_button.grid(row=0, column=1, padx=(6, 0))

        self.youtube_clear_button = self._make_button(
            youtube_batch_actions, self._t("clear_batch"), self._clear_youtube_batch, width=12
        )
        self.youtube_clear_button.grid(row=0, column=2, padx=(6, 0))

        self.youtube_batch_download_button = self._make_button(
            youtube_batch_actions, self._t("download_batch"), self._start_youtube_batch_download, width=14
        )
        self.youtube_batch_download_button.grid(row=0, column=3, padx=(6, 0))

        settings_row = tk.Frame(left, bg=WIN_FACE)
        settings_row.grid(row=3, column=0, sticky="ew", padx=8, pady=(0, 8))
        settings_row.grid_columnconfigure(0, weight=1)
        settings_row.grid_columnconfigure(1, weight=0)

        mode_group = self._make_group(settings_row, self._t("format_group"))
        mode_group.grid(row=0, column=0, sticky="ew", padx=(0, 6))

        self.video_radio = tk.Radiobutton(
            mode_group,
            text="Video",
            variable=self.mode_var,
            value="Video",
            bg=WIN_FACE,
            fg=WIN_BLACK,
            activebackground=WIN_FACE,
            activeforeground=WIN_BLACK,
            selectcolor=WIN_WHITE,
            anchor="w",
            command=lambda: self._update_quality_options("Video"),
            font=FONT_NORMAL,
        )
        self.video_radio.grid(row=0, column=0, sticky="w", padx=8, pady=4)

        self.audio_radio = tk.Radiobutton(
            mode_group,
            text="Audio",
            variable=self.mode_var,
            value="Audio",
            bg=WIN_FACE,
            fg=WIN_BLACK,
            activebackground=WIN_FACE,
            activeforeground=WIN_BLACK,
            selectcolor=WIN_WHITE,
            anchor="w",
            command=lambda: self._update_quality_options("Audio"),
            font=FONT_NORMAL,
        )
        self.audio_radio.grid(row=0, column=1, sticky="w", padx=8, pady=4)

        quality_group = self._make_group(settings_row, self._t("quality_group"))
        quality_group.grid(row=0, column=1, sticky="ns")
        self.quality_menu = self._make_option_menu(
            quality_group, self.quality_var, [self._t("quality_best")]
        )
        self.quality_menu.grid(row=0, column=0, sticky="w", padx=8, pady=8)

        tk.Label(
            left,
            text=self._t("output_folder"),
            bg=WIN_FACE,
            fg=WIN_BLACK,
            font=FONT_BOLD,
        ).grid(
            row=4, column=0, sticky="w", padx=8, pady=(0, 2)
        )
        folder_row = tk.Frame(left, bg=WIN_FACE)
        folder_row.grid(row=5, column=0, sticky="ew", padx=8, pady=(0, 8))
        folder_row.grid_columnconfigure(0, weight=1)

        self.folder_entry = self._make_entry(folder_row, self.output_var)
        self.folder_entry.grid(row=0, column=0, sticky="ew")
        self.browse_button = self._make_button(
            folder_row, self._t("browse"), lambda: self._pick_folder("youtube"), width=12
        )
        self.browse_button.grid(row=0, column=1, padx=(6, 0))

        actions_row = tk.Frame(left, bg=WIN_FACE)
        actions_row.grid(row=6, column=0, sticky="ew", padx=8, pady=(2, 8))
        actions_row.grid_columnconfigure(0, weight=1)

        self.youtube_open_folder_button = self._make_button(
            actions_row, self._t("open_folder"), self._open_output_folder, width=16
        )
        self.youtube_open_folder_button.grid(row=0, column=1, padx=(6, 0))

        self.download_button = self._make_button(
            actions_row, self._t("download"), self._start_youtube_download, width=14
        )
        self.download_button.grid(row=0, column=2, padx=(6, 0))

        info = self._make_group(form, self._t("how_to_use"))
        info.grid(row=0, column=1, sticky="nsew")
        tk.Label(
            info,
            text=self._t("youtube_how_to_use_text"),
            bg=WIN_WHITE,
            fg=WIN_BLACK,
            justify="left",
            anchor="nw",
            relief="sunken",
            bd=2,
            font=FONT_NORMAL,
        ).grid(row=0, column=0, sticky="nsew", padx=8, pady=8)

        self._refresh_youtube_batch_summary()
        return frame

    def _build_images_panel(self, parent):
        frame = tk.Frame(parent, bg=WIN_FACE)
        frame.grid_columnconfigure(0, weight=0)
        frame.grid_columnconfigure(1, weight=1)
        frame.grid_rowconfigure(0, weight=1)

        left = tk.Frame(frame, bg=WIN_FACE)
        left.grid(row=0, column=0, sticky="nsw", padx=(0, 8))
        left.grid_columnconfigure(0, weight=1)

        search_group = self._make_group(left, self._t("search_group"))
        search_group.grid(row=0, column=0, sticky="ew", pady=(0, 6))
        search_group.grid_columnconfigure(0, weight=1)

        tk.Label(
            search_group,
            text=self._t("search_header_text"),
            bg=WIN_WHITE,
            fg=WIN_BLACK,
            justify="left",
            anchor="w",
            relief="sunken",
            bd=2,
            font=FONT_NORMAL,
        ).grid(row=0, column=0, columnspan=4, sticky="ew", padx=8, pady=(8, 6))

        tk.Label(
            search_group,
            text=self._t("source_label"),
            bg=WIN_FACE,
            fg=WIN_BLACK,
            font=FONT_BOLD,
        ).grid(
            row=1, column=0, sticky="w", padx=8, pady=(0, 2)
        )

        self.search_source_menu = self._make_option_menu(
            search_group,
            self.search_source_var,
            SEARCH_SOURCES,
            command=self._on_search_source_change,
        )
        self.search_source_menu.grid(row=1, column=1, sticky="w", padx=8, pady=(0, 2))

        tk.Label(
            search_group,
            text=self._t("add_to_list"),
            bg=WIN_FACE,
            fg=WIN_BLACK,
            font=FONT_BOLD,
        ).grid(row=2, column=0, sticky="w", padx=8, pady=(4, 2))

        fill_row = tk.Frame(search_group, bg=WIN_FACE)
        fill_row.grid(row=3, column=0, columnspan=4, sticky="ew", padx=8, pady=(0, 8))
        fill_row.grid_columnconfigure(0, weight=1)

        self.list_entry = self._make_entry(fill_row, self.list_entry_var)
        self.list_entry.grid(row=0, column=0, sticky="ew")

        self.add_list_item_button = self._make_button(
            fill_row, self._t("add"), self._add_list_entry, width=10
        )
        self.add_list_item_button.grid(row=0, column=1, padx=(6, 0))

        tk.Label(
            search_group,
            text=self._t("current_list"),
            bg=WIN_FACE,
            fg=WIN_BLACK,
            font=FONT_BOLD,
        ).grid(row=4, column=0, sticky="w", padx=8, pady=(0, 2))

        self.list_box, self.list_scrollbar = self._make_text_box(search_group, 12)
        self.list_box.grid(row=5, column=0, columnspan=3, sticky="nsew", padx=(8, 0))
        self.list_scrollbar.grid(row=5, column=3, sticky="ns", padx=(0, 8))
        self.list_box.insert("end", self._list_placeholder())
        self.list_box.configure(fg=WIN_DARK)

        query_actions = tk.Frame(search_group, bg=WIN_FACE)
        query_actions.grid(row=6, column=0, columnspan=4, sticky="ew", padx=8, pady=8)
        query_actions.grid_columnconfigure(0, weight=1)

        self.load_query_file_button = self._make_button(
            query_actions, self._t("load_txt"), self._load_queries_from_file, width=12
        )
        self.load_query_file_button.grid(row=0, column=1, padx=(6, 0))

        self.search_queries_button = self._make_button(
            query_actions, self._t("search_images"), self._start_query_search, width=16
        )
        self.search_queries_button.grid(row=0, column=2, padx=(6, 0))

        self.clear_list_button = self._make_button(
            query_actions, self._t("clear_batch"), self._clear_input_list, width=12
        )
        self.clear_list_button.grid(row=0, column=3, padx=(6, 0))

        paste_group = self._make_group(left, self._t("quick_paste_group"))
        paste_group.grid(row=1, column=0, sticky="ew")
        paste_group.grid_columnconfigure(0, weight=1)

        self.images_autopaste_toggle = tk.Checkbutton(
            paste_group,
            text=self._t("youtube_hotkey_toggle"),
            variable=self.images_autopaste_var,
            command=lambda: self._toggle_autopaste("imagenes"),
            bg=WIN_FACE,
            fg=WIN_BLACK,
            activebackground=WIN_FACE,
            activeforeground=WIN_BLACK,
            selectcolor=WIN_WHITE,
            anchor="w",
            font=FONT_NORMAL,
        )
        self.images_autopaste_toggle.grid(row=0, column=0, sticky="w", padx=8, pady=(8, 6))

        paste_actions = tk.Frame(paste_group, bg=WIN_FACE)
        paste_actions.grid(row=1, column=0, sticky="ew", padx=8, pady=(0, 8))
        paste_actions.grid_columnconfigure(0, weight=1)

        self.paste_now_button = self._make_button(
            paste_actions, self._t("paste_now"), self._paste_clipboard_content, width=16
        )
        self.paste_now_button.grid(row=0, column=1, padx=(6, 0))

        self.clear_batch_button = self._make_button(
            paste_actions, self._t("clear_batch"), self._clear_batch_items, width=14
        )
        self.clear_batch_button.grid(row=0, column=2, padx=(6, 0))

        right = tk.Frame(frame, bg=WIN_FACE)
        right.grid(row=0, column=1, sticky="nsew")
        right.grid_columnconfigure(0, weight=1)
        right.grid_rowconfigure(0, weight=1)

        batch_group = self._make_group(right, self._t("final_image_batch"))
        batch_group.grid(row=0, column=0, sticky="nsew")
        batch_group.grid_columnconfigure(0, weight=1)
        batch_group.grid_rowconfigure(1, weight=1)

        tk.Label(
            batch_group,
            text=self._t("final_batch_text"),
            bg=WIN_WHITE,
            fg=WIN_BLACK,
            justify="left",
            anchor="w",
            relief="sunken",
            bd=2,
            font=FONT_NORMAL,
        ).grid(row=0, column=0, columnspan=2, sticky="ew", padx=8, pady=(8, 6))

        batch_canvas_wrap = tk.Frame(batch_group, bg=WIN_FACE)
        batch_canvas_wrap.grid(row=1, column=0, sticky="nsew", padx=8, pady=(0, 8))
        batch_canvas_wrap.grid_columnconfigure(0, weight=1)
        batch_canvas_wrap.grid_rowconfigure(0, weight=1)

        self.batch_canvas = tk.Canvas(
            batch_canvas_wrap,
            bg=WIN_WHITE,
            bd=2,
            relief="sunken",
            highlightthickness=0,
        )
        self.batch_canvas.grid(row=0, column=0, sticky="nsew")

        self.batch_scrollbar = tk.Scrollbar(
            batch_canvas_wrap, orient="vertical", command=self.batch_canvas.yview
        )
        self.batch_scrollbar.grid(row=0, column=1, sticky="ns")
        self.batch_canvas.configure(yscrollcommand=self.batch_scrollbar.set)

        self.batch_inner = tk.Frame(self.batch_canvas, bg=WIN_WHITE)
        self.batch_canvas_window = self.batch_canvas.create_window(
            (0, 0), window=self.batch_inner, anchor="nw"
        )
        self.batch_inner.bind("<Configure>", self._update_batch_scroll_region)
        self.batch_canvas.bind("<Configure>", self._resize_batch_inner)
        self.batch_canvas.bind_all("<MouseWheel>", self._on_batch_mousewheel)

        download_group = self._make_group(right, self._t("save_group"))
        download_group.grid(row=1, column=0, sticky="ew", pady=(6, 0))
        download_group.grid_columnconfigure(0, weight=1)

        folder_row = tk.Frame(download_group, bg=WIN_FACE)
        folder_row.grid(row=0, column=0, sticky="ew", padx=8, pady=(8, 6))
        folder_row.grid_columnconfigure(0, weight=1)

        self.image_folder_entry = self._make_entry(folder_row, self.image_output_var)
        self.image_folder_entry.grid(row=0, column=0, sticky="ew")
        self.image_browse_button = self._make_button(
            folder_row, self._t("browse"), lambda: self._pick_folder("imagenes"), width=12
        )
        self.image_browse_button.grid(row=0, column=1, padx=(6, 0))

        actions_row = tk.Frame(download_group, bg=WIN_FACE)
        actions_row.grid(row=1, column=0, sticky="ew", padx=8, pady=(0, 8))
        actions_row.grid_columnconfigure(0, weight=1)

        self.image_open_folder_button = self._make_button(
            actions_row, self._t("open_folder"), self._open_output_folder, width=16
        )
        self.image_open_folder_button.grid(row=0, column=1, padx=(6, 0))

        self.image_download_button = self._make_button(
            actions_row, self._t("download_batch"), self._start_image_download, width=18
        )
        self.image_download_button.grid(row=0, column=2, padx=(6, 0))

        self._refresh_batch_view()
        self._apply_search_source_state()
        return frame

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
            self.youtube_batch_box,
            self.folder_entry,
            self.image_folder_entry,
            self.list_entry,
            self.list_box,
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
            bg=WIN_WHITE,
            fg=WIN_BLACK,
            justify="left",
            anchor="w",
            relief="sunken",
            bd=2,
            font=FONT_NORMAL,
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
            bg=WIN_WHITE,
            fg=WIN_BLACK,
            justify="left",
            anchor="w",
            relief="sunken",
            bd=2,
            font=FONT_NORMAL,
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
        self.youtube_tab_button.configure(
            relief="solid",
            bg=WIN_TAB_ACTIVE if selected == "youtube" else WIN_TAB_IDLE,
        )
        self.images_tab_button.configure(
            relief="solid",
            bg=WIN_TAB_ACTIVE if selected == "imagenes" else WIN_TAB_IDLE,
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

    def _pick_folder(self, target):
        current = self.output_var.get() if target == "youtube" else self.image_output_var.get()
        selected = filedialog.askdirectory(initialdir=current or str(Path.home()))
        if not selected:
            return

        if target == "youtube":
            self.output_var.set(selected)
        else:
            self.image_output_var.set(selected)

    def _append_text_block(self, text_widget, new_text, placeholder):
        current = text_widget.get("1.0", "end").strip()
        text_widget.delete("1.0", "end")

        if current and current != placeholder:
            text_widget.insert("end", f"{current}\n{new_text}")
        else:
            text_widget.insert("end", new_text)

    def _parse_multiline_values(self, text_widget, placeholder, dedupe=True):
        raw_text = text_widget.get("1.0", "end").strip()
        if not raw_text or raw_text == placeholder:
            return []

        values = []
        seen = set()
        for line in raw_text.splitlines():
            value = line.strip()
            if not value or value == placeholder:
                continue
            if dedupe and value in seen:
                continue
            seen.add(value)
            values.append(value)
        return values

    def _append_to_input_list(self, text):
        cleaned = text.strip()
        if not cleaned:
            return
        self._append_text_block(self.list_box, cleaned, self._list_placeholder())
        self.list_box.configure(fg=WIN_BLACK)

    def _append_to_youtube_batch(self, text):
        cleaned = text.strip()
        if not cleaned:
            return
        self._append_text_block(
            self.youtube_batch_box,
            cleaned,
            self._youtube_batch_placeholder(),
        )
        self.youtube_batch_box.configure(fg=WIN_BLACK)
        self._refresh_youtube_batch_summary()

    def _add_current_url_to_youtube_batch(self):
        value = self.url_var.get().strip()
        if not value:
            messagebox.showwarning(self._app_title(), self._t("youtube_missing_link"))
            return
        self._append_to_youtube_batch(value)
        self.url_var.set("")
        self._log(self._t("youtube_link_added_log"))

    def _clear_youtube_batch(self):
        if self._is_busy():
            return
        self.youtube_batch_box.delete("1.0", "end")
        self.youtube_batch_box.insert("end", self._youtube_batch_placeholder())
        self.youtube_batch_box.configure(fg=WIN_DARK)
        self._refresh_youtube_batch_summary()

    def _collect_youtube_batch_urls(self):
        entries = self._parse_multiline_values(
            self.youtube_batch_box, self._youtube_batch_placeholder(), dedupe=False
        )
        urls = []
        for entry in entries:
            urls.extend(self._extract_urls(entry))
        return urls

    def _paste_clipboard_to_youtube_batch(self, show_empty_message=True):
        try:
            clipboard_text = self.clipboard_get().strip()
        except tk.TclError:
            clipboard_text = ""

        urls = self._extract_urls(clipboard_text)
        if urls:
            self._append_to_youtube_batch("\n".join(urls))
            self.status_var.set(self._t("youtube_batch_updated_status"))
            self.detail_var.set(self._t("youtube_batch_updated_detail", count=len(urls)))
            self._log(self._t("youtube_batch_updated_log", count=len(urls)))
            return True

        if clipboard_text:
            self._append_to_youtube_batch(clipboard_text)
            self.status_var.set(self._t("youtube_batch_updated_status"))
            self.detail_var.set(self._t("youtube_batch_updated_text_detail"))
            self._log(self._t("youtube_batch_updated_text_log"))
            return True

        if show_empty_message:
            messagebox.showinfo(self._app_title(), self._t("clipboard_no_text"))
        return False

    def _refresh_youtube_batch_summary(self):
        total = len(self._collect_youtube_batch_urls()) if hasattr(self, "youtube_batch_box") else 0
        self.batch_summary_var.set(self._t("youtube_batch_summary", total=total))

    def _add_list_entry(self):
        value = self.list_entry_var.get().strip()
        if not value:
            return
        self._append_to_input_list(value)
        self.list_entry_var.set("")

    def _clear_input_list(self):
        if self._is_busy():
            return
        self.list_box.delete("1.0", "end")
        self.list_box.insert("end", self._list_placeholder())
        self.list_box.configure(fg=WIN_DARK)
        self.list_entry_var.set("")

    def _collect_search_entries(self):
        return self._parse_multiline_values(self.list_box, self._list_placeholder(), dedupe=False)

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

        self._append_to_input_list(content)
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

        self._append_to_youtube_batch(content)
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
            self.clear_batch_button,
            self.image_folder_entry,
            self.image_browse_button,
            self.image_open_folder_button,
            self.image_download_button,
        ):
            widget.configure(state=state)

        self.list_box.configure(state=state)
        self.youtube_batch_box.configure(state=state)
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
        self, mode, quality_value, quality_label, output_folder, ffmpeg_available, hook
    ):
        options = {
            "noplaylist": True,
            "outtmpl": str(output_folder / "%(title).180B [%(id)s].%(ext)s"),
            "progress_hooks": [hook],
            "quiet": True,
            "no_warnings": True,
        }

        if mode == "Video":
            options["format"] = self._build_video_format(quality_value, ffmpeg_available)
            if ffmpeg_available:
                options["merge_output_format"] = "mp4"
        else:
            options["format"] = "bestaudio/best"
            if ffmpeg_available:
                target_quality = "320" if quality_value == "best" else quality_value
                options["postprocessors"] = [
                    {
                        "key": "FFmpegExtractAudio",
                        "preferredcodec": "mp3",
                        "preferredquality": target_quality,
                    }
                ]
        return options

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
                    (
                        "log",
                        "ffmpeg no esta instalado. Se descargara el audio original disponible.",
                    )
                )

    def _download_youtube_item(
        self, url, mode, quality_value, quality_label, output_folder, ffmpeg_available, hook
    ):
        options = self._build_youtube_options(
            mode, quality_value, quality_label, output_folder, ffmpeg_available, hook
        )
        with YoutubeDL(options) as ydl:
            info = ydl.extract_info(url, download=True)
        return info.get("title", "Archivo")

    def _download_youtube_worker(self, url, mode, quality_value, quality_label, output_folder):
        ffmpeg_available = shutil.which("ffmpeg") is not None
        self._log_youtube_mode_details(mode, quality_value, quality_label, ffmpeg_available)

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
                url, mode, quality_value, quality_label, output_folder, ffmpeg_available, hook
            )
            self.worker_queue.put(("log", f"Descarga completada: {title}"))
            self.worker_queue.put(("status", "Descarga terminada."))
            self.worker_queue.put(
                ("detail", f"{mode} | {quality_label} | Guardado en {output_folder}")
            )
            self.worker_queue.put(("done", f"Se guardo en: {output_folder}"))
        except DownloadError as error:
            self.worker_queue.put(("error", f"No se pudo descargar: {error}"))
        except Exception as error:
            self.worker_queue.put(("error", f"Ocurrio un error inesperado: {error}"))

    def _download_youtube_batch_worker(self, urls, mode, quality_value, quality_label, output_folder):
        ffmpeg_available = shutil.which("ffmpeg") is not None
        self._log_youtube_mode_details(mode, quality_value, quality_label, ffmpeg_available)

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
                        ffmpeg_available,
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

    def _update_batch_scroll_region(self, _event=None):
        self.batch_canvas.configure(scrollregion=self.batch_canvas.bbox("all"))

    def _resize_batch_inner(self, event):
        if self.batch_canvas_window is not None:
            self.batch_canvas.itemconfigure(self.batch_canvas_window, width=event.width)

    def _on_batch_mousewheel(self, event):
        if self.section_var.get() == "imagenes":
            self.batch_canvas.yview_scroll(int(-1 * (event.delta / 120)), "units")

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

    def _placeholder_preview(self, text):
        image = Image.new("RGB", (220, 150), WIN_LIGHT)
        return image

    def _refresh_batch_view(self):
        for widget in self.batch_inner.winfo_children():
            widget.destroy()

        self.card_photo_refs.clear()
        self._refresh_batch_summary()

        if not self.image_items:
            tk.Label(
                self.batch_inner,
                text=self._t("empty_batch_text"),
                bg=WIN_WHITE,
                fg=WIN_BLACK,
                font=FONT_NORMAL,
                justify="left",
                anchor="w",
            ).grid(row=0, column=0, padx=12, pady=24, sticky="w")
            self._update_batch_scroll_region()
            return

        for column in range(2):
            self.batch_inner.grid_columnconfigure(column, weight=1)

        for index, item in enumerate(self.image_items):
            row = index // 2
            column = index % 2

            card = tk.Frame(self.batch_inner, bg=WIN_FACE, bd=2, relief="groove")
            card.grid(row=row, column=column, sticky="nsew", padx=8, pady=8)
            card.grid_columnconfigure(0, weight=1)

            actions = tk.Frame(card, bg=WIN_FACE)
            actions.grid(row=0, column=0, sticky="ew", padx=6, pady=(6, 2))
            actions.grid_columnconfigure(0, weight=1)

            replace_button = self._make_button(
                actions,
                self._t("replace_button"),
                lambda item_id=item["id"]: self._start_replace_item(item_id),
                width=8,
            )
            replace_button.grid(row=0, column=1, padx=(4, 0))
            if item["kind"] not in ("pexels", "flickr"):
                replace_button.configure(state="disabled")

            remove_button = self._make_button(
                actions,
                self._t("remove_button"),
                lambda item_id=item["id"]: self._remove_batch_item(item_id),
                width=8,
            )
            remove_button.grid(row=0, column=2, padx=(4, 0))

            preview_image = item.get("preview_image") or self._placeholder_preview(item["title"])
            thumb = preview_image.copy()
            thumb.thumbnail((220, 150))
            photo = ImageTk.PhotoImage(thumb)
            self.card_photo_refs.append(photo)

            image_label = tk.Label(
                card,
                image=photo,
                bg=WIN_WHITE,
                bd=2,
                relief="sunken",
                width=220,
                height=150,
            )
            image_label.grid(row=1, column=0, padx=6, pady=(2, 4))

            tk.Label(
                card,
                text=item["title"],
                bg=WIN_FACE,
                fg=WIN_BLACK,
                font=FONT_BOLD,
                justify="left",
                wraplength=220,
                anchor="w",
            ).grid(row=2, column=0, sticky="ew", padx=6)

            tk.Label(
                card,
                text=item["subtitle"],
                bg=WIN_FACE,
                fg=WIN_BLACK,
                font=FONT_SMALL,
                justify="left",
                wraplength=220,
                anchor="w",
            ).grid(row=3, column=0, sticky="ew", padx=6, pady=(2, 6))

        self._update_batch_scroll_region()

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

        self._refresh_batch_view()

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
        self._refresh_batch_view()
        self._log(self._t("removed_from_batch_log", title=removed["title"]))

    def _clear_batch_items(self):
        if self._is_busy():
            return

        self.image_items.clear()
        self._refresh_batch_view()
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
            self._append_to_input_list(clipboard_text)
            self._log(self._t("clipboard_list_log"))
            self.status_var.set(self._t("list_updated_status"))
            self.detail_var.set(self._t("list_updated_detail"))
            return True

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

    def _save_image_item(self, item, output_folder, index, total):
        if item["kind"] == "clipboard":
            file_path = ensure_unique_path(output_folder / item["filename_hint"])
            image_to_save = item["image_data"].copy()
            if image_to_save.mode not in ("RGB", "RGBA", "L"):
                if "A" in image_to_save.getbands():
                    image_to_save = image_to_save.convert("RGBA")
                else:
                    image_to_save = image_to_save.convert("RGB")

            image_to_save.save(file_path, format="PNG")
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

        return file_path

    def _start_image_download(self):
        if not self.image_items:
            messagebox.showwarning(self._app_title(), self._t("image_batch_empty_warning"))
            return

        if self._is_busy():
            messagebox.showinfo(self._app_title(), self._t("operation_busy"))
            return

        output_folder = Path(self.image_output_var.get().strip() or DEFAULT_IMAGE_FOLDER)
        output_folder.mkdir(parents=True, exist_ok=True)

        snapshot = []
        for item in self.image_items:
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
            args=(snapshot, output_folder),
            daemon=True,
        )
        self.active_thread.start()

    def _download_images_worker(self, items, output_folder):
        total = len(items)
        downloaded_count = 0
        failed = []

        try:
            for index, item in enumerate(items, start=1):
                self.worker_queue.put(("status", f"Guardando imagen {index}/{total}..."))
                self.worker_queue.put(("detail", item["title"]))

                try:
                    file_path = self._save_image_item(item, output_folder, index, total)
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
                elif kind == "replace_item":
                    index = self._find_item_index(payload["id"])
                    if index is not None:
                        self.image_items[index] = payload
                        self._refresh_batch_view()
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
