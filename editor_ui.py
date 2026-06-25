"""Editor panel UI for FissileKit."""

from __future__ import annotations

import tkinter as tk
from pathlib import Path
from tkinter import colorchooser, filedialog, messagebox, ttk

from PIL import Image, ImageTk

import conversion
import editor
import editor_icons
import editor_ops
import editor_cursors
import editor_text

EDITOR_THEME = {
    "bg": "#151515",
    "panel": "#202020",
    "surface": "#2a2a2a",
    "border": "#3a3a3a",
    "text": "#e6e6e6",
    "muted": "#9ca3af",
    "accent": "#60a5fa",
    "canvas": "#121212",
    "btn": "#303030",
    "btn_active": "#454545",
    "btn_text": "#f3f4f6",
}


class EditorController:
    HISTORY_WIDTH = 220
    TOOLBAR_ICON_SIZE = 40
    DRAW_TOOL_ICON_SIZE = 28
    DRAW_SLIDER_LENGTH = 100
    DRAW_SLIDER_WIDTH = 22
    DRAW_COLOR_SWATCH_SIZE = 32
    SHAPE_TOOL_ICON_SIZE = 26

    def __init__(self, app):
        self.app = app
        self.session = editor.EditorSession()
        self.active_tool = None
        self.tool_buttons: dict[str, tk.Button] = {}
        self.canvas_photo = None
        self._preview_dirty = True
        self._configure_after_id = None
        self._icon_photos: list[ImageTk.PhotoImage] = []
        self.stroke_active = False
        self.stroke_points: list[tuple[float, float]] = []
        self.last_point = None
        self.crop_box = None
        self.crop_handle = None
        self.crop_drag_origin = None
        self.crop_drag_start = None
        self.crop_drag_active = False
        self.crop_drag_phase = None
        self.crop_mode_buttons: dict[str, tk.Button] = {}
        self.crop_aspect_buttons: dict[str, tk.Button] = {}
        self.draw_mode_buttons: dict[str, tk.Button] = {}
        self._draw_return_mode = "pencil"
        self._eyedropper_feedback_after_id = None
        self._crop_interacting = False
        self._crop_overlay_after_id = None
        self._rotate_dragging = False
        self._rotate_start_pointer_angle = 0.0
        self._rotate_wheel_angle = 0.0
        self._rotate_angle_at_drag_start = 0.0
        self._rotate_drag_display: Image.Image | None = None
        self._rotate_drag_photo: ImageTk.PhotoImage | None = None
        self._rotate_refresh_after_id = None
        self.resize_mode_buttons: dict[str, tk.Button] = {}
        self.resize_preset_buttons: dict[str, tk.Button] = {}
        self.canvas_resolution_buttons: dict[str, tk.Button] = {}
        self.canvas_aspect_buttons: dict[str, tk.Button] = {}
        self._resize_source_size: tuple[int, int] | None = None
        self._canvas_source_image: Image.Image | None = None
        self._canvas_source_stroke: Image.Image | None = None
        self._canvas_placement_x = 0.0
        self._canvas_placement_y = 0.0
        self._canvas_content_scale = 1.0
        self._canvas_dragging = False
        self._canvas_handle_resizing = False
        self._canvas_handle = None
        self._canvas_box_origin = None
        self._canvas_handle_start = None
        self._canvas_drag_origin: tuple[float, float] | None = None
        self._canvas_drag_canvas_start: tuple[float, float] | None = None
        self._canvas_placement_origin: tuple[float, float] | None = None
        self._canvas_refresh_after_id = None
        self._canvas_wheel_after_id = None
        self._canvas_drag_photo: ImageTk.PhotoImage | None = None
        self._canvas_scaled_base: Image.Image | None = None
        self._canvas_scaled_stroke: Image.Image | None = None
        self._canvas_scaled_at_scale: float | None = None
        self.shape_start_canvas = None
        self.shape_start_image = None
        self.shape_dragging = False
        self.shape_curve_points: list[tuple[float, float]] = []
        self.shape_kind_buttons: dict[str, tk.Button] = {}
        self.shape_fill_color = "#e74c3c"
        self.shape_stroke_color = "#ffffff"
        self._shape_ignore_next_click = False
        self._text_selected_id: str | None = None
        self._text_editing_id: str | None = None
        self._text_edit_widget: tk.Text | None = None
        self._text_edit_frame: tk.Frame | None = None
        self._text_edit_window = None
        self._text_dragging = False
        self._text_drag_mode: str | None = None
        self._text_drag_handle: str | None = None
        self._text_drag_origin: tuple[float, float] | None = None
        self._text_drag_box_origin: tuple[float, float, float, float] | None = None
        self._text_drag_size_origin = 0.0
        self._text_drag_object_origin: tuple[float, float] | None = None
        self._text_pending_move_id: str | None = None
        self._text_format_buttons: dict[str, tk.Button] = {}
        self._text_border_row: tk.Frame | None = None
        self.text_color = "#ffffff"
        self.text_border_color = "#000000"
        self.magic_color = None
        self.draw_color = "#e74c3c"
        self._widgets: dict[str, tk.Variable] = {}

    def t(self, key, **kwargs):
        return self.app._t(key, **kwargs)

    def build_panel(self, parent):
        frame = tk.Frame(parent, bg=EDITOR_THEME["bg"])
        frame.grid_columnconfigure(0, weight=0, minsize=self.HISTORY_WIDTH)
        frame.grid_columnconfigure(1, weight=1)
        frame.grid_rowconfigure(0, weight=1)

        history = tk.LabelFrame(
            frame,
            text=f"  {self.t('editor_history')}  ",
            bg=EDITOR_THEME["panel"],
            fg=EDITOR_THEME["text"],
            bd=1,
            relief="solid",
            highlightbackground=EDITOR_THEME["border"],
            font=self.app.FONT_NORMAL if hasattr(self.app, "FONT_NORMAL") else ("Segoe UI", 10),
            labelanchor="n",
        )
        history.grid(row=0, column=0, sticky="ns", padx=(0, 8))
        history.grid_rowconfigure(1, weight=1)
        history.grid_columnconfigure(0, weight=1)
        history.configure(width=self.HISTORY_WIDTH)

        folder_row = tk.Frame(history, bg=EDITOR_THEME["panel"])
        folder_row.grid(row=0, column=0, sticky="ew", padx=6, pady=(8, 6))
        folder_row.grid_columnconfigure(0, weight=1)
        self.folder_entry = self._entry(folder_row, self.app.editor_folder_var)
        self.folder_entry.grid(row=0, column=0, sticky="ew")
        browse = self._button(folder_row, self.t("change_folder"), lambda: self.app._pick_folder("editor"), width=7)
        browse.grid(row=1, column=0, sticky="ew", pady=(4, 0))
        refresh = self._button(folder_row, self.t("editor_refresh"), self.refresh_history, width=7)
        refresh.grid(row=2, column=0, sticky="ew", pady=(4, 0))

        tree_wrap = tk.Frame(history, bg=EDITOR_THEME["panel"])
        tree_wrap.grid(row=1, column=0, sticky="nsew", padx=6, pady=(0, 8))
        tree_wrap.grid_columnconfigure(0, weight=1)
        tree_wrap.grid_rowconfigure(0, weight=1)
        style = ttk.Style()
        style.theme_use("clam")
        style.configure(
            "Editor.Treeview",
            background=EDITOR_THEME["surface"],
            fieldbackground=EDITOR_THEME["surface"],
            foreground=EDITOR_THEME["text"],
            bordercolor=EDITOR_THEME["border"],
            lightcolor=EDITOR_THEME["border"],
            darkcolor=EDITOR_THEME["border"],
            rowheight=22,
        )
        style.map("Editor.Treeview", background=[("selected", EDITOR_THEME["accent"])])
        scroll = tk.Scrollbar(tree_wrap, orient="vertical")
        scroll.grid(row=0, column=1, sticky="ns")
        self.history_tree = ttk.Treeview(
            tree_wrap,
            show="tree",
            selectmode="browse",
            yscrollcommand=scroll.set,
            style="Editor.Treeview",
        )
        self.history_tree.grid(row=0, column=0, sticky="nsew")
        scroll.configure(command=self.history_tree.yview)
        self.history_tree.bind("<<TreeviewSelect>>", self._on_history_select)
        self.history_items: dict[str, Path] = {}

        workspace = tk.Frame(frame, bg=EDITOR_THEME["bg"])
        workspace.grid(row=0, column=1, sticky="nsew")
        workspace.grid_rowconfigure(1, weight=1)
        workspace.grid_columnconfigure(0, weight=1)

        self.toolbar_host = tk.Frame(workspace, bg=EDITOR_THEME["bg"])
        self.toolbar_host.grid(row=0, column=0, sticky="ew", pady=(0, 8))
        self.toolbar_host.grid_columnconfigure(0, weight=1)

        self.main_toolbar = tk.Frame(self.toolbar_host, bg=EDITOR_THEME["bg"])
        self.main_toolbar.grid(row=0, column=0, sticky="ew")
        self.sub_toolbar = tk.Frame(self.toolbar_host, bg=EDITOR_THEME["bg"])
        self.sub_toolbar_content = tk.Frame(self.sub_toolbar, bg=EDITOR_THEME["bg"])
        self.sub_toolbar_content.pack(side="left", fill="x", expand=True)
        self.sub_toolbar_actions = tk.Frame(self.sub_toolbar, bg=EDITOR_THEME["bg"])
        self.sub_toolbar_actions.pack(side="right")

        tool_specs = (
            ("crop", "editor_tool_crop"),
            ("rotate", "editor_tool_rotate"),
            ("resize", "editor_tool_resize"),
            ("draw", "editor_tool_draw"),
            ("shape", "editor_tool_shapes"),
            ("text", "editor_tool_text"),
        )
        toolbar_actions = (
            ("undo", "editor_tool_undo", self.undo),
            ("redo", "editor_tool_redo", self.redo),
        )
        col = 0
        for key, label_key in tool_specs:
            self.main_toolbar.grid_columnconfigure(col, weight=1, uniform="editor_tools")
            button = self._icon_button(
                self.main_toolbar,
                key,
                lambda tool=key: self.enter_tool(tool),
                size=self.TOOLBAR_ICON_SIZE,
                tooltip_key=label_key,
            )
            button.grid(row=0, column=col, sticky="nsew", padx=(0 if col == 0 else 3, 0), pady=2)
            self.tool_buttons[key] = button
            col += 1
        for key, label_key, command in toolbar_actions:
            self.main_toolbar.grid_columnconfigure(col, weight=1, uniform="editor_tools")
            button = self._icon_button(
                self.main_toolbar,
                key,
                command,
                size=self.TOOLBAR_ICON_SIZE,
                tooltip_key=label_key,
            )
            button.grid(row=0, column=col, sticky="nsew", padx=3, pady=2)
            col += 1

        canvas_wrap = tk.Frame(workspace, bg=EDITOR_THEME["border"], bd=0)
        canvas_wrap.grid(row=1, column=0, sticky="nsew", pady=(0, 8))
        canvas_wrap.grid_columnconfigure(0, weight=1)
        canvas_wrap.grid_rowconfigure(0, weight=1)
        self.canvas = tk.Canvas(canvas_wrap, bg=EDITOR_THEME["canvas"], highlightthickness=0, bd=0, cursor="hand2")
        self.canvas.grid(row=0, column=0, sticky="nsew", padx=1, pady=1)
        self.canvas.bind("<Configure>", self._on_canvas_configure)
        self.canvas.bind("<Button-1>", lambda e: self._safe_canvas(self._canvas_press, e))
        self.canvas.bind("<B1-Motion>", lambda e: self._safe_canvas(self._canvas_drag, e))
        self.canvas.bind("<ButtonRelease-1>", lambda e: self._safe_canvas(self._canvas_release, e))
        self.canvas.bind("<MouseWheel>", lambda e: self._safe_canvas(self._canvas_wheel, e))
        self.canvas.bind("<Double-Button-1>", lambda e: self._safe_canvas(self._canvas_double_click, e))

        self.crop_confirm_frame = tk.Frame(canvas_wrap, bg=EDITOR_THEME["surface"], bd=1, relief="solid")
        self.crop_confirm_check = self._button(
            self.crop_confirm_frame,
            "✓",
            self._confirm_crop_drag,
            width=3,
            primary=True,
        )
        self.crop_confirm_check.pack(side="left", padx=(4, 2), pady=4)
        self.crop_confirm_cancel = self._button(
            self.crop_confirm_frame,
            "✗",
            self._cancel_crop_drag,
            width=3,
        )
        self.crop_confirm_cancel.pack(side="left", padx=(2, 4), pady=4)
        self._hide_crop_confirm()

        export_row = tk.Frame(workspace, bg=EDITOR_THEME["bg"])
        export_row.grid(row=2, column=0, sticky="ew")
        export_row.grid_columnconfigure(0, weight=1)
        self.save_button = self._button(export_row, self.t("editor_finish"), self.save, width=12, primary=True)
        self.save_button.grid(row=0, column=1, sticky="e")

        self._vars()
        self.refresh_history()
        self.refresh_canvas()
        return frame

    def _vars(self):
        self._widgets["crop_mode"] = tk.StringVar(value="handles")
        self._widgets["crop_aspect"] = tk.StringVar(value="free")
        self._widgets["rotate_degrees"] = tk.StringVar(value="0")
        self._widgets["draw_tolerance"] = tk.IntVar(value=32)
        self._widgets["resize_preset"] = tk.StringVar(value="media")
        self._widgets["resize_mode"] = tk.StringVar(value="scale")
        self._widgets["resize_canvas_resolution"] = tk.StringVar(value="fhd")
        self._widgets["resize_canvas_aspect"] = tk.StringVar(value="16:9")
        self._widgets["resize_lock_aspect"] = tk.BooleanVar(value=True)
        self._widgets["resize_w"] = tk.StringVar(value="")
        self._widgets["resize_h"] = tk.StringVar(value="")
        self._widgets["draw_mode"] = tk.StringVar(value="pencil")
        self._widgets["draw_opacity"] = tk.IntVar(value=100)
        self._widgets["draw_size"] = tk.IntVar(value=6)
        self._widgets["eraser_mode"] = tk.StringVar(value="manual")
        self._widgets["eraser_tolerance"] = tk.IntVar(value=32)
        self._widgets["eraser_size"] = tk.IntVar(value=18)
        self._widgets["shape_kind"] = tk.StringVar(value="rectangle")
        self._widgets["shape_fill"] = tk.BooleanVar(value=False)
        self._widgets["shape_stroke"] = tk.BooleanVar(value=True)
        self._widgets["shape_stroke_width"] = tk.IntVar(value=3)
        self._widgets["text_font"] = tk.StringVar(value=editor_text.DEFAULT_FONT_FAMILY)
        self._widgets["text_size"] = tk.IntVar(value=int(editor_text.DEFAULT_FONT_SIZE))
        self._widgets["text_bold"] = tk.BooleanVar(value=False)
        self._widgets["text_italic"] = tk.BooleanVar(value=False)
        self._widgets["text_underline"] = tk.BooleanVar(value=False)
        self._widgets["text_strikethrough"] = tk.BooleanVar(value=False)
        self._widgets["text_border"] = tk.BooleanVar(value=False)
        self._widgets["text_border_width"] = tk.IntVar(value=2)

    def var(self, name):
        return self._widgets[name]

    def _attach_tooltip(self, widget, text: str):
        def show(_event):
            tip = tk.Toplevel(widget)
            tip.wm_overrideredirect(True)
            tip.wm_geometry(
                f"+{widget.winfo_rootx() + 8}+{widget.winfo_rooty() + widget.winfo_height() + 6}"
            )
            tk.Label(
                tip,
                text=text,
                bg=EDITOR_THEME["surface"],
                fg=EDITOR_THEME["text"],
                font=("Segoe UI", 9),
                padx=6,
                pady=3,
            ).pack()
            widget._tooltip_window = tip

        def hide(_event):
            tip = getattr(widget, "_tooltip_window", None)
            if tip is not None:
                tip.destroy()
                widget._tooltip_window = None

        widget.bind("<Enter>", show)
        widget.bind("<Leave>", hide)

    def _icon_button(self, parent, icon_name, command, size=24, primary=False, tooltip_key=None):
        image = editor_icons.render_icon(icon_name, size, EDITOR_THEME["btn_text"])
        photo = ImageTk.PhotoImage(image)
        self._icon_photos.append(photo)
        bg = EDITOR_THEME["accent"] if primary else EDITOR_THEME["btn"]
        active_bg = EDITOR_THEME["btn_active"] if not primary else EDITOR_THEME["accent"]
        pad = max(2, size // 10)
        button = tk.Button(
            parent,
            image=photo,
            command=command,
            bg=bg,
            activebackground=active_bg,
            relief="flat",
            bd=0,
            padx=pad,
            pady=pad,
            cursor="hand2",
        )
        button.image = photo
        if tooltip_key:
            self._attach_tooltip(button, self.t(tooltip_key))
        return button

    def _button(self, parent, text, command, width=10, primary=False, toggle=False):
        bg = EDITOR_THEME["accent"] if primary else EDITOR_THEME["btn"]
        fg = "#111827" if primary else EDITOR_THEME["btn_text"]
        button = tk.Button(
            parent,
            text=text,
            command=command,
            width=width,
            bg=bg,
            fg=fg,
            activebackground=EDITOR_THEME["btn_active"],
            activeforeground=EDITOR_THEME["btn_text"],
            relief="flat",
            bd=0,
            font=("Segoe UI", 9),
            padx=6,
            pady=4,
            cursor="hand2",
            highlightthickness=2 if toggle else 0,
            highlightbackground=EDITOR_THEME["bg"],
            highlightcolor=EDITOR_THEME["accent"],
        )
        return button

    def _set_toggle_button_active(self, button: tk.Button, active: bool):
        if active:
            button.configure(
                relief="solid",
                highlightbackground=EDITOR_THEME["accent"],
                highlightthickness=2,
                bg=EDITOR_THEME["btn_active"],
            )
        else:
            button.configure(
                relief="flat",
                highlightbackground=EDITOR_THEME["bg"],
                highlightthickness=0,
                bg=EDITOR_THEME["btn"],
            )

    def _entry(self, parent, textvariable):
        return tk.Entry(
            parent,
            textvariable=textvariable,
            bg=EDITOR_THEME["surface"],
            fg=EDITOR_THEME["text"],
            insertbackground=EDITOR_THEME["text"],
            relief="flat",
            bd=0,
            highlightthickness=1,
            highlightbackground=EDITOR_THEME["border"],
            highlightcolor=EDITOR_THEME["accent"],
            font=("Segoe UI", 9),
        )

    def _label(self, parent, text):
        return tk.Label(parent, text=text, bg=EDITOR_THEME["bg"], fg=EDITOR_THEME["muted"], font=("Segoe UI", 9))

    def _option(self, parent, variable, values, width=10):
        menu = tk.OptionMenu(parent, variable, *values)
        menu.configure(
            bg=EDITOR_THEME["btn"],
            fg=EDITOR_THEME["btn_text"],
            activebackground=EDITOR_THEME["btn_active"],
            highlightthickness=0,
            bd=0,
            width=width,
        )
        menu["menu"].configure(bg=EDITOR_THEME["surface"], fg=EDITOR_THEME["text"])
        return menu

    def _sub_actions(self):
        for child in self.sub_toolbar_actions.winfo_children():
            child.destroy()
        undo_btn = self._icon_button(
            self.sub_toolbar_actions,
            "undo",
            self.undo,
            tooltip_key="editor_tool_undo",
        )
        undo_btn.pack(side="left", padx=(0, 4))
        redo_btn = self._icon_button(
            self.sub_toolbar_actions,
            "redo",
            self.redo,
            tooltip_key="editor_tool_redo",
        )
        redo_btn.pack(side="left", padx=(0, 8))
        self._button(
            self.sub_toolbar_actions,
            self.t("editor_save"),
            self.save_and_exit,
            width=8,
            primary=True,
        ).pack(side="left", padx=(0, 4))
        self._button(
            self.sub_toolbar_actions,
            self.t("editor_tool_exit"),
            self.exit_tool,
            width=8,
        ).pack(side="left")

    def enter_tool(self, tool_name: str):
        if tool_name == "crop":
            if not self.session.is_cropable():
                messagebox.showinfo(self.app._app_title(), self.t("editor_crop_no_media"))
                return
        elif not self.session.is_editable_image() and tool_name not in {"shape", "text"}:
            messagebox.showinfo(self.app._app_title(), self.t("editor_no_image"))
            return
        if tool_name in {"shape", "text"} and not self.session.is_editable_image():
            messagebox.showinfo(self.app._app_title(), self.t("editor_no_image"))
            return
        self.active_tool = tool_name
        self.main_toolbar.grid_remove()
        self.sub_toolbar.grid(row=0, column=0, sticky="ew")
        for child in self.sub_toolbar_content.winfo_children():
            child.destroy()
        self.crop_mode_buttons.clear()
        self.crop_aspect_buttons.clear()
        self.resize_mode_buttons.clear()
        self.resize_preset_buttons.clear()
        self.shape_kind_buttons.clear()
        self.canvas_resolution_buttons.clear()
        self.canvas_aspect_buttons.clear()
        self.draw_mode_buttons.clear()
        self._resize_scale_row = None
        self._resize_canvas_row = None
        self._resize_aspect_row = None
        self._resize_dims_row = None
        self._resize_lock_btn = None
        self._resize_hint = None
        self._clear_canvas_layout()
        self._sub_actions()
        builders = {
            "crop": self._build_crop_bar,
            "rotate": self._build_rotate_bar,
            "resize": self._build_resize_bar,
            "draw": self._build_draw_bar,
            "shape": self._build_shape_bar,
            "text": self._build_text_bar,
        }
        builders[tool_name]()
        if tool_name == "crop" and self.session.image is not None:
            self._reset_crop_state()
        if tool_name == "rotate":
            self._reset_rotate_state()
        if tool_name == "resize" and self.session.image is not None:
            self._reset_resize_state()
        if tool_name == "draw":
            self._update_draw_cursor()
        elif tool_name == "shape":
            self._reset_shape_state()
            self.canvas.configure(cursor="crosshair")
        elif tool_name == "text":
            self._reset_text_state()
            self.canvas.configure(cursor="xterm")
            self.canvas.focus_set()
            self.canvas.bind("<Delete>", self._on_text_key_delete)
        else:
            self.canvas.unbind("<Delete>")
            self.canvas.configure(cursor="hand2")
        self.refresh_canvas()

    def _reset_crop_state(self):
        self.crop_drag_active = False
        self.crop_drag_phase = None
        self._crop_interacting = False
        if self._crop_overlay_after_id is not None:
            self.canvas.after_cancel(self._crop_overlay_after_id)
            self._crop_overlay_after_id = None
        self.crop_handle = None
        self.crop_drag_origin = None
        self.crop_drag_start = None
        self.shape_start_image = None
        self.shape_start_canvas = None
        self._hide_crop_confirm()
        self.var("crop_aspect").set("free")
        if self.session.image is not None:
            self.crop_box = editor_ops.full_image_crop_box(
                self.session.image.width,
                self.session.image.height,
            )
        if self.crop_aspect_buttons:
            self._refresh_crop_aspect_buttons()

    def _clear_rotate_drag(self):
        self._rotate_dragging = False
        self._rotate_drag_display = None
        self._rotate_drag_photo = None
        if self._rotate_refresh_after_id is not None:
            self.canvas.after_cancel(self._rotate_refresh_after_id)
            self._rotate_refresh_after_id = None

    def _clear_canvas_layout(self):
        self._canvas_source_image = None
        self._canvas_source_stroke = None
        self._canvas_dragging = False
        self._canvas_handle_resizing = False
        self._canvas_handle = None
        self._canvas_box_origin = None
        self._canvas_handle_start = None
        self._canvas_drag_origin = None
        self._canvas_drag_canvas_start = None
        self._canvas_placement_origin = None
        self._canvas_drag_photo = None
        self._invalidate_canvas_scaled_cache()
        if self._canvas_refresh_after_id is not None:
            self.canvas.after_cancel(self._canvas_refresh_after_id)
            self._canvas_refresh_after_id = None
        if self._canvas_wheel_after_id is not None:
            self.canvas.after_cancel(self._canvas_wheel_after_id)
            self._canvas_wheel_after_id = None

    def _reset_resize_state(self):
        self._clear_canvas_layout()
        if self.session.image is None:
            self._resize_source_size = None
            return
        width, height = self.session.image.size
        self._resize_source_size = (width, height)
        self.var("resize_w").set(str(width))
        self.var("resize_h").set(str(height))
        self.var("resize_mode").set("scale")
        self.var("resize_canvas_resolution").set("fhd")
        self.var("resize_canvas_aspect").set("16:9")
        self.var("resize_lock_aspect").set(True)

    def _reset_rotate_state(self):
        self._rotate_wheel_angle = 0.0
        self._rotate_angle_at_drag_start = 0.0
        self._clear_rotate_drag()

    def exit_tool(self, *, force: bool = False) -> bool:
        if not force and self._tool_has_pending_changes():
            if not messagebox.askyesno(
                self.app._app_title(),
                self.t("editor_exit_unsaved"),
            ):
                return False
        self._discard_tool_preview()
        self.active_tool = None
        self.crop_box = None
        self.crop_handle = None
        self.crop_drag_phase = None
        self._crop_interacting = False
        if self._crop_overlay_after_id is not None:
            self.canvas.after_cancel(self._crop_overlay_after_id)
            self._crop_overlay_after_id = None
        self._hide_crop_confirm()
        self.sub_toolbar.grid_remove()
        self.main_toolbar.grid(row=0, column=0, sticky="ew")
        self.canvas.configure(cursor="hand2")
        self.canvas.unbind("<Delete>")
        self.invalidate_preview()
        self.refresh_canvas()
        return True

    def _discard_tool_preview(self):
        self._clear_canvas_layout()
        self._reset_rotate_state()
        self._reset_shape_state()
        self._finish_text_edit()
        self._reset_text_state()

    def _reset_text_state(self):
        self._finish_text_edit()
        self._text_selected_id = None
        self._text_dragging = False
        self._text_drag_mode = None
        self._text_drag_handle = None
        self._text_drag_origin = None
        self._text_drag_box_origin = None
        self._text_drag_size_origin = 0.0
        self._text_drag_object_origin = None
        self._text_pending_move_id = None
        self.canvas.delete("text_overlay")

    def _reset_shape_state(self):
        self.shape_start_canvas = None
        self.shape_start_image = None
        self.shape_dragging = False
        self.shape_curve_points = []
        self.canvas.delete("overlay")

    def _tool_has_pending_changes(self) -> bool:
        tool = self.active_tool
        if tool is None or self.session.image is None:
            return False
        if tool == "shape":
            if self.var("shape_kind").get() == "curve" and self.shape_curve_points:
                return True
            if self.shape_start_image is not None:
                return True
        if tool == "text" and self._text_editing_id is not None:
            return True
        if tool == "crop" and self.crop_box is not None:
            width, height = self.session.image.size
            if self.crop_box != (0, 0, width, height):
                return True
        if tool == "resize":
            mode = self.var("resize_mode").get()
            if mode == "canvas" and self._canvas_layout_active():
                return True
            if mode == "scale":
                dims = self._parse_resize_dimensions()
                if dims is not None and dims != self.session.image.size:
                    return True
        return False

    def _build_crop_bar(self):
        row = tk.Frame(self.sub_toolbar_content, bg=EDITOR_THEME["bg"])
        row.pack(fill="x")
        self._label(row, self.t("editor_crop_mode")).pack(side="left", padx=(0, 4))
        for mode, label in (("handles", "editor_crop_handles"), ("drag", "editor_crop_drag")):
            btn = self._button(
                row,
                self.t(label),
                lambda m=mode: self._set_crop_mode(m),
                width=8,
                toggle=True,
            )
            btn.pack(side="left", padx=2)
            self.crop_mode_buttons[mode] = btn
        self._refresh_crop_mode_buttons()
        self.crop_aspect_buttons.clear()
        for key, label in (
            ("free", "editor_aspect_free"),
            ("1:1", "editor_aspect_1_1"),
            ("9:16", "editor_aspect_9_16"),
            ("16:9", "editor_aspect_16_9"),
        ):
            btn = self._button(
                row,
                self.t(label),
                lambda aspect=key: self._set_crop_aspect(aspect),
                width=6,
                toggle=True,
            )
            btn.pack(side="left", padx=2)
            self.crop_aspect_buttons[key] = btn
        self._refresh_crop_aspect_buttons()

    def _crop_aspect_locked(self) -> bool:
        return editor_ops.CROP_ASPECTS.get(self.var("crop_aspect").get()) is not None

    def _refresh_crop_aspect_buttons(self):
        active = self.var("crop_aspect").get()
        for key, button in self.crop_aspect_buttons.items():
            button.configure(state="normal", fg=EDITOR_THEME["btn_text"], bg=EDITOR_THEME["btn"])
            self._set_toggle_button_active(button, key == active)

    def _refresh_crop_mode_buttons(self):
        active = self.var("crop_mode").get()
        for mode, button in self.crop_mode_buttons.items():
            self._set_toggle_button_active(button, mode == active)

    def _show_crop_confirm(self):
        self.crop_confirm_frame.place(relx=1.0, rely=1.0, anchor="se", x=-10, y=-10)

    def _hide_crop_confirm(self):
        self.crop_confirm_frame.place_forget()

    def _confirm_crop_drag(self):
        self.crop_drag_phase = None
        self._hide_crop_confirm()
        self.var("crop_mode").set("handles")
        self._refresh_crop_mode_buttons()
        self._refresh_crop_aspect_buttons()
        self.invalidate_preview()
        self.refresh_canvas()

    def _cancel_crop_drag(self):
        if self.session.image is not None:
            self.crop_box = editor_ops.full_image_crop_box(
                self.session.image.width,
                self.session.image.height,
            )
        self.crop_drag_phase = None
        self.crop_drag_active = False
        self.shape_start_image = None
        self.shape_start_canvas = None
        self._hide_crop_confirm()
        self.invalidate_preview()
        self.refresh_canvas()

    def _set_crop_mode(self, mode: str):
        self.var("crop_mode").set(mode)
        self._refresh_crop_mode_buttons()
        self._refresh_crop_aspect_buttons()
        self.crop_handle = None
        self.crop_drag_origin = None
        self.crop_drag_start = None
        self.crop_drag_active = False
        self.shape_start_image = None
        self.shape_start_canvas = None
        if mode == "drag":
            self.crop_drag_phase = None
            self._hide_crop_confirm()
        self.invalidate_preview()
        self.refresh_canvas()

    def _set_crop_aspect(self, aspect_key: str):
        self.var("crop_aspect").set(aspect_key)
        self._refresh_crop_aspect_buttons()
        if self.crop_box is None or self.session.image is None:
            return
        aspect = editor_ops.CROP_ASPECTS.get(aspect_key)
        img_w, img_h = self.session.image.size
        if aspect is not None:
            self.crop_box = editor_ops.fit_crop_box_to_aspect(self.crop_box, aspect, img_w, img_h)
        self.invalidate_preview()
        self.refresh_canvas(overlay_only=True)

    def _build_rotate_bar(self):
        row = tk.Frame(self.sub_toolbar_content, bg=EDITOR_THEME["bg"])
        row.pack(fill="x")
        self._icon_button(
            row,
            "flip_h",
            self.flip_horizontal,
            size=22,
            tooltip_key="editor_flip_h",
        ).pack(side="left", padx=(0, 2))
        self._icon_button(
            row,
            "flip_v",
            self.flip_vertical,
            size=22,
            tooltip_key="editor_flip_v",
        ).pack(side="left", padx=(0, 10))
        self._label(row, self.t("editor_rotate_degrees")).pack(side="left", padx=(0, 4))
        entry = tk.Entry(
            row,
            textvariable=self.var("rotate_degrees"),
            width=6,
            bg=EDITOR_THEME["surface"],
            fg=EDITOR_THEME["text"],
            insertbackground=EDITOR_THEME["text"],
        )
        entry.pack(side="left")
        entry.bind("<Return>", self._commit_rotate_degrees_entry)
        entry.bind("<FocusOut>", self._commit_rotate_degrees_entry)
        self._label(row, self.t("editor_rotate_entry_hint")).pack(side="left", padx=(6, 8))
        self._icon_button(
            row,
            "rotate_left",
            lambda: self.rotate_by(-90),
            size=22,
            tooltip_key="editor_rotate_ccw",
        ).pack(side="left", padx=2)
        self._icon_button(
            row,
            "rotate_right",
            lambda: self.rotate_by(90),
            size=22,
            tooltip_key="editor_rotate_cw",
        ).pack(side="left", padx=2)

    def _build_resize_bar(self):
        row = tk.Frame(self.sub_toolbar_content, bg=EDITOR_THEME["bg"])
        row.pack(fill="x")
        self._label(row, self.t("editor_resize_mode")).pack(side="left", padx=(0, 4))
        for mode, label in (("scale", "editor_resize_scale"), ("canvas", "editor_resize_canvas")):
            btn = self._button(
                row,
                self.t(label),
                lambda m=mode: self._set_resize_mode(m),
                width=8,
                toggle=True,
            )
            btn.pack(side="left", padx=2)
            self.resize_mode_buttons[mode] = btn

        row2 = tk.Frame(self.sub_toolbar_content, bg=EDITOR_THEME["bg"])
        row2.pack(fill="x", pady=(6, 0))
        self._resize_scale_row = row2
        for preset, label in (
            ("baja", "quality_baja"),
            ("media", "quality_media"),
            ("alta", "quality_alta"),
        ):
            btn = self._button(
                row2,
                self.t(label),
                lambda p=preset: self._apply_resize_preset(p),
                width=7,
                toggle=True,
            )
            btn.pack(side="left", padx=2)
            self.resize_preset_buttons[preset] = btn
        self._refresh_resize_preset_buttons()

        row3 = tk.Frame(self.sub_toolbar_content, bg=EDITOR_THEME["bg"])
        row3.pack(fill="x", pady=(6, 0))
        self._resize_dims_row = row3
        self._label(row3, "W").pack(side="left", padx=(0, 2))
        w_entry = tk.Entry(
            row3,
            textvariable=self.var("resize_w"),
            width=6,
            bg=EDITOR_THEME["surface"],
            fg=EDITOR_THEME["text"],
            insertbackground=EDITOR_THEME["text"],
        )
        w_entry.pack(side="left")
        w_entry.bind("<KeyRelease>", lambda _e: self._on_resize_dimension_change("w"))
        self._label(row3, "H").pack(side="left", padx=(6, 2))
        h_entry = tk.Entry(
            row3,
            textvariable=self.var("resize_h"),
            width=6,
            bg=EDITOR_THEME["surface"],
            fg=EDITOR_THEME["text"],
            insertbackground=EDITOR_THEME["text"],
        )
        h_entry.pack(side="left")
        h_entry.bind("<KeyRelease>", lambda _e: self._on_resize_dimension_change("h"))

        self._resize_lock_btn = self._button(
            row3,
            "🔒",
            self._toggle_resize_lock_aspect,
            width=3,
            toggle=True,
        )
        self._resize_lock_btn.pack(side="left", padx=(8, 4))
        self._refresh_resize_lock_button()

        self._resize_canvas_row = tk.Frame(self.sub_toolbar_content, bg=EDITOR_THEME["bg"])
        self._resize_canvas_row.pack(fill="x", pady=(6, 0))
        self._label(self._resize_canvas_row, self.t("editor_resize_resolution")).pack(side="left", padx=(0, 4))
        for res_key, label in (
            ("hd", "editor_resize_res_hd"),
            ("fhd", "editor_resize_res_fhd"),
            ("4k", "editor_resize_res_4k"),
        ):
            btn = self._button(
                self._resize_canvas_row,
                self.t(label),
                lambda r=res_key: self._set_canvas_resolution(r),
                width=8,
                toggle=True,
            )
            btn.pack(side="left", padx=2)
            self.canvas_resolution_buttons[res_key] = btn

        self._resize_aspect_row = tk.Frame(self.sub_toolbar_content, bg=EDITOR_THEME["bg"])
        self._resize_aspect_row.pack(fill="x", pady=(6, 0))
        self._label(self._resize_aspect_row, self.t("editor_resize_aspect")).pack(side="left", padx=(0, 4))
        for aspect_key, label in (
            ("16:9", "editor_aspect_16_9"),
            ("9:16", "editor_aspect_9_16"),
            ("1:1", "editor_aspect_1_1"),
            ("free", "editor_aspect_free"),
        ):
            btn = self._button(
                self._resize_aspect_row,
                self.t(label),
                lambda a=aspect_key: self._set_canvas_aspect(a),
                width=6,
                toggle=True,
            )
            btn.pack(side="left", padx=2)
            self.canvas_aspect_buttons[aspect_key] = btn

        self._resize_hint = self._label(self.sub_toolbar_content, self.t("editor_resize_scale_hint"))
        self._resize_hint.pack(fill="x", pady=(6, 0))

        self._refresh_resize_mode_buttons()
        self._refresh_canvas_resolution_buttons()
        self._refresh_canvas_aspect_buttons()

    def _tk_alive(self, widget) -> bool:
        return widget is not None and bool(widget.winfo_exists())

    def _refresh_resize_mode_buttons(self):
        active = self.var("resize_mode").get()
        for key, button in list(self.resize_mode_buttons.items()):
            if not self._tk_alive(button):
                continue
            button.configure(state="normal", fg=EDITOR_THEME["btn_text"], bg=EDITOR_THEME["btn"])
            self._set_toggle_button_active(button, key == active)
        is_canvas = active == "canvas"
        for row, show in (
            (getattr(self, "_resize_scale_row", None), not is_canvas),
            (getattr(self, "_resize_canvas_row", None), is_canvas),
            (getattr(self, "_resize_aspect_row", None), is_canvas),
        ):
            if self._tk_alive(row):
                if show:
                    row.pack(fill="x", pady=(6, 0))
                else:
                    row.pack_forget()
        lock_btn = getattr(self, "_resize_lock_btn", None)
        if self._tk_alive(lock_btn):
            if is_canvas:
                lock_btn.pack_forget()
            else:
                lock_btn.pack(side="left", padx=(8, 4))
        hint = getattr(self, "_resize_hint", None)
        if self._tk_alive(hint):
            if is_canvas and self.var("resize_canvas_aspect").get() == "free":
                hint.configure(text=self.t("editor_resize_canvas_free_hint"))
            elif is_canvas:
                hint.configure(text=self.t("editor_resize_canvas_hint"))
            else:
                hint.configure(text=self.t("editor_resize_scale_hint"))

    def _refresh_canvas_resolution_buttons(self, active: str | None = None):
        if active is None:
            active = self.var("resize_canvas_resolution").get()
        for key, button in list(self.canvas_resolution_buttons.items()):
            if not self._tk_alive(button):
                continue
            button.configure(state="normal", fg=EDITOR_THEME["btn_text"], bg=EDITOR_THEME["btn"])
            self._set_toggle_button_active(button, key == active)

    def _refresh_canvas_aspect_buttons(self, active: str | None = None):
        if active is None:
            active = self.var("resize_canvas_aspect").get()
        for key, button in list(self.canvas_aspect_buttons.items()):
            if not self._tk_alive(button):
                continue
            button.configure(state="normal", fg=EDITOR_THEME["btn_text"], bg=EDITOR_THEME["btn"])
            self._set_toggle_button_active(button, key == active)

    def _refresh_resize_preset_buttons(self, active: str | None = None):
        if active is None:
            active = self.var("resize_preset").get()
        for key, button in list(self.resize_preset_buttons.items()):
            if not self._tk_alive(button):
                continue
            button.configure(state="normal", fg=EDITOR_THEME["btn_text"], bg=EDITOR_THEME["btn"])
            self._set_toggle_button_active(button, key == active)

    def _refresh_resize_lock_button(self):
        if not self._tk_alive(getattr(self, "_resize_lock_btn", None)):
            return
        locked = self.var("resize_lock_aspect").get()
        self._set_toggle_button_active(self._resize_lock_btn, locked)
        self._resize_lock_btn.configure(text="🔒" if locked else "🔓")

    def _set_resize_mode(self, mode: str):
        self.var("resize_mode").set(mode)
        if mode == "canvas":
            self._init_canvas_layout()
        elif self.session.image is not None:
            width, height = self.session.image.size
            self.var("resize_w").set(str(width))
            self.var("resize_h").set(str(height))
            self._resize_source_size = (width, height)
            self._clear_canvas_layout()
        self._refresh_resize_mode_buttons()
        self.invalidate_preview()
        self.refresh_canvas()

    def _init_canvas_layout(self):
        if self.session.image is None:
            return
        self._canvas_source_image = self.session.image.copy()
        stroke = self.session.stroke_layer
        self._canvas_source_stroke = stroke.copy() if stroke is not None else None
        self._invalidate_canvas_scaled_cache()
        self._update_canvas_dimensions_from_preset()
        self._refit_canvas_image()

    def _update_canvas_dimensions_from_preset(self):
        aspect = self.var("resize_canvas_aspect").get()
        if aspect == "free":
            dims = self._parse_resize_dimensions()
            if dims is None and self.session.image is not None:
                dims = self.session.image.size
            if dims is not None:
                self.var("resize_w").set(str(dims[0]))
                self.var("resize_h").set(str(dims[1]))
            return
        canvas_w, canvas_h = editor_ops.canvas_dimensions_from_preset(
            self.var("resize_canvas_resolution").get(),
            aspect,
        )
        self.var("resize_w").set(str(canvas_w))
        self.var("resize_h").set(str(canvas_h))

    def _refit_canvas_image(self):
        if self._canvas_source_image is None:
            return
        dims = self._parse_resize_dimensions()
        if dims is None:
            return
        canvas_w, canvas_h = dims
        px, py, scale = editor_ops.fit_image_on_canvas(
            self._canvas_source_image.width,
            self._canvas_source_image.height,
            canvas_w,
            canvas_h,
        )
        self._canvas_placement_x = px
        self._canvas_placement_y = py
        self._canvas_content_scale = scale

    def _set_canvas_resolution(self, resolution: str):
        self.var("resize_canvas_resolution").set(resolution)
        self._refresh_canvas_resolution_buttons(resolution)
        if self.var("resize_canvas_aspect").get() != "free":
            self._update_canvas_dimensions_from_preset()
        if self._canvas_source_image is None:
            self._init_canvas_layout()
        else:
            self._refit_canvas_image()
        self.invalidate_preview()
        self.refresh_canvas()

    def _set_canvas_aspect(self, aspect: str):
        self.var("resize_canvas_aspect").set(aspect)
        self._refresh_canvas_aspect_buttons(aspect)
        if aspect != "free":
            self._update_canvas_dimensions_from_preset()
        if self._canvas_source_image is None:
            self._init_canvas_layout()
        else:
            self._refit_canvas_image()
        hint = getattr(self, "_resize_hint", None)
        if self._tk_alive(hint):
            if aspect == "free":
                hint.configure(text=self.t("editor_resize_canvas_free_hint"))
            else:
                hint.configure(text=self.t("editor_resize_canvas_hint"))
        self.invalidate_preview()
        self.refresh_canvas()

    def _canvas_layout_active(self) -> bool:
        return (
            self.active_tool == "resize"
            and self.var("resize_mode").get() == "canvas"
            and self._canvas_source_image is not None
        )

    def _canvas_dims(self) -> tuple[int, int]:
        dims = self._parse_resize_dimensions()
        if dims is not None:
            return dims
        if self.session.image is not None:
            return self.session.image.size
        return 1, 1

    def _canvas_free_aspect(self) -> bool:
        return self.var("resize_canvas_aspect").get() == "free"

    def _canvas_box(self) -> tuple[int, int, int, int]:
        cw, ch = self._canvas_dims()
        return 0, 0, cw, ch

    def _invalidate_canvas_scaled_cache(self):
        self._canvas_scaled_base = None
        self._canvas_scaled_stroke = None
        self._canvas_scaled_at_scale = None

    def _ensure_canvas_scaled_cache(self):
        if self._canvas_source_image is None:
            return
        scale = self._canvas_content_scale
        if self._canvas_scaled_at_scale == scale and self._canvas_scaled_base is not None:
            return
        base = self._canvas_source_image.convert("RGBA")
        scaled_w = max(1, int(round(base.width * scale)))
        scaled_h = max(1, int(round(base.height * scale)))
        self._canvas_scaled_base = base.resize((scaled_w, scaled_h), Image.Resampling.BILINEAR)
        self._canvas_scaled_stroke = None
        if self._canvas_source_stroke is not None:
            stroke_rgba = self._canvas_source_stroke.convert("RGBA")
            if stroke_rgba.size != base.size:
                stroke_rgba = stroke_rgba.resize(base.size, Image.Resampling.NEAREST)
            self._canvas_scaled_stroke = stroke_rgba.resize((scaled_w, scaled_h), Image.Resampling.BILINEAR)
        self._canvas_scaled_at_scale = scale

    def _compose_canvas_frame_fast(
        self,
        canvas_w: int,
        canvas_h: int,
        preview_factor: float = 1.0,
    ) -> Image.Image | None:
        if self._canvas_source_image is None:
            return None
        self._ensure_canvas_scaled_cache()
        if self._canvas_scaled_base is None:
            return None
        pf = max(0.05, min(1.0, preview_factor))
        cw = max(1, int(round(canvas_w * pf)))
        ch = max(1, int(round(canvas_h * pf)))
        px = int(round(self._canvas_placement_x * pf))
        py = int(round(self._canvas_placement_y * pf))
        paste_base = self._canvas_scaled_base
        if pf < 0.999:
            paste_base = paste_base.resize(
                (
                    max(1, int(round(paste_base.width * pf))),
                    max(1, int(round(paste_base.height * pf))),
                ),
                Image.Resampling.BILINEAR,
            )
        new_base = Image.new("RGBA", (cw, ch), (0, 0, 0, 0))
        new_base.paste(paste_base, (px, py), paste_base)
        if self._canvas_scaled_stroke is not None:
            paste_stroke = self._canvas_scaled_stroke
            if pf < 0.999:
                paste_stroke = paste_stroke.resize(
                    (
                        max(1, int(round(paste_stroke.width * pf))),
                        max(1, int(round(paste_stroke.height * pf))),
                    ),
                    Image.Resampling.BILINEAR,
                )
            stroke_layer = Image.new("RGBA", (cw, ch), (0, 0, 0, 0))
            stroke_layer.paste(paste_stroke, (px, py), paste_stroke)
            return Image.alpha_composite(new_base, stroke_layer)
        return new_base

    def _schedule_canvas_refresh(self):
        if self._canvas_refresh_after_id is not None:
            return
        self._canvas_refresh_after_id = self.canvas.after(10, self._flush_canvas_refresh)

    def _flush_canvas_refresh(self):
        self._canvas_refresh_after_id = None
        if not self._canvas_layout_active():
            return
        self._paint_canvas_frame()

    def _paint_canvas_frame(self):
        if not self._canvas_layout_active():
            return
        widget_w = max(self.canvas.winfo_width(), 1)
        widget_h = max(self.canvas.winfo_height(), 1)
        canvas_w, canvas_h = self._canvas_dims()
        scale, offset_x, offset_y, display_w, display_h = editor.display_metrics(
            widget_w, widget_h, canvas_w, canvas_h
        )
        max_dim = max(canvas_w, canvas_h)
        cap = max(512, int(max(display_w, display_h) * 2))
        preview_factor = min(1.0, cap / max_dim) if max_dim > cap else 1.0
        composite = self._compose_canvas_frame_fast(canvas_w, canvas_h, preview_factor)
        if composite is None:
            return
        preview = composite.copy()
        preview.thumbnail(
            (max(1, int(display_w)), max(1, int(display_h))),
            Image.Resampling.BILINEAR,
        )
        self._canvas_drag_photo = ImageTk.PhotoImage(preview)
        self.canvas.delete("base", "overlay")
        self.canvas.create_image(offset_x, offset_y, anchor="nw", image=self._canvas_drag_photo, tags="base")
        self._draw_resize_overlay(scale, offset_x, offset_y, canvas_w, canvas_h)

    def _begin_canvas_handle_drag(self, event) -> bool:
        if not self._canvas_layout_active() or not self._canvas_free_aspect():
            return False
        canvas_w, canvas_h = self._canvas_dims()
        width, height, scale, offset_x, offset_y, _, _ = self.metrics()
        handle = editor_ops.hit_crop_handle(
            event.x,
            event.y,
            (0, 0, canvas_w, canvas_h),
            scale,
            offset_x,
            offset_y,
            handle_size=editor_ops.CROP_HANDLE_HIT_RADIUS,
            corners_only=False,
        )
        if not handle:
            return False
        self._canvas_handle_resizing = True
        self._canvas_handle = handle
        self._canvas_box_origin = (0, 0, canvas_w, canvas_h)
        self._canvas_handle_start = (event.x, event.y)
        self._paint_canvas_frame()
        return True

    def _update_canvas_handle_drag(self, event):
        if not self._canvas_handle_resizing or self._canvas_box_origin is None or self._canvas_handle_start is None:
            return
        _width, _height, scale, _offset_x, _offset_y, _, _ = self.metrics()
        dx = (event.x - self._canvas_handle_start[0]) / scale
        dy = (event.y - self._canvas_handle_start[1]) / scale
        left, top, right, bottom = editor_ops.resize_crop_box_by_handle(
            self._canvas_box_origin,
            self._canvas_handle,
            dx,
            dy,
            10000,
            10000,
            None,
        )
        canvas_w = max(50, right - left)
        canvas_h = max(50, bottom - top)
        self.var("resize_w").set(str(canvas_w))
        self.var("resize_h").set(str(canvas_h))
        self._schedule_canvas_refresh()

    def _commit_canvas_interaction(self):
        if not self._canvas_dragging and not self._canvas_handle_resizing:
            return
        self._clear_canvas_drag_state()
        self.invalidate_preview()
        self.refresh_canvas()

    def _clear_canvas_drag_state(self):
        self._canvas_dragging = False
        self._canvas_handle_resizing = False
        self._canvas_handle = None
        self._canvas_box_origin = None
        self._canvas_handle_start = None
        self._canvas_drag_canvas_start = None
        self._canvas_placement_origin = None

    def _canvas_coords_from_event(self, event) -> tuple[float, float, float] | None:
        width = max(self.canvas.winfo_width(), 1)
        height = max(self.canvas.winfo_height(), 1)
        canvas_w, canvas_h = self._canvas_dims()
        scale, offset_x, offset_y, display_w, display_h = editor.display_metrics(
            width, height, canvas_w, canvas_h
        )
        if (
            event.x < offset_x
            or event.y < offset_y
            or event.x > offset_x + display_w
            or event.y > offset_y + display_h
        ):
            return None
        return (event.x - offset_x) / scale, (event.y - offset_y) / scale, scale

    def _canvas_image_bounds(self) -> tuple[float, float, float, float]:
        iw, ih = self._canvas_source_image.size
        scale = self._canvas_content_scale
        return (
            self._canvas_placement_x,
            self._canvas_placement_y,
            iw * scale,
            ih * scale,
        )

    def _hit_canvas_image(self, event) -> bool:
        coords = self._canvas_coords_from_event(event)
        if coords is None:
            return False
        cx, cy, _scale = coords
        x0, y0, w, h = self._canvas_image_bounds()
        return x0 <= cx <= x0 + w and y0 <= cy <= y0 + h

    def _begin_canvas_drag(self, event) -> bool:
        if not self._canvas_layout_active():
            return False
        if not self._hit_canvas_image(event):
            return False
        self._canvas_dragging = True
        self._canvas_drag_origin = (event.x, event.y)
        coords = self._canvas_coords_from_event(event)
        self._canvas_drag_canvas_start = (coords[0], coords[1]) if coords else None
        self._canvas_placement_origin = (self._canvas_placement_x, self._canvas_placement_y)
        self._paint_canvas_frame()
        return True

    def _update_canvas_drag(self, event):
        if (
            not self._canvas_dragging
            or self._canvas_drag_canvas_start is None
            or self._canvas_placement_origin is None
        ):
            return
        coords = self._canvas_coords_from_event(event)
        if coords is None:
            return
        dx = coords[0] - self._canvas_drag_canvas_start[0]
        dy = coords[1] - self._canvas_drag_canvas_start[1]
        self._canvas_placement_x = self._canvas_placement_origin[0] + dx
        self._canvas_placement_y = self._canvas_placement_origin[1] + dy
        self._schedule_canvas_refresh()

    def _canvas_zoom(self, factor: float, anchor_x: float, anchor_y: float):
        if not self._canvas_layout_active():
            return
        old_scale = self._canvas_content_scale
        new_scale = max(0.05, min(4.0, old_scale * factor))
        if abs(new_scale - old_scale) < 0.0001:
            return
        rel_x = (anchor_x - self._canvas_placement_x) / max(old_scale, 0.0001)
        rel_y = (anchor_y - self._canvas_placement_y) / max(old_scale, 0.0001)
        self._canvas_content_scale = new_scale
        self._canvas_placement_x = anchor_x - rel_x * new_scale
        self._canvas_placement_y = anchor_y - rel_y * new_scale
        self._schedule_canvas_refresh()
        self._schedule_canvas_wheel_commit()

    def _schedule_canvas_wheel_commit(self):
        if self._canvas_wheel_after_id is not None:
            self.canvas.after_cancel(self._canvas_wheel_after_id)
        self._canvas_wheel_after_id = self.canvas.after(200, self._commit_canvas_wheel)

    def _commit_canvas_wheel(self):
        self._canvas_wheel_after_id = None
        if self._canvas_dragging or self._canvas_handle_resizing:
            return
        self.invalidate_preview()
        self.refresh_canvas()

    def _canvas_wheel(self, event):
        if not self._canvas_layout_active():
            return
        coords = self._canvas_coords_from_event(event)
        if coords is None:
            return
        cx, cy, _scale = coords
        delta = getattr(event, "delta", 0)
        if delta == 0:
            return
        factor = 1.1 if delta > 0 else 0.9
        self._canvas_zoom(factor, cx, cy)

    def _toggle_resize_lock_aspect(self):
        self.var("resize_lock_aspect").set(not self.var("resize_lock_aspect").get())
        self._refresh_resize_lock_button()
        self._on_resize_dimension_change("w")

    def _apply_resize_preset(self, preset: str):
        if self.session.image is None:
            return
        if self.var("resize_mode").get() != "scale":
            self._set_resize_mode("scale")
        width, height = self.session.image.size
        self._resize_source_size = (width, height)
        max_side = editor_ops.RESIZE_PRESETS.get(preset, editor_ops.RESIZE_PRESETS["media"])
        new_w, new_h = editor_ops.preset_scale_dimensions(width, height, max_side)
        self.var("resize_preset").set(preset)
        self.var("resize_w").set(str(new_w))
        self.var("resize_h").set(str(new_h))
        self._refresh_resize_preset_buttons(preset)
        self.apply_resize()

    def _on_resize_dimension_change(self, edited_axis: str):
        if self.session.image is None or self._resize_source_size is None:
            return
        mode = self.var("resize_mode").get()
        if mode == "canvas":
            if self.var("resize_canvas_aspect").get() != "free":
                self._update_canvas_dimensions_from_preset()
            if self._canvas_source_image is not None:
                self._refit_canvas_image()
            self.invalidate_preview()
            self.refresh_canvas()
            return
        source_w, source_h = self._resize_source_size
        try:
            current_w = int(self.var("resize_w").get().strip())
            current_h = int(self.var("resize_h").get().strip())
        except ValueError:
            self.refresh_canvas(overlay_only=True)
            return
        if self.var("resize_mode").get() == "scale" and self.var("resize_lock_aspect").get():
            new_w, new_h = editor_ops.paired_scale_dimensions(
                source_w,
                source_h,
                current_w,
                current_h,
                True,
                edited_axis,
            )
            self.var("resize_w").set(str(new_w))
            self.var("resize_h").set(str(new_h))
        self.refresh_canvas(overlay_only=True)

    def _parse_resize_dimensions(self) -> tuple[int, int] | None:
        try:
            return int(self.var("resize_w").get().strip()), int(self.var("resize_h").get().strip())
        except ValueError:
            return None

    def _draw_image_boundary(self, scale: float, offset_x: float, offset_y: float, img_w: int, img_h: int):
        if (
            self.active_tool == "resize"
            and self.var("resize_mode").get() == "canvas"
            and self._canvas_layout_active()
        ):
            return
        x1 = offset_x + img_w * scale
        y1 = offset_y + img_h * scale
        self.canvas.create_rectangle(
            offset_x,
            offset_y,
            x1,
            y1,
            outline=EDITOR_THEME["text"],
            width=1,
            dash=(4, 3),
            tags="overlay",
        )

    def _draw_tool_overlays(self, scale: float, offset_x: float, offset_y: float, img_w: int, img_h: int):
        if self.active_tool == "crop" and self.crop_box is not None:
            self._draw_crop_overlay(scale, offset_x, offset_y)
        elif self.active_tool == "rotate":
            wheel = self._rotate_wheel_metrics()
            if wheel is not None:
                self._draw_rotate_overlay(*wheel)
        elif self.active_tool == "resize":
            self._draw_resize_overlay(scale, offset_x, offset_y, img_w, img_h)
        elif self.active_tool == "text":
            self._draw_text_overlays(scale, offset_x, offset_y, img_w, img_h)
        if self.active_tool is None:
            self._draw_image_boundary(scale, offset_x, offset_y, img_w, img_h)

    def _draw_resize_overlay(self, scale: float, offset_x: float, offset_y: float, img_w: int, img_h: int):
        dims = self._parse_resize_dimensions()
        if dims is None:
            return
        target_w, target_h = dims
        target_w = max(1, target_w)
        target_h = max(1, target_h)
        disp_w = img_w * scale
        disp_h = img_h * scale
        mode = self.var("resize_mode").get()
        if mode == "scale":
            new_disp_w = target_w * scale
            new_disp_h = target_h * scale
            center_x = offset_x + disp_w / 2
            center_y = offset_y + disp_h / 2
            x0 = center_x - new_disp_w / 2
            y0 = center_y - new_disp_h / 2
            x1 = x0 + new_disp_w
            y1 = y0 + new_disp_h
            self.canvas.create_rectangle(
                x0, y0, x1, y1,
                outline=EDITOR_THEME["accent"],
                width=2,
                dash=(5, 4),
                tags="overlay",
            )
            if abs(target_w - img_w) > 0 or abs(target_h - img_h) > 0:
                self.canvas.create_text(
                    center_x,
                    y0 - 10,
                    text=f"{target_w} × {target_h}",
                    fill=EDITOR_THEME["text"],
                    font=("Segoe UI", 10, "bold"),
                    tags="overlay",
                )
            return

        if not self._canvas_layout_active():
            return
        x0, y0, placed_w, placed_h = self._canvas_image_bounds()
        sx0 = offset_x + x0 * scale
        sy0 = offset_y + y0 * scale
        sx1 = sx0 + placed_w * scale
        sy1 = sy0 + placed_h * scale
        self.canvas.create_rectangle(
            offset_x, offset_y, offset_x + disp_w, offset_y + disp_h,
            outline=EDITOR_THEME["accent"],
            width=2,
            tags="overlay",
        )
        self.canvas.create_rectangle(
            sx0, sy0, sx1, sy1,
            outline=EDITOR_THEME["text"],
            width=2,
            dash=(4, 3),
            tags="overlay",
        )
        self.canvas.create_text(
            offset_x + disp_w / 2,
            offset_y - 10,
            text=f"{target_w} × {target_h}",
            fill=EDITOR_THEME["text"],
            font=("Segoe UI", 10, "bold"),
            tags="overlay",
        )
        if self._canvas_free_aspect():
            handles = editor_ops.crop_handle_canvas_positions(
                (0, 0, target_w, target_h),
                scale,
                offset_x,
                offset_y,
                corners_only=False,
            )
            radius = editor_ops.CROP_HANDLE_VISUAL_RADIUS
            for cx, cy in handles.values():
                self.canvas.create_oval(
                    cx - radius,
                    cy - radius,
                    cx + radius,
                    cy + radius,
                    fill=EDITOR_THEME["accent"],
                    outline=EDITOR_THEME["text"],
                    width=1,
                    tags="overlay",
                )

    def _draw_scale(self, parent, variable, from_: int, to: int):
        return tk.Scale(
            parent,
            from_=from_,
            to=to,
            orient="horizontal",
            variable=variable,
            length=self.DRAW_SLIDER_LENGTH,
            width=self.DRAW_SLIDER_WIDTH,
            sliderlength=24,
            bg=EDITOR_THEME["bg"],
            fg=EDITOR_THEME["text"],
            highlightthickness=0,
            troughcolor=EDITOR_THEME["surface"],
            activebackground=EDITOR_THEME["accent"],
        )

    def _build_draw_color_swatch(self, parent):
        size = self.DRAW_COLOR_SWATCH_SIZE
        frame = tk.Frame(
            parent,
            bg=EDITOR_THEME["border"],
            bd=0,
            highlightthickness=1,
            highlightbackground=EDITOR_THEME["border"],
            width=size,
            height=size,
        )
        frame.pack_propagate(False)
        inner = tk.Frame(frame, bg=self.draw_color, cursor="hand2")
        inner.pack(fill="both", expand=True, padx=1, pady=1)
        inner.bind("<Button-1>", lambda _e: self.pick_draw_color())
        frame.bind("<Button-1>", lambda _e: self.pick_draw_color())
        frame._color_inner = inner
        return frame

    def _refresh_draw_color_swatch(self):
        swatch = getattr(self, "_draw_color_swatch", None)
        if swatch is None or not swatch.winfo_exists():
            return
        inner = getattr(swatch, "_color_inner", None)
        if inner is not None and inner.winfo_exists():
            inner.configure(bg=self.draw_color)
        swatch.configure(
            highlightbackground=EDITOR_THEME["border"],
            highlightthickness=1,
        )

    def _show_eyedropper_feedback(self, canvas_x: float, canvas_y: float, color_hex: str):
        if self._eyedropper_feedback_after_id is not None:
            self.canvas.after_cancel(self._eyedropper_feedback_after_id)
            self._eyedropper_feedback_after_id = None
        self.canvas.delete("eyedropper_feedback")
        half = 9
        self.canvas.create_rectangle(
            canvas_x - half,
            canvas_y - half,
            canvas_x + half,
            canvas_y + half,
            outline=color_hex,
            width=2,
            tags="eyedropper_feedback",
        )
        self.canvas.create_rectangle(
            canvas_x - half + 2,
            canvas_y - half + 2,
            canvas_x + half - 2,
            canvas_y + half - 2,
            fill=color_hex,
            outline="",
            tags="eyedropper_feedback",
        )
        self.canvas.create_text(
            canvas_x,
            canvas_y - half - 12,
            text=color_hex.upper(),
            fill=EDITOR_THEME["text"],
            font=("Segoe UI", 9, "bold"),
            tags="eyedropper_feedback",
        )
        self._eyedropper_feedback_after_id = self.canvas.after(
            900,
            self._clear_eyedropper_feedback,
        )

    def _clear_eyedropper_feedback(self):
        self._eyedropper_feedback_after_id = None
        self.canvas.delete("eyedropper_feedback")

    def _build_draw_bar(self):
        icon_size = self.DRAW_TOOL_ICON_SIZE
        row = tk.Frame(self.sub_toolbar_content, bg=EDITOR_THEME["bg"])
        row.pack(fill="x")
        self.draw_mode_buttons.clear()
        for mode, icon, label_key in (
            ("pencil", "pencil", "editor_draw_pencil"),
            ("eraser", "eraser", "editor_draw_eraser"),
            ("eyedropper", "eyedropper", "editor_draw_eyedropper"),
            ("bucket", "bucket", "editor_draw_bucket"),
        ):
            btn = self._icon_button(
                row,
                icon,
                lambda m=mode: self._set_draw_mode(m),
                size=icon_size,
                tooltip_key=label_key,
            )
            btn._icon_name = icon
            btn._draw_mode = mode
            btn.pack(side="left", padx=3)
            self.draw_mode_buttons[mode] = btn

        self._label(row, self.t("editor_opacity")).pack(side="left", padx=(10, 2))
        self._draw_scale(row, self.var("draw_opacity"), 5, 100).pack(side="left", padx=(0, 8))

        self._draw_size_row = tk.Frame(row, bg=EDITOR_THEME["bg"])
        self._draw_size_label = self._label(self._draw_size_row, self.t("editor_size"))
        self._draw_size_label.pack(side="left", padx=(0, 4))
        self._draw_scale(self._draw_size_row, self.var("draw_size"), 1, 100).pack(side="left")

        self._draw_tolerance_row = tk.Frame(row, bg=EDITOR_THEME["bg"])
        self._draw_tolerance_label = self._label(self._draw_tolerance_row, self.t("editor_tolerance"))
        self._draw_tolerance_label.pack(side="left", padx=(0, 4))
        self._draw_scale(self._draw_tolerance_row, self.var("draw_tolerance"), 0, 80).pack(side="left")

        self._draw_color_swatch = self._build_draw_color_swatch(row)
        self._draw_color_swatch.pack(side="left", padx=4)
        self._refresh_draw_bar_state()

    def _set_draw_mode(self, mode: str):
        current = self.var("draw_mode").get()
        if mode == "eyedropper":
            if current != "eyedropper":
                self._draw_return_mode = "pencil" if current == "eraser" else current
            self.var("draw_mode").set("eyedropper")
        else:
            self.var("draw_mode").set(mode)
            self._draw_return_mode = mode
        self._refresh_draw_bar_state()

    def _refresh_draw_bar_state(self):
        mode = self.var("draw_mode").get()
        icon_size = self.DRAW_TOOL_ICON_SIZE
        disabled_mode = self._draw_return_mode if mode == "eyedropper" else None
        for key, button in list(self.draw_mode_buttons.items()):
            icon_name = getattr(button, "_icon_name", key)
            draw_mode = getattr(button, "_draw_mode", key)
            is_disabled = draw_mode == disabled_mode
            if is_disabled:
                image = editor_icons.render_icon(icon_name, icon_size, EDITOR_THEME["muted"])
                photo = ImageTk.PhotoImage(image)
                self._icon_photos.append(photo)
                button.configure(
                    image=photo,
                    state="disabled",
                    bg=EDITOR_THEME["surface"],
                    relief="flat",
                    highlightthickness=0,
                    cursor="arrow",
                )
                button.image = photo
                continue
            image = editor_icons.render_icon(icon_name, icon_size, EDITOR_THEME["btn_text"])
            photo = ImageTk.PhotoImage(image)
            self._icon_photos.append(photo)
            button.configure(
                image=photo,
                state="normal",
                bg=EDITOR_THEME["btn"],
                cursor="hand2",
                command=lambda m=draw_mode: self._set_draw_mode(m),
            )
            button.image = photo
            self._set_toggle_button_active(button, draw_mode == mode)

        if mode == "bucket":
            self._draw_size_row.pack_forget()
            self._draw_tolerance_row.pack(side="left", padx=(0, 8))
        elif mode in {"pencil", "eraser"}:
            self._draw_tolerance_row.pack_forget()
            self._draw_size_row.pack(side="left", padx=(0, 8))
        else:
            self._draw_size_row.pack_forget()
            self._draw_tolerance_row.pack_forget()
        self._update_draw_cursor()
        self._refresh_draw_color_swatch()

    def _update_draw_cursor(self):
        if self.active_tool != "draw":
            return
        editor_cursors.apply_draw_cursor(self.canvas, self.var("draw_mode").get())

    def _pick_color_at(self, point: tuple[float, float], canvas_x: float, canvas_y: float):
        composite = self.session.composite()
        if composite is None:
            return
        rgba = editor_ops.sample_composite_color(composite, point[0], point[1])
        if rgba is None:
            return
        new_color = editor_ops.rgba_to_hex(rgba)
        old_color = self.draw_color.lower()
        self.draw_color = new_color
        self._refresh_draw_color_swatch()
        self._show_eyedropper_feedback(canvas_x, canvas_y, new_color)
        if new_color.lower() != old_color:
            self._set_draw_mode(self._draw_return_mode)

        if color and color[1]:
            self.draw_color = color[1]
            self._refresh_draw_color_swatch()

    def _build_color_swatch(self, parent, color: str, command):
        size = self.DRAW_COLOR_SWATCH_SIZE
        frame = tk.Frame(
            parent,
            bg=EDITOR_THEME["border"],
            bd=0,
            highlightthickness=1,
            highlightbackground=EDITOR_THEME["border"],
            width=size,
            height=size,
        )
        frame.pack_propagate(False)
        inner = tk.Frame(frame, bg=color, cursor="hand2")
        inner.pack(fill="both", expand=True, padx=1, pady=1)
        inner.bind("<Button-1>", lambda _e: command())
        frame.bind("<Button-1>", lambda _e: command())
        frame._color_inner = inner
        return frame

    def _refresh_color_swatch(self, swatch, color: str):
        if swatch is None or not swatch.winfo_exists():
            return
        inner = getattr(swatch, "_color_inner", None)
        if inner is not None and inner.winfo_exists():
            inner.configure(bg=color)

    def _set_shape_kind(self, kind: str):
        if self.var("shape_kind").get() == kind:
            return
        self.var("shape_kind").set(kind)
        self._reset_shape_state()
        self._refresh_shape_bar_state()

    def _refresh_shape_bar_state(self):
        active = self.var("shape_kind").get()
        icon_size = self.SHAPE_TOOL_ICON_SIZE
        for key, button in list(self.shape_kind_buttons.items()):
            icon_name = getattr(button, "_icon_name", f"shape_{key}")
            image = editor_icons.render_icon(icon_name, icon_size, EDITOR_THEME["btn_text"])
            photo = ImageTk.PhotoImage(image)
            self._icon_photos.append(photo)
            button.configure(image=photo, command=lambda k=key: self._set_shape_kind(k))
            button.image = photo
            self._set_toggle_button_active(button, key == active)
        hint = getattr(self, "_shape_hint", None)
        if self._tk_alive(hint):
            hints = {
                "line": "editor_shape_hint_line",
                "curve": "editor_shape_hint_curve",
                "rectangle": "editor_shape_hint_box",
                "oval": "editor_shape_hint_box",
                "circle": "editor_shape_hint_circle",
                "triangle": "editor_shape_hint_box",
                "pentagon": "editor_shape_hint_box",
                "hexagon": "editor_shape_hint_box",
                "star": "editor_shape_hint_box",
            }
            hint.configure(text=self.t(hints.get(active, "editor_shape_hint_rect")))
        self._refresh_color_swatch(getattr(self, "_shape_fill_swatch", None), self.shape_fill_color)
        self._refresh_color_swatch(getattr(self, "_shape_stroke_swatch", None), self.shape_stroke_color)

    def _pick_shape_fill_color(self):
        color = colorchooser.askcolor(color=self.shape_fill_color, title=self.t("editor_shape_fill_color"))
        if color and color[1]:
            self.shape_fill_color = color[1]
            self.var("shape_fill").set(True)
            self._refresh_shape_bar_state()

    def _pick_shape_stroke_color(self):
        color = colorchooser.askcolor(color=self.shape_stroke_color, title=self.t("editor_shape_stroke_color"))
        if color and color[1]:
            self.shape_stroke_color = color[1]
            self.var("shape_stroke").set(True)
            self._refresh_shape_bar_state()

    def _shape_preview_color(self) -> str:
        if self.var("shape_stroke").get():
            return self.shape_stroke_color
        if self.var("shape_fill").get():
            return self.shape_fill_color
        return EDITOR_THEME["accent"]

    def _shape_preview_width(self) -> int:
        if self.var("shape_stroke").get():
            return max(1, int(self.var("shape_stroke_width").get()))
        return 2

    def _canvas_coords_for_image_points(self, points: list[tuple[float, float]]) -> list[float]:
        width, height, scale, offset_x, offset_y, img_w, img_h = self.metrics()
        coords: list[float] = []
        for px, py in points:
            cx, cy = editor.image_to_canvas(px, py, width, height, img_w, img_h)
            coords.extend((cx, cy))
        return coords

    def _refresh_shape_overlay(self, end_image: tuple[float, float] | None = None):
        self.canvas.delete("overlay")
        kind = self.var("shape_kind").get()
        color = self._shape_preview_color()
        width = self._shape_preview_width()

        if kind == "curve":
            points = list(self.shape_curve_points)
            if end_image is not None:
                points.append(end_image)
            if len(points) >= 2:
                path = editor_ops.catmull_rom_chain(points)
                coords = self._canvas_coords_for_image_points(path)
                if len(coords) >= 4:
                    self.canvas.create_line(
                        *coords,
                        fill=color,
                        width=width,
                        capstyle="round",
                        joinstyle="round",
                        smooth=True,
                        tags="overlay",
                    )
            for px, py in self.shape_curve_points:
                cx, cy = self._canvas_coords_for_image_points([(px, py)])
                self.canvas.create_oval(
                    cx - 3,
                    cy - 3,
                    cx + 3,
                    cy + 3,
                    fill=color,
                    outline="",
                    tags="overlay",
                )
            return

        if self.shape_start_image is None or end_image is None:
            return
        widget_w, widget_h, scale, offset_x, offset_y, img_w, img_h = self.metrics()
        geometry = editor_ops.resolve_shape_geometry(
            kind,
            self.shape_start_image,
            end_image,
            img_w,
            img_h,
        )
        if geometry is None:
            return
        start, end = geometry

        if kind == "line":
            coords = self._canvas_coords_for_image_points([start, end])
            self.canvas.create_line(*coords, fill=color, width=width, capstyle="round", tags="overlay")
            return

        if kind == "circle":
            cx, cy = editor.image_to_canvas(start[0], start[1], widget_w, widget_h, img_w, img_h)
            radius = editor_ops.shape_radius_from_center(start, end) * scale
            self.canvas.create_oval(
                cx - radius,
                cy - radius,
                cx + radius,
                cy + radius,
                outline=color,
                width=width,
                tags="overlay",
            )
            return

        if kind in editor_ops.SHAPE_REGULAR_BOX_KINDS:
            cx, cy, radius = editor_ops.shape_box_center_radius((*start, *end))
            if kind == "star":
                verts = editor_ops.star_vertices(cx, cy, radius)
            else:
                sides = editor_ops.SHAPE_POLYGON_SIDES[kind]
                verts = editor_ops.regular_polygon_vertices(cx, cy, radius, sides)
            if not verts:
                return
            coords = self._canvas_coords_for_image_points(verts + [verts[0]])
            self.canvas.create_polygon(*coords, outline=color, fill="", width=width, tags="overlay")
            return

        if kind in {"rectangle", "oval"}:
            coords = self._canvas_coords_for_image_points([start, (end[0], start[1]), end, (start[0], end[1]), start])
            x_coords = coords[0::2]
            y_coords = coords[1::2]
            bbox = (min(x_coords), min(y_coords), max(x_coords), max(y_coords))
            if kind == "rectangle":
                self.canvas.create_rectangle(*bbox, outline=color, width=width, tags="overlay")
            else:
                self.canvas.create_oval(*bbox, outline=color, width=width, tags="overlay")

    def _commit_shape_drag(self, end: tuple[float, float]):
        if self.shape_start_image is None or self.session.image is None:
            return
        if not self.var("shape_fill").get() and not self.var("shape_stroke").get():
            messagebox.showinfo(self.app._app_title(), self.t("editor_shape_need_style"))
            return
        kind = self.var("shape_kind").get()
        img_w, img_h = self.session.image.size
        geometry = editor_ops.resolve_shape_geometry(
            kind,
            self.shape_start_image,
            end,
            img_w,
            img_h,
        )
        if geometry is None:
            return
        start, resolved_end = geometry
        self.session.draw_shape_form(
            kind,
            start,
            resolved_end,
            fill_enabled=self.var("shape_fill").get(),
            fill_hex=self.shape_fill_color,
            fill_opacity=100,
            stroke_enabled=self.var("shape_stroke").get(),
            stroke_hex=self.shape_stroke_color,
            stroke_opacity=100,
            stroke_width=self.var("shape_stroke_width").get(),
        )
        self.invalidate_preview()
        self.refresh_canvas()

    def _commit_shape_curve(self):
        if len(self.shape_curve_points) < 2:
            return
        if not self.var("shape_fill").get() and not self.var("shape_stroke").get():
            messagebox.showinfo(self.app._app_title(), self.t("editor_shape_need_style"))
            return
        self.session.draw_shape_form(
            "curve",
            self.shape_curve_points[0],
            curve_points=list(self.shape_curve_points),
            fill_enabled=self.var("shape_fill").get(),
            stroke_enabled=self.var("shape_stroke").get(),
            fill_hex=self.shape_fill_color,
            fill_opacity=100,
            stroke_hex=self.shape_stroke_color,
            stroke_opacity=100,
            stroke_width=self.var("shape_stroke_width").get(),
        )
        self._reset_shape_state()
        self.invalidate_preview()
        self.refresh_canvas()

    def _build_shape_bar(self):
        row = tk.Frame(self.sub_toolbar_content, bg=EDITOR_THEME["bg"])
        row.pack(fill="x")
        self.shape_kind_buttons.clear()
        for kind, icon, label_key in (
            ("line", "shape_line", "editor_shape_line"),
            ("curve", "shape_curve", "editor_shape_curve"),
            ("rectangle", "shape_rect", "editor_shape_rect"),
            ("oval", "shape_oval", "editor_shape_oval"),
            ("circle", "shape_circle", "editor_shape_circle"),
            ("triangle", "shape_triangle", "editor_shape_triangle"),
            ("pentagon", "shape_pentagon", "editor_shape_pentagon"),
            ("hexagon", "shape_hexagon", "editor_shape_hexagon"),
            ("star", "shape_star", "editor_shape_star"),
        ):
            btn = self._icon_button(
                row,
                icon,
                lambda k=kind: self._set_shape_kind(k),
                size=self.SHAPE_TOOL_ICON_SIZE,
                tooltip_key=label_key,
            )
            btn._icon_name = icon
            btn.pack(side="left", padx=2)
            self.shape_kind_buttons[kind] = btn

        row2 = tk.Frame(self.sub_toolbar_content, bg=EDITOR_THEME["bg"])
        row2.pack(fill="x", pady=(6, 0))

        tk.Checkbutton(
            row2,
            text=self.t("editor_shape_fill"),
            variable=self.var("shape_fill"),
            bg=EDITOR_THEME["bg"],
            fg=EDITOR_THEME["text"],
            selectcolor=EDITOR_THEME["surface"],
            activebackground=EDITOR_THEME["bg"],
            activeforeground=EDITOR_THEME["text"],
        ).pack(side="left", padx=(0, 4))
        self._shape_fill_swatch = self._build_color_swatch(row2, self.shape_fill_color, self._pick_shape_fill_color)
        self._shape_fill_swatch.pack(side="left", padx=(0, 10))

        tk.Checkbutton(
            row2,
            text=self.t("editor_shape_stroke"),
            variable=self.var("shape_stroke"),
            bg=EDITOR_THEME["bg"],
            fg=EDITOR_THEME["text"],
            selectcolor=EDITOR_THEME["surface"],
            activebackground=EDITOR_THEME["bg"],
            activeforeground=EDITOR_THEME["text"],
        ).pack(side="left", padx=(0, 4))
        self._label(row2, self.t("editor_size")).pack(side="left", padx=(0, 2))
        self._draw_scale(row2, self.var("shape_stroke_width"), 1, 40).pack(side="left", padx=(0, 6))
        self._shape_stroke_swatch = self._build_color_swatch(row2, self.shape_stroke_color, self._pick_shape_stroke_color)
        self._shape_stroke_swatch.pack(side="left", padx=(0, 8))

        self._shape_hint = self._label(self.sub_toolbar_content, self.t("editor_shape_hint_box"))
        self._shape_hint.pack(fill="x", pady=(6, 0))
        self._refresh_shape_bar_state()

    def _selected_text_object(self) -> editor_text.TextObject | None:
        if not self._text_selected_id:
            return None
        return self.session.get_text_object(self._text_selected_id)

    def _sync_text_bar_from_object(self, obj: editor_text.TextObject | None):
        if obj is None:
            return
        self.var("text_font").set(obj.font_family)
        self.var("text_size").set(int(round(obj.font_size)))
        self.var("text_bold").set(obj.bold)
        self.var("text_italic").set(obj.italic)
        self.var("text_underline").set(obj.underline)
        self.var("text_strikethrough").set(obj.strikethrough)
        self.var("text_border").set(obj.border_enabled)
        self.var("text_border_width").set(obj.border_width)
        self.text_color = obj.color
        self.text_border_color = obj.border_color
        self._refresh_text_bar_state()

    def _apply_text_bar_to_object(self, obj: editor_text.TextObject | None):
        if obj is None:
            return
        obj.font_family = self.var("text_font").get()
        obj.font_size = float(self.var("text_size").get())
        obj.bold = self.var("text_bold").get()
        obj.italic = self.var("text_italic").get()
        obj.underline = self.var("text_underline").get()
        obj.strikethrough = self.var("text_strikethrough").get()
        obj.border_enabled = self.var("text_border").get()
        obj.border_width = int(self.var("text_border_width").get())
        obj.color = self.text_color
        obj.border_color = self.text_border_color

    def _refresh_text_bar_state(self):
        for key, button in self._text_format_buttons.items():
            active = self.var(f"text_{key}").get()
            self._set_toggle_button_active(button, active)
        self._refresh_color_swatch(getattr(self, "_text_color_swatch", None), self.text_color)
        self._refresh_color_swatch(getattr(self, "_text_border_color_swatch", None), self.text_border_color)
        border_row = getattr(self, "_text_border_row", None)
        if self._tk_alive(border_row):
            if self.var("text_border").get():
                border_row.pack(fill="x", pady=(6, 0))
            else:
                border_row.pack_forget()
        if self._text_editing_id and self._text_edit_widget is not None:
            self._refresh_text_edit_widget()

    def _toggle_text_style(self, key: str):
        var = self.var(f"text_{key}")
        var.set(not var.get())
        obj = self._selected_text_object()
        if obj is not None:
            self._apply_text_bar_to_object(obj)
            self.invalidate_preview()
            self.refresh_canvas()
        self._refresh_text_bar_state()

    def _on_text_font_change(self, *_args):
        obj = self._selected_text_object()
        if obj is not None:
            self._apply_text_bar_to_object(obj)
            self.invalidate_preview()
            self.refresh_canvas()
        self._refresh_text_bar_state()

    def _on_text_size_change(self, *_args):
        obj = self._selected_text_object()
        if obj is not None:
            self._apply_text_bar_to_object(obj)
            self.invalidate_preview()
            self.refresh_canvas()
        self._refresh_text_bar_state()

    def _on_text_border_toggle(self):
        obj = self._selected_text_object()
        if obj is not None:
            self._apply_text_bar_to_object(obj)
            self.invalidate_preview()
            self.refresh_canvas()
        self._refresh_text_bar_state()

    def _pick_text_color(self):
        color = colorchooser.askcolor(color=self.text_color, title=self.t("editor_text_color"))
        if color and color[1]:
            self.text_color = color[1]
            obj = self._selected_text_object()
            if obj is not None:
                obj.color = self.text_color
                self.invalidate_preview()
                self.refresh_canvas()
            self._refresh_text_bar_state()

    def _pick_text_border_color(self):
        color = colorchooser.askcolor(color=self.text_border_color, title=self.t("editor_text_border_color"))
        if color and color[1]:
            self.text_border_color = color[1]
            obj = self._selected_text_object()
            if obj is not None:
                obj.border_color = self.text_border_color
                self.var("text_border").set(True)
                self.invalidate_preview()
                self.refresh_canvas()
            self._refresh_text_bar_state()

    def _autosize_text_edit(self, widget: tk.Text, obj: editor_text.TextObject, scale: float):
        content = widget.get("1.0", "end-1c")
        lines = content.split("\n") if content else [""]
        widget.configure(width=max(4, max(len(line) for line in lines) + 1), height=max(1, len(lines)))

    def _refresh_text_edit_widget(self):
        obj = self.session.get_text_object(self._text_editing_id) if self._text_editing_id else None
        widget = self._text_edit_widget
        if obj is None or widget is None or not widget.winfo_exists():
            return
        width, height, scale, offset_x, offset_y, img_w, img_h = self.metrics()
        widget.configure(
            font=editor_text.tk_font_tuple(obj, scale),
            fg=obj.color,
            insertbackground=obj.color,
        )
        cx, cy = editor.image_to_canvas(obj.x, obj.y, width, height, img_w, img_h)
        if self._text_edit_window is not None:
            self.canvas.coords(self._text_edit_window, cx, cy)
        self._autosize_text_edit(widget, obj, scale)

    def _finish_text_edit(self):
        if self._text_editing_id is None:
            return
        obj = self.session.get_text_object(self._text_editing_id)
        if self._text_edit_widget is not None and self._text_edit_widget.winfo_exists() and obj is not None:
            obj.text = self._text_edit_widget.get("1.0", "end-1c")
        if self._text_edit_window is not None:
            self.canvas.delete(self._text_edit_window)
        if self._text_edit_frame is not None and self._text_edit_frame.winfo_exists():
            self._text_edit_frame.destroy()
        self._text_edit_widget = None
        self._text_edit_frame = None
        self._text_edit_window = None
        self._text_editing_id = None
        if obj is not None and not obj.text.strip():
            self.session.text_objects = [item for item in self.session.text_objects if item.id != obj.id]
            self._text_selected_id = None
        self.invalidate_preview()
        self.refresh_canvas()

    def _start_text_edit(self, obj: editor_text.TextObject):
        self._finish_text_edit()
        self._text_editing_id = obj.id
        self._text_selected_id = obj.id
        width, height, scale, offset_x, offset_y, img_w, img_h = self.metrics()
        cx, cy = editor.image_to_canvas(obj.x, obj.y, width, height, img_w, img_h)
        frame = tk.Frame(
            self.canvas,
            bg=EDITOR_THEME["surface"],
            bd=0,
            highlightthickness=1,
            highlightbackground=EDITOR_THEME["accent"],
        )
        text_widget = tk.Text(
            frame,
            font=editor_text.tk_font_tuple(obj, scale),
            fg=obj.color,
            bg=EDITOR_THEME["surface"],
            insertbackground=obj.color,
            insertwidth=2,
            relief="flat",
            bd=0,
            wrap="word",
            height=1,
            width=max(4, len(obj.text) + 2),
            highlightthickness=0,
        )
        if obj.text:
            text_widget.insert("1.0", obj.text)
        text_widget.pack(fill="both", expand=True, padx=2, pady=2)

        def on_modified(_event=None):
            if not text_widget.edit_modified():
                return
            text_widget.edit_modified(False)
            if obj is None:
                return
            obj.text = text_widget.get("1.0", "end-1c")
            self._autosize_text_edit(text_widget, obj, scale)
            self.invalidate_preview()
            self.refresh_canvas()

        text_widget.bind("<<Modified>>", on_modified)
        text_widget.bind("<Return>", lambda _e: self._finish_text_edit() or "break")
        text_widget.bind("<Escape>", lambda _e: self._finish_text_edit() or "break")
        self._text_edit_frame = frame
        self._text_edit_widget = text_widget
        self._text_edit_window = self.canvas.create_window(cx, cy, window=frame, anchor="nw", tags="text_edit")
        self.canvas.update_idletasks()
        text_widget.focus_set()
        text_widget.focus_force()
        self.canvas.tag_raise("text_edit")

    def _create_text_at(self, point: tuple[float, float]):
        obj = editor_text.new_text_object(
            point[0],
            point[1],
            font_family=self.var("text_font").get(),
            font_size=float(self.var("text_size").get()),
            color=self.text_color,
            bold=self.var("text_bold").get(),
            italic=self.var("text_italic").get(),
            underline=self.var("text_underline").get(),
            strikethrough=self.var("text_strikethrough").get(),
            border_enabled=self.var("text_border").get(),
            border_color=self.text_border_color,
            border_width=int(self.var("text_border_width").get()),
        )
        self.session.add_text_object(obj)
        self._text_selected_id = obj.id
        self._sync_text_bar_from_object(obj)
        self._start_text_edit(obj)

    def _select_text_object(self, obj: editor_text.TextObject):
        self._finish_text_edit()
        self._text_selected_id = obj.id
        self._sync_text_bar_from_object(obj)
        self.refresh_canvas()

    def _delete_selected_text(self):
        if not self._text_selected_id:
            return
        self._finish_text_edit()
        self.session.remove_text_object(self._text_selected_id)
        self._text_selected_id = None
        self.invalidate_preview()
        self.refresh_canvas()

    def _draw_text_overlays(self, scale: float, offset_x: float, offset_y: float, img_w: int, img_h: int):
        self.canvas.delete("text_overlay")
        width, height = self.metrics()[0], self.metrics()[1]
        for obj in self.session.text_objects:
            if obj.id == self._text_editing_id:
                continue
            x0, y0, x1, y1 = editor_text.measure_text_object(obj)
            cx0, cy0 = editor.image_to_canvas(x0, y0, width, height, img_w, img_h)
            cx1, cy1 = editor.image_to_canvas(x1, y1, width, height, img_w, img_h)
            left, top, right, bottom = min(cx0, cx1), min(cy0, cy1), max(cx0, cx1), max(cy0, cy1)
            selected = obj.id == self._text_selected_id
            color = EDITOR_THEME["accent"] if selected else EDITOR_THEME["muted"]
            self.canvas.create_rectangle(
                left - 2,
                top - 2,
                right + 2,
                bottom + 2,
                outline=color,
                width=2 if selected else 1,
                dash=() if selected else (3, 2),
                tags="text_overlay",
            )
            if selected:
                for hx, hy in ((left, top), (right, top), (left, bottom), (right, bottom)):
                    self.canvas.create_rectangle(
                        hx - 4,
                        hy - 4,
                        hx + 4,
                        hy + 4,
                        fill=EDITOR_THEME["accent"],
                        outline="",
                        tags="text_overlay",
                    )

    def _text_resize_from_pointer(self, obj: editor_text.TextObject, pointer: tuple[float, float]):
        if self._text_drag_box_origin is None or self._text_drag_handle is None:
            return
        x0, y0, x1, y1 = self._text_drag_box_origin
        old_w = max(1.0, x1 - x0)
        old_h = max(1.0, y1 - y0)
        handle = self._text_drag_handle
        px, py = pointer
        if handle == "se":
            new_w = max(12.0, px - x0)
            new_h = max(12.0, py - y0)
        elif handle == "sw":
            new_w = max(12.0, x1 - px)
            new_h = max(12.0, py - y0)
            obj.x = px
        elif handle == "ne":
            new_w = max(12.0, px - x0)
            new_h = max(12.0, y1 - py)
            obj.y = py
        else:
            new_w = max(12.0, x1 - px)
            new_h = max(12.0, y1 - py)
            obj.x = px
            obj.y = py
        factor = min(new_w / old_w, new_h / old_h)
        obj.font_size = max(8.0, self._text_drag_size_origin * factor)

    def _handle_text_press(self, point: tuple[float, float]):
        self._finish_text_edit()
        hit = editor_text.find_object_at(self.session.text_objects, point[0], point[1])
        if hit is not None:
            self._text_selected_id = hit.id
            self._sync_text_bar_from_object(hit)
            handle = editor_text.hit_text_handle(hit, point[0], point[1])
            self._text_drag_origin = point
            if handle is not None:
                self.session.snapshot()
                self._text_dragging = True
                self._text_drag_mode = "resize"
                self._text_drag_handle = handle
                self._text_drag_box_origin = editor_text.measure_text_object(hit)
                self._text_drag_size_origin = hit.font_size
            else:
                self._text_pending_move_id = hit.id
                self._text_drag_object_origin = (hit.x, hit.y)
            self.refresh_canvas()
            return
        self._create_text_at(point)

    def _handle_text_drag(self, point: tuple[float, float]):
        if self._text_pending_move_id and not self._text_dragging and self._text_drag_origin is not None:
            if editor_ops.shape_drag_distance(self._text_drag_origin, point) >= editor_ops.SHAPE_CLICK_DRAG_THRESHOLD:
                self.session.snapshot()
                self._text_dragging = True
                self._text_drag_mode = "move"
        obj = self._selected_text_object()
        if not self._text_dragging or obj is None or self._text_drag_origin is None:
            return
        if self._text_drag_mode == "move" and self._text_drag_object_origin is not None:
            dx = point[0] - self._text_drag_origin[0]
            dy = point[1] - self._text_drag_origin[1]
            obj.x = self._text_drag_object_origin[0] + dx
            obj.y = self._text_drag_object_origin[1] + dy
            self.invalidate_preview()
            self.refresh_canvas()
            return
        if self._text_drag_mode == "resize":
            self._text_resize_from_pointer(obj, point)
            self.invalidate_preview()
            self.refresh_canvas()

    def _handle_text_release(self):
        self._text_pending_move_id = None
        if not self._text_dragging:
            self._text_drag_origin = None
            self._text_drag_object_origin = None
            return
        self._text_dragging = False
        self._text_drag_mode = None
        self._text_drag_handle = None
        self._text_drag_origin = None
        self._text_drag_box_origin = None
        self._text_drag_size_origin = 0.0
        self._text_drag_object_origin = None

    def _build_text_bar(self):
        row = tk.Frame(self.sub_toolbar_content, bg=EDITOR_THEME["bg"])
        row.pack(fill="x")
        self._label(row, self.t("editor_text_font")).pack(side="left", padx=(0, 4))
        fonts = editor_text.list_font_families()
        menu = tk.OptionMenu(row, self.var("text_font"), *fonts, command=lambda _v: self._on_text_font_change())
        menu.configure(
            bg=EDITOR_THEME["btn"],
            fg=EDITOR_THEME["btn_text"],
            activebackground=EDITOR_THEME["btn_active"],
            activeforeground=EDITOR_THEME["btn_text"],
            highlightthickness=0,
            relief="flat",
        )
        menu["menu"].configure(bg=EDITOR_THEME["surface"], fg=EDITOR_THEME["text"])
        menu.pack(side="left", padx=(0, 8))
        self._label(row, self.t("editor_text_size")).pack(side="left", padx=(0, 4))
        size_scale = self._draw_scale(row, self.var("text_size"), 12, 160)
        size_scale.pack(side="left", padx=(0, 8))
        self.var("text_size").trace_add("write", self._on_text_size_change)

        row2 = tk.Frame(self.sub_toolbar_content, bg=EDITOR_THEME["bg"])
        row2.pack(fill="x", pady=(6, 0))
        for key, label in (("bold", "B"), ("italic", "I"), ("underline", "U"), ("strikethrough", "S")):
            btn = self._button(
                row2,
                label,
                lambda k=key: self._toggle_text_style(k),
                width=3,
                toggle=True,
            )
            btn.pack(side="left", padx=2)
            self._text_format_buttons[key] = btn
        self._text_color_swatch = self._build_color_swatch(row2, self.text_color, self._pick_text_color)
        self._text_color_swatch.pack(side="left", padx=(8, 4))
        tk.Checkbutton(
            row2,
            text=self.t("editor_text_border"),
            variable=self.var("text_border"),
            command=self._on_text_border_toggle,
            bg=EDITOR_THEME["bg"],
            fg=EDITOR_THEME["text"],
            selectcolor=EDITOR_THEME["surface"],
            activebackground=EDITOR_THEME["bg"],
            activeforeground=EDITOR_THEME["text"],
        ).pack(side="left", padx=(8, 0))

        self._text_border_row = tk.Frame(self.sub_toolbar_content, bg=EDITOR_THEME["bg"])
        self._label(self._text_border_row, self.t("editor_size")).pack(side="left", padx=(0, 4))
        border_scale = self._draw_scale(self._text_border_row, self.var("text_border_width"), 1, 20)
        border_scale.pack(side="left", padx=(0, 8))
        self.var("text_border_width").trace_add("write", lambda *_a: self._on_text_border_toggle())
        self._text_border_color_swatch = self._build_color_swatch(
            self._text_border_row,
            self.text_border_color,
            self._pick_text_border_color,
        )
        self._text_border_color_swatch.pack(side="left", padx=(0, 8))

        self._text_hint = self._label(self.sub_toolbar_content, self.t("editor_text_hint"))
        self._text_hint.pack(fill="x", pady=(6, 0))
        self._refresh_text_bar_state()

    def refresh_history(self):
        if not hasattr(self, "history_tree"):
            return
        tree = self.history_tree
        tree.delete(*tree.get_children())
        self.history_items.clear()
        root = Path(self.app.editor_folder_var.get() or Path.home() / "Downloads" / "FissileKit")
        groups = editor.scan_media_folder(root)
        for group_id, kind, label_key in (
            ("group-image", "image", "editor_group_images"),
            ("group-video", "video", "editor_group_videos"),
            ("group-audio", "audio", "editor_group_audio"),
        ):
            items = groups.get(kind, [])
            tree.insert("", "end", iid=group_id, text=self.t(label_key, count=len(items)), open=True)
            for path in items:
                item_id = f"file-{len(self.history_items)}"
                self.history_items[item_id] = path
                tree.insert(group_id, "end", iid=item_id, text=path.name)

    def _on_history_select(self, _event=None):
        selection = self.history_tree.selection()
        if not selection:
            return
        path = self.history_items.get(selection[0])
        if path is not None:
            self.load_path(path)

    def pick_file(self):
        selected = filedialog.askopenfilename(
            title=self.t("tab_editor"),
            filetypes=self.app._editor_filetypes(),
            initialdir=self.app.editor_folder_var.get() or str(Path.home() / "Downloads" / "FissileKit"),
        )
        if selected:
            self.load_path(Path(selected))

    def load_path(self, path: Path):
        try:
            ffmpeg_path = self.app._editor_ffmpeg_location()
            self.session.load(path, ffmpeg_location=ffmpeg_path)
        except Exception as error:
            messagebox.showerror(self.app._app_title(), str(error))
            return
        if self.session.image is not None:
            self.var("resize_w").set(str(self.session.image.width))
            self.var("resize_h").set(str(self.session.image.height))
        self.exit_tool(force=True)
        self.invalidate_preview()
        self.refresh_canvas()
        message = self.t("editor_loaded", name=path.name)
        self.app.detail_var.set(message)
        self.app._log(message)

    def metrics(self):
        width = max(self.canvas.winfo_width(), 1)
        height = max(self.canvas.winfo_height(), 1)
        if self._canvas_layout_active():
            canvas_w, canvas_h = self._canvas_dims()
            scale, offset_x, offset_y, _, _ = editor.display_metrics(width, height, canvas_w, canvas_h)
            return width, height, scale, offset_x, offset_y, canvas_w, canvas_h
        image = self.session.image
        if image is None:
            return width, height, 1.0, 0.0, 0.0, 0, 0
        scale, offset_x, offset_y, _, _ = editor.display_metrics(width, height, image.width, image.height)
        return width, height, scale, offset_x, offset_y, image.width, image.height

    def canvas_point(self, event):
        width, height, scale, offset_x, offset_y, img_w, img_h = self.metrics()
        if img_w <= 0:
            return None
        return editor.canvas_to_image(event.x, event.y, width, height, img_w, img_h)

    def canvas_point_for_shape(self, event):
        width, height, scale, offset_x, offset_y, img_w, img_h = self.metrics()
        if img_w <= 0:
            return None
        return editor.canvas_to_image_clamped(event.x, event.y, width, height, img_w, img_h)

    def invalidate_preview(self):
        self._preview_dirty = True

    def _on_canvas_configure(self, _event):
        if self._configure_after_id is not None:
            self.canvas.after_cancel(self._configure_after_id)
        self._configure_after_id = self.canvas.after(120, self._on_canvas_configure_delayed)

    def _on_canvas_configure_delayed(self):
        self._configure_after_id = None
        self.invalidate_preview()
        self.refresh_canvas()

    def _composite_for_canvas(self) -> Image.Image | None:
        if self._canvas_layout_active():
            canvas_w, canvas_h = self._canvas_dims()
            base, stroke = editor_ops.compose_canvas_layout(
                self._canvas_source_image,
                self._canvas_source_stroke,
                canvas_w,
                canvas_h,
                self._canvas_placement_x,
                self._canvas_placement_y,
                self._canvas_content_scale,
            )
            if stroke is not None:
                return Image.alpha_composite(base.convert("RGBA"), stroke)
            return base
        return self.session.composite(
            exclude_text_ids={self._text_editing_id} if self._text_editing_id else None,
        )

    def _clear_canvas_drawables(self):
        for tag in (
            "base",
            "overlay",
            "stroke_preview",
            "rotate_label",
            "eyedropper_feedback",
            "text_overlay",
        ):
            self.canvas.delete(tag)

    def _raise_text_edit_layer(self):
        if self._text_editing_id and self.canvas.find_withtag("text_edit"):
            self.canvas.tag_raise("text_edit")
            self._refresh_text_edit_widget()

    def refresh_canvas(self, overlay_only: bool = False):
        if self._rotate_dragging or self._canvas_dragging or self._canvas_handle_resizing:
            return
        canvas = self.canvas
        width = max(canvas.winfo_width(), 1)
        height = max(canvas.winfo_height(), 1)
        image = self._composite_for_canvas()
        if image is None:
            if overlay_only and self.canvas_photo is not None and not self._preview_dirty:
                return
            self._clear_canvas_drawables()
            canvas.create_text(
                width / 2,
                height / 2,
                text=self.t("editor_click_add"),
                fill=EDITOR_THEME["muted"],
                font=("Segoe UI", 11),
            )
            self.canvas_photo = None
            self._preview_dirty = False
            self._raise_text_edit_layer()
            return

        img_w, img_h = image.width, image.height
        scale, offset_x, offset_y, display_w, display_h = editor.display_metrics(width, height, img_w, img_h)

        if overlay_only and self.canvas_photo is not None and not self._preview_dirty:
            canvas.delete("overlay")
            self._draw_tool_overlays(scale, offset_x, offset_y, img_w, img_h)
            self._raise_text_edit_layer()
            return

        if (
            not self._preview_dirty
            and self.canvas_photo is not None
            and not self._rotate_dragging
            and self.canvas.find_withtag("base")
        ):
            canvas.delete("overlay")
            canvas.delete("stroke_preview")
            self._draw_tool_overlays(scale, offset_x, offset_y, img_w, img_h)
            self._raise_text_edit_layer()
            return

        self._clear_canvas_drawables()
        fast = self.stroke_active or self._crop_interacting or self._rotate_dragging
        resample = Image.Resampling.BILINEAR if fast else Image.Resampling.LANCZOS
        preview_source = image
        if self.active_tool == "crop" and self.crop_box is not None and not self._crop_interacting:
            preview_source = editor_ops.darken_outside_box(image, self.crop_box)
        preview = preview_source.copy()
        preview.thumbnail(
            (max(1, int(img_w * scale)), max(1, int(img_h * scale))),
            resample,
        )
        self.canvas_photo = ImageTk.PhotoImage(preview)
        canvas.create_image(offset_x, offset_y, anchor="nw", image=self.canvas_photo, tags="base")
        self._preview_dirty = False
        self._draw_tool_overlays(scale, offset_x, offset_y, img_w, img_h)
        self._raise_text_edit_layer()

    def _draw_stroke_preview(self, mode: str):
        self.canvas.delete("stroke_preview")
        if not self.stroke_points:
            return
        width, height, scale, offset_x, offset_y, img_w, img_h = self.metrics()
        if mode == "pencil":
            color = self.draw_color
        else:
            color = "#ffffff"
        line_width = max(1, int(round(self.var("draw_size").get() * scale)))
        coords: list[float] = []
        for px, py in self.stroke_points:
            cx, cy = editor.image_to_canvas(px, py, width, height, img_w, img_h)
            coords.extend((cx, cy))
        if len(coords) >= 4:
            self.canvas.create_line(
                *coords,
                fill=color,
                width=line_width,
                capstyle="round",
                joinstyle="round",
                smooth=True,
                tags="stroke_preview",
            )
        elif len(coords) == 2:
            x, y = coords
            r = line_width
            self.canvas.create_oval(
                x - r,
                y - r,
                x + r,
                y + r,
                fill=color,
                outline="",
                tags="stroke_preview",
            )

    def _commit_stroke(self, mode: str):
        if not self.stroke_points:
            return
        if mode == "pencil":
            self.session.apply_draw(
                self.stroke_points,
                self.draw_color,
                self.var("draw_size").get(),
                self.var("draw_opacity").get(),
                "pencil",
            )
        elif mode == "eraser":
            self.session.apply_eraser(
                "manual",
                self.stroke_points[-1][0],
                self.stroke_points[-1][1],
                self.stroke_points,
                0,
                self.var("draw_size").get(),
            )

    def _refresh_crop_overlay_only(self):
        if self._crop_overlay_after_id is not None:
            return
        self._crop_overlay_after_id = self.canvas.after(8, self._flush_crop_overlay)

    def _flush_crop_overlay(self):
        self._crop_overlay_after_id = None
        if self.active_tool != "crop" or self.crop_box is None:
            return
        self.canvas.delete("overlay")
        width, height, scale, offset_x, offset_y, img_w, img_h = self.metrics()
        self._draw_tool_overlays(scale, offset_x, offset_y, img_w, img_h)

    def _schedule_rotate_refresh(self):
        if self._rotate_refresh_after_id is not None:
            return
        self._rotate_refresh_after_id = self.canvas.after(10, self._flush_rotate_refresh)

    def _flush_rotate_refresh(self):
        self._rotate_refresh_after_id = None
        if not self._rotate_dragging or self.active_tool != "rotate":
            return
        self._paint_rotate_drag_frame()

    def _cache_rotate_drag_display(self):
        composite = self.session.composite()
        if composite is None:
            self._rotate_drag_display = None
            return
        width = max(self.canvas.winfo_width(), 1)
        height = max(self.canvas.winfo_height(), 1)
        img_w, img_h = composite.size
        scale, _offset_x, _offset_y, display_w, display_h = editor.display_metrics(
            width, height, img_w, img_h
        )
        preview = composite.copy()
        preview.thumbnail(
            (max(1, int(img_w * scale)), max(1, int(img_h * scale))),
            Image.Resampling.BILINEAR,
        )
        self._rotate_drag_display = preview

    def _rotate_drag_delta(self) -> float:
        return self._rotate_wheel_angle - self._rotate_angle_at_drag_start

    def _paint_rotate_drag_frame(self):
        if self._rotate_drag_display is None:
            return
        wheel = self._rotate_wheel_metrics()
        if wheel is None:
            return
        center_x, center_y, radius = wheel
        preview_delta = self._rotate_drag_delta()
        if abs(preview_delta) < 0.01:
            rotated = self._rotate_drag_display
        else:
            rotated = editor_ops.rotate_free_preview(self._rotate_drag_display, preview_delta)
        self._rotate_drag_photo = ImageTk.PhotoImage(rotated)
        self.canvas.delete("base", "overlay", "rotate_label")
        self.canvas.create_image(center_x, center_y, anchor="center", image=self._rotate_drag_photo, tags="base")
        self._draw_rotate_overlay(center_x, center_y, radius)
        if abs(preview_delta) >= 0.5:
            self.canvas.create_text(
                center_x,
                center_y - radius - 16,
                text=f"{preview_delta:.0f}°",
                fill=EDITOR_THEME["text"],
                font=("Segoe UI", 13, "bold"),
                tags="rotate_label",
            )

    def _draw_rotate_overlay(self, center_x, center_y, radius):
        handle_angle = self._rotate_wheel_angle
        snapped_tick = int(round(handle_angle / editor_ops.ROTATE_WHEEL_TICK_STEP)) * editor_ops.ROTATE_WHEEL_TICK_STEP
        snapped_tick = snapped_tick % 360
        if snapped_tick < 0:
            snapped_tick += 360
        is_snapped = (
            abs(handle_angle - round(handle_angle / editor_ops.ROTATE_WHEEL_TICK_STEP) * editor_ops.ROTATE_WHEEL_TICK_STEP)
            < 0.1
        )
        self.canvas.create_oval(
            center_x - radius,
            center_y - radius,
            center_x + radius,
            center_y + radius,
            outline=EDITOR_THEME["accent"],
            width=2,
            tags="overlay",
        )
        tick_inner = radius * 0.88
        tick_outer = radius * 1.04
        for angle in editor_ops.rotate_wheel_tick_angles():
            inner_x, inner_y = editor_ops.rotate_point_on_wheel(center_x, center_y, tick_inner, angle)
            outer_x, outer_y = editor_ops.rotate_point_on_wheel(center_x, center_y, tick_outer, angle)
            tick_color = EDITOR_THEME["accent"] if is_snapped and angle == snapped_tick else EDITOR_THEME["text"]
            tick_width = 3 if is_snapped and angle == snapped_tick else 2
            self.canvas.create_line(
                inner_x,
                inner_y,
                outer_x,
                outer_y,
                fill=tick_color,
                width=tick_width,
                tags="overlay",
            )
        handle_x, handle_y = editor_ops.rotate_point_on_wheel(
            center_x,
            center_y,
            radius,
            handle_angle,
        )
        handle_r = editor_ops.ROTATE_HANDLE_VISUAL_RADIUS
        self.canvas.create_oval(
            handle_x - handle_r,
            handle_y - handle_r,
            handle_x + handle_r,
            handle_y + handle_r,
            fill=EDITOR_THEME["accent"],
            outline=EDITOR_THEME["text"],
            width=2,
            tags="overlay",
        )

    def _rotate_wheel_metrics(self):
        width = max(self.canvas.winfo_width(), 1)
        height = max(self.canvas.winfo_height(), 1)
        if self.session.image is None:
            return None
        img_w, img_h = self.session.image.size
        _scale, offset_x, offset_y, display_w, display_h = editor.display_metrics(width, height, img_w, img_h)
        center_x, center_y, radius = editor_ops.rotate_wheel_geometry(offset_x, offset_y, display_w, display_h)
        return center_x, center_y, radius

    def _begin_rotate_drag(self, event):
        wheel = self._rotate_wheel_metrics()
        if wheel is None:
            return False
        center_x, center_y, radius = wheel
        if not editor_ops.hit_rotate_handle(
            event.x,
            event.y,
            center_x,
            center_y,
            radius,
            self._rotate_wheel_angle,
        ):
            return False
        if self.session.image is None:
            return False
        self._cache_rotate_drag_display()
        if self._rotate_drag_display is None:
            return False
        self._rotate_angle_at_drag_start = self._rotate_wheel_angle
        self._rotate_dragging = True
        self._rotate_start_pointer_angle = editor_ops.rotate_pointer_angle_from_top(center_x, center_y, event.x, event.y)
        self._paint_rotate_drag_frame()
        return True

    def _update_rotate_drag(self, event):
        wheel = self._rotate_wheel_metrics()
        if wheel is None or not self._rotate_dragging:
            return
        center_x, center_y, _radius = wheel
        current_angle = editor_ops.rotate_pointer_angle_from_top(center_x, center_y, event.x, event.y)
        raw_delta = editor_ops.rotate_angle_delta_degrees(
            self._rotate_start_pointer_angle,
            current_angle,
        )
        self._rotate_wheel_angle = editor_ops.snap_rotate_angle(self._rotate_angle_at_drag_start + raw_delta)
        self._schedule_rotate_refresh()

    def _commit_rotate_drag(self):
        if self._rotate_dragging:
            delta = self._rotate_drag_delta()
            if abs(delta) > 0.01:
                self.session.rotate(delta)
        self._clear_rotate_drag()
        self.invalidate_preview()
        self.refresh_canvas()

    def _draw_crop_overlay(self, scale, offset_x, offset_y):
        left, top, right, bottom = self.crop_box
        x0 = offset_x + left * scale
        y0 = offset_y + top * scale
        x1 = offset_x + right * scale
        y1 = offset_y + bottom * scale
        self.canvas.create_rectangle(x0, y0, x1, y1, outline=EDITOR_THEME["accent"], width=2, tags="overlay")
        corners_only = self._crop_aspect_locked()
        handles = editor_ops.crop_handle_canvas_positions(
            self.crop_box,
            scale,
            offset_x,
            offset_y,
            corners_only=corners_only,
        )
        radius = editor_ops.CROP_HANDLE_VISUAL_RADIUS
        for cx, cy in handles.values():
            self.canvas.create_oval(
                cx - radius,
                cy - radius,
                cx + radius,
                cy + radius,
                fill=EDITOR_THEME["accent"],
                outline=EDITOR_THEME["text"],
                width=1,
                tags="overlay",
            )

    def _safe_canvas(self, handler, event):
        try:
            handler(event)
        except Exception as error:
            messagebox.showerror(self.app._app_title(), str(error))

    def _canvas_press(self, event):
        if self.session.image is None:
            self.pick_file()
            return
        tool = self.active_tool
        if tool == "resize" and self.var("resize_mode").get() == "canvas":
            if self._canvas_free_aspect() and self._begin_canvas_handle_drag(event):
                return
            if self._begin_canvas_drag(event):
                return
            return
        point = self.canvas_point(event)
        if point is None:
            return
        if tool == "rotate":
            if self._begin_rotate_drag(event):
                return
            return
        if tool == "crop":
            if self.crop_box is None:
                return
            mode = self.var("crop_mode").get()
            can_use_handles = mode == "handles" or self.crop_drag_phase == "review"
            if can_use_handles:
                width, height, scale, offset_x, offset_y, img_w, img_h = self.metrics()
                handle = editor_ops.hit_crop_handle(
                    event.x,
                    event.y,
                    self.crop_box,
                    scale,
                    offset_x,
                    offset_y,
                    handle_size=editor_ops.CROP_HANDLE_HIT_RADIUS,
                    corners_only=self._crop_aspect_locked(),
                )
                if handle:
                    self._crop_interacting = True
                    self.crop_handle = handle
                    self.crop_drag_origin = self.crop_box
                    self.crop_drag_start = (event.x, event.y)
                    return
            if mode == "drag" and self.crop_drag_phase != "review":
                self._crop_interacting = True
                self.crop_drag_phase = "drawing"
                self.crop_drag_active = True
                self.shape_start_canvas = (event.x, event.y)
                self.shape_start_image = point
            return
        if tool == "text":
            self._handle_text_press(point)
            return
        if tool == "draw":
            mode = self.var("draw_mode").get()
            if mode == "eyedropper":
                self._pick_color_at(point, event.x, event.y)
                return
            if mode == "bucket":
                self.session.snapshot()
                self.canvas.configure(cursor="watch")
                self.canvas.update_idletasks()
                self.session.bucket_fill_at(
                    point[0],
                    point[1],
                    self.draw_color,
                    self.var("draw_opacity").get(),
                    self.var("draw_tolerance").get(),
                )
                self._update_draw_cursor()
                self.invalidate_preview()
                self.refresh_canvas()
                return
            if mode in {"pencil", "eraser"}:
                self.session.snapshot()
                self.stroke_active = True
                self.stroke_points = [point]
                self.last_point = point
            return
        if tool == "shape":
            kind = self.var("shape_kind").get()
            if kind == "curve":
                if self._shape_ignore_next_click:
                    self._shape_ignore_next_click = False
                    return
                self.shape_curve_points.append(point)
                self._refresh_shape_overlay()
                return
            self.shape_dragging = True
            self.shape_start_canvas = (event.x, event.y)
            self.shape_start_image = point
            return

    def _canvas_drag(self, event):
        tool = self.active_tool
        if tool == "resize" and self._canvas_handle_resizing:
            self._update_canvas_handle_drag(event)
            return
        if tool == "resize" and self._canvas_dragging:
            self._update_canvas_drag(event)
            return
        if tool == "rotate" and self._rotate_dragging:
            self._update_rotate_drag(event)
            return
        if tool == "crop" and self.crop_box is not None:
            width, height, scale, offset_x, offset_y, img_w, img_h = self.metrics()
            aspect_key = self.var("crop_aspect").get()
            aspect = editor_ops.CROP_ASPECTS.get(aspect_key)
            mode = self.var("crop_mode").get()
            can_use_handles = (
                (mode == "handles" or self.crop_drag_phase == "review")
                and self.crop_handle
                and self.crop_drag_origin
                and self.crop_drag_start
            )
            if can_use_handles:
                dx = (event.x - self.crop_drag_start[0]) / scale
                dy = (event.y - self.crop_drag_start[1]) / scale
                aspect = editor_ops.CROP_ASPECTS.get(aspect_key)
                locked = aspect is not None
                self.crop_box = editor_ops.resize_crop_box_by_handle(
                    self.crop_drag_origin,
                    self.crop_handle,
                    dx,
                    dy,
                    img_w,
                    img_h,
                    aspect if locked and self.crop_handle in editor_ops.CORNER_HANDLES else None,
                )
                self._refresh_crop_overlay_only()
                return
            if mode == "drag" and self.crop_drag_phase == "drawing" and self.crop_drag_active and self.shape_start_image is not None:
                end = self.canvas_point(event)
                if end is not None:
                    x0, y0 = self.shape_start_image
                    x1, y1 = end
                    aspect = editor_ops.CROP_ASPECTS.get(self.var("crop_aspect").get())
                    self.crop_box = editor_ops.crop_box_from_drag_anchor(
                        (x0, y0),
                        (x1, y1),
                        img_w,
                        img_h,
                        aspect,
                    )
                    self._refresh_crop_overlay_only()
                return
        if tool == "shape":
            kind = self.var("shape_kind").get()
            end = self.canvas_point_for_shape(event)
            if end is not None:
                self._refresh_shape_overlay(end_image=end)
            return
        if tool == "text":
            point = self.canvas_point(event)
            if point is not None:
                self._handle_text_drag(point)
            return
        if tool == "draw":
            mode = self.var("draw_mode").get()
            if mode in {"pencil", "eraser"} and self.stroke_active and self.last_point is not None:
                point = self.canvas_point(event)
                if point is None:
                    return
                segment = editor_ops.interpolate_segment(
                    self.last_point,
                    point,
                    step=editor_ops.brush_interpolation_step(self.var("draw_size").get()),
                )
                self.stroke_points.extend(segment)
                self._draw_stroke_preview(mode)
                self.last_point = point
            return

    def _canvas_release(self, event):
        if self._canvas_dragging or self._canvas_handle_resizing:
            self._commit_canvas_interaction()
            return
        if self.active_tool == "rotate" and self._rotate_dragging:
            self._commit_rotate_drag()
            return
        if self.active_tool == "text":
            self._handle_text_release()
            return
        if self.active_tool == "shape":
            kind = self.var("shape_kind").get()
            if kind != "curve" and self.shape_start_image is not None:
                end = self.canvas_point_for_shape(event)
                if end is not None:
                    self._commit_shape_drag(end)
                self._reset_shape_state()
                self.invalidate_preview()
                self.refresh_canvas()
                return
        self.crop_handle = None
        self.crop_drag_origin = None
        self.crop_drag_start = None
        if self.active_tool == "crop":
            if self._crop_interacting:
                self._crop_interacting = False
                self.invalidate_preview()
                self.refresh_canvas()
            was_drawing = self.crop_drag_phase == "drawing" and self.var("crop_mode").get() == "drag"
            self.crop_drag_active = False
            if was_drawing and self.crop_box is not None:
                width, height = self.session.image.size
                if self.crop_box != (0, 0, width, height):
                    self.crop_drag_phase = "review"
                    self._show_crop_confirm()
                else:
                    self.crop_drag_phase = None
            if self.var("crop_mode").get() == "drag" and self.crop_drag_phase != "review":
                self.shape_start_image = None
                self.shape_start_canvas = None
        elif self.active_tool != "shape":
            self.shape_start_image = None
            self.shape_start_canvas = None
        if self.stroke_active and self.active_tool == "draw":
            mode = self.var("draw_mode").get()
            if mode in {"pencil", "eraser"}:
                self.canvas.delete("stroke_preview")
                self._commit_stroke(mode)
                self.invalidate_preview()
                self.refresh_canvas()
        self.stroke_active = False
        self.last_point = None
        self.stroke_points = []

    def _canvas_double_click(self, event):
        if self.active_tool == "text":
            point = self.canvas_point(event)
            if point is None:
                return
            hit = editor_text.find_object_at(self.session.text_objects, point[0], point[1])
            if hit is not None:
                self._select_text_object(hit)
                self._start_text_edit(hit)
            return
        if self.active_tool != "shape":
            return
        if self.var("shape_kind").get() != "curve":
            return
        self._shape_ignore_next_click = True
        self._commit_shape_curve()

    def _on_text_key_delete(self, event):
        if self.active_tool != "text" or self._text_editing_id:
            return
        if self._text_selected_id:
            self._delete_selected_text()

    def apply_crop(self):
        if self._commit_crop():
            self.exit_tool(force=True)

    def _commit_crop(self) -> bool:
        if self.crop_box is None or not self.session.is_cropable():
            return True
        width, height = self.session.image.size
        if self.crop_box == (0, 0, width, height):
            messagebox.showinfo(self.app._app_title(), self.t("editor_crop_no_change"))
            return False
        try:
            ffmpeg_path = self.app._editor_ffmpeg_location()
            self.session.crop(self.crop_box, ffmpeg_location=ffmpeg_path)
        except Exception as error:
            messagebox.showerror(self.app._app_title(), str(error))
            return False
        if self.session.image is not None:
            self.var("resize_w").set(str(self.session.image.width))
            self.var("resize_h").set(str(self.session.image.height))
        self.crop_box = None
        self.crop_handle = None
        self.crop_drag_phase = None
        self._crop_interacting = False
        self.invalidate_preview()
        return True

    def _commit_pending_tool(self) -> bool:
        tool = self.active_tool
        if tool == "text":
            self._finish_text_edit()
            return True
        if tool == "crop" and self.crop_box is not None:
            return self._commit_crop()
        if tool == "resize":
            return self.apply_resize()
        return True

    def _commit_rotate_degrees_entry(self, _event=None):
        try:
            degrees = float(self.var("rotate_degrees").get().strip())
        except ValueError:
            self.var("rotate_degrees").set("0")
            return "break"
        if abs(degrees) < 0.01:
            self.var("rotate_degrees").set("0")
            return "break"
        self.session.rotate(degrees)
        self._rotate_wheel_angle += degrees
        self.var("rotate_degrees").set("0")
        self._clear_rotate_drag()
        self.invalidate_preview()
        self.refresh_canvas()
        return "break"

    def rotate_by(self, degrees: float):
        self.session.rotate(degrees)
        self._rotate_wheel_angle += degrees
        self._clear_rotate_drag()
        self.invalidate_preview()
        self.refresh_canvas()

    def flip_horizontal(self):
        self.session.flip_horizontal()
        self._clear_rotate_drag()
        self.invalidate_preview()
        self.refresh_canvas()

    def flip_vertical(self):
        self.session.flip_vertical()
        self._clear_rotate_drag()
        self.invalidate_preview()
        self.refresh_canvas()

    def apply_resize(self) -> bool:
        dims = self._parse_resize_dimensions()
        if dims is None:
            messagebox.showwarning(self.app._app_title(), self.t("editor_invalid_size"))
            return False
        target_w, target_h = dims
        if self.session.image is None:
            return False
        mode = self.var("resize_mode").get()
        if mode == "scale":
            lock = self.var("resize_lock_aspect").get()
            self.session.resize_scale(target_w, target_h, lock_aspect=lock)
        else:
            if self._canvas_source_image is None:
                self._init_canvas_layout()
            self.session.apply_canvas_layout(
                target_w,
                target_h,
                self._canvas_placement_x,
                self._canvas_placement_y,
                self._canvas_content_scale,
                source_image=self._canvas_source_image,
                source_stroke=self._canvas_source_stroke,
            )
            self._clear_canvas_layout()
        if self.session.image is not None:
            width, height = self.session.image.size
            self.var("resize_w").set(str(width))
            self.var("resize_h").set(str(height))
            self._resize_source_size = (width, height)
        self.invalidate_preview()
        self.refresh_canvas()
        return True

    def pick_draw_color(self):
        color = colorchooser.askcolor(color=self.draw_color, title=self.t("editor_color"))
        if color and color[1]:
            self.draw_color = color[1]
            self._refresh_draw_color_swatch()

    def undo(self):
        if self.session.undo():
            self._finish_text_edit()
            self._text_selected_id = None
            self._reset_rotate_state()
            self.invalidate_preview()
            self.refresh_canvas()

    def redo(self):
        if self.session.redo():
            self._finish_text_edit()
            self._text_selected_id = None
            self._reset_rotate_state()
            self.invalidate_preview()
            self.refresh_canvas()

    def save_and_exit(self):
        if self.session.image is None:
            self.pick_file()
            return
        if not self._commit_pending_tool():
            return
        self.exit_tool(force=True)

    def save(self):
        if self.session.image is None:
            self.pick_file()
            return
        if not self._commit_pending_tool():
            return
        self._save_to_file()

    def _render_for_save(self) -> Image.Image | None:
        if self._canvas_layout_active():
            canvas_w, canvas_h = self._canvas_dims()
            base, stroke = editor_ops.compose_canvas_layout(
                self._canvas_source_image,
                self._canvas_source_stroke,
                canvas_w,
                canvas_h,
                self._canvas_placement_x,
                self._canvas_placement_y,
                self._canvas_content_scale,
            )
            if stroke is not None:
                return Image.alpha_composite(base.convert("RGBA"), stroke)
            return base
        return self.session.composite()

    def _save_to_file(self) -> bool:
        initial = self.session.source_path
        initial_name = initial.stem + "_edit.png" if initial else "edit.png"
        initial_dir = str(initial.parent) if initial else self.app.editor_folder_var.get()
        selected = filedialog.asksaveasfilename(
            title=self.t("editor_save"),
            defaultextension=".png",
            initialdir=initial_dir,
            initialfile=initial_name,
            filetypes=[("PNG", "*.png"), ("JPEG", "*.jpg"), ("WEBP", "*.webp")],
        )
        if not selected:
            return False
        try:
            rendered = self._render_for_save()
            if rendered is None:
                raise ValueError("No hay imagen para guardar.")
            output_path = Path(selected)
            output_path.parent.mkdir(parents=True, exist_ok=True)
            suffix = output_path.suffix.lower()
            if suffix in (".jpg", ".jpeg"):
                rgb = Image.new("RGB", rendered.size, (255, 255, 255))
                rgb.paste(rendered, mask=rendered.split()[3] if rendered.mode == "RGBA" else None)
                rgb.save(output_path, quality=95)
            else:
                rendered.save(output_path)
            saved = output_path
        except Exception as error:
            messagebox.showerror(self.app._app_title(), str(error))
            return False
        message = self.t("editor_saved", name=saved.name)
        self.app.detail_var.set(message)
        self.app._log(message)
        self.refresh_history()
        return True
