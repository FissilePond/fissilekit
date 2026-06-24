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
        self.shape_start_canvas = None
        self.shape_start_image = None
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
            ("eraser", "editor_tool_eraser"),
            ("shape", "editor_tool_shapes"),
            ("text", "editor_tool_text"),
        )
        for index, (key, label_key) in enumerate(tool_specs):
            button = self._icon_button(
                self.main_toolbar,
                key,
                lambda tool=key: self.enter_tool(tool),
                tooltip_key=label_key,
            )
            button.grid(row=0, column=index, padx=(0 if index == 0 else 4, 0))
            self.tool_buttons[key] = button

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

        export_row = tk.Frame(workspace, bg=EDITOR_THEME["bg"])
        export_row.grid(row=2, column=0, sticky="ew")
        export_row.grid_columnconfigure(0, weight=1)
        self.save_button = self._icon_button(
            export_row,
            "save",
            self.save,
            tooltip_key="editor_save",
            primary=True,
        )
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
        self._widgets["resize_w"] = tk.StringVar(value="")
        self._widgets["resize_h"] = tk.StringVar(value="")
        self._widgets["draw_mode"] = tk.StringVar(value="pencil")
        self._widgets["draw_opacity"] = tk.IntVar(value=100)
        self._widgets["draw_size"] = tk.IntVar(value=6)
        self._widgets["eraser_mode"] = tk.StringVar(value="manual")
        self._widgets["eraser_tolerance"] = tk.IntVar(value=32)
        self._widgets["eraser_size"] = tk.IntVar(value=18)

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
        button = tk.Button(
            parent,
            image=photo,
            command=command,
            bg=bg,
            activebackground=active_bg,
            relief="flat",
            bd=0,
            padx=8,
            pady=6,
            cursor="hand2",
        )
        button.image = photo
        if tooltip_key:
            self._attach_tooltip(button, self.t(tooltip_key))
        return button

    def _button(self, parent, text, command, width=10, primary=False):
        bg = EDITOR_THEME["accent"] if primary else EDITOR_THEME["btn"]
        fg = "#111827" if primary else EDITOR_THEME["btn_text"]
        return tk.Button(
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
        exit_btn = self._icon_button(
            self.sub_toolbar_actions,
            "exit",
            self.exit_tool,
            tooltip_key="editor_tool_exit",
        )
        exit_btn.pack(side="left", padx=(0, 4))
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
        redo_btn.pack(side="left")

    def enter_tool(self, tool_name: str):
        if not self.session.is_editable_image() and tool_name not in {"shape", "text"}:
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
        self._sub_actions()
        builders = {
            "crop": self._build_crop_bar,
            "rotate": self._build_rotate_bar,
            "resize": self._build_resize_bar,
            "draw": self._build_draw_bar,
            "eraser": self._build_eraser_bar,
            "shape": self._build_shape_bar,
            "text": self._build_text_bar,
        }
        builders[tool_name]()
        if tool_name == "crop" and self.session.image is not None:
            self.crop_drag_active = False
            self.shape_start_image = None
            self.shape_start_canvas = None
            self.crop_box = editor_ops.initial_crop_box(
                self.session.image.width,
                self.session.image.height,
            )
        self.refresh_canvas()

    def exit_tool(self):
        self.active_tool = None
        self.crop_box = None
        self.crop_handle = None
        self.sub_toolbar.grid_remove()
        self.main_toolbar.grid(row=0, column=0, sticky="ew")
        self.refresh_canvas()

    def _build_crop_bar(self):
        row = tk.Frame(self.sub_toolbar_content, bg=EDITOR_THEME["bg"])
        row.pack(fill="x")
        self._label(row, self.t("editor_crop_mode")).pack(side="left", padx=(0, 4))
        for mode, label in (("handles", "editor_crop_handles"), ("drag", "editor_crop_drag")):
            self._button(row, self.t(label), lambda m=mode: self._set_crop_mode(m), width=8).pack(side="left", padx=2)
        for key, label in (
            ("free", "editor_aspect_free"),
            ("1:1", "editor_aspect_1_1"),
            ("9:16", "editor_aspect_9_16"),
            ("16:9", "editor_aspect_16_9"),
        ):
            btn = self._button(row, self.t(label), lambda aspect=key: self._set_crop_aspect(aspect), width=6)
            btn.pack(side="left", padx=2)
        self._button(row, self.t("editor_apply"), self.apply_crop, width=8, primary=True).pack(side="left", padx=(8, 0))

    def _set_crop_mode(self, mode: str):
        self.var("crop_mode").set(mode)
        self.crop_handle = None
        self.crop_drag_origin = None
        self.crop_drag_start = None
        self.crop_drag_active = False
        self.shape_start_image = None
        self.shape_start_canvas = None
        self.refresh_canvas()

    def _set_crop_aspect(self, aspect_key: str):
        self.var("crop_aspect").set(aspect_key)
        if self.crop_box is None or self.session.image is None:
            return
        aspect = editor_ops.CROP_ASPECTS.get(aspect_key)
        img_w, img_h = self.session.image.size
        self.crop_box = editor_ops.fit_crop_box_to_aspect(self.crop_box, aspect, img_w, img_h)
        self.refresh_canvas(overlay_only=True)

    def _build_rotate_bar(self):
        row = tk.Frame(self.sub_toolbar_content, bg=EDITOR_THEME["bg"])
        row.pack(fill="x")
        self._label(row, self.t("editor_rotate_degrees")).pack(side="left", padx=(0, 4))
        tk.Entry(row, textvariable=self.var("rotate_degrees"), width=6, bg=EDITOR_THEME["surface"], fg=EDITOR_THEME["text"], insertbackground=EDITOR_THEME["text"]).pack(side="left")
        self._button(row, "-90", lambda: self.rotate_by(-90), width=4).pack(side="left", padx=2)
        self._button(row, "+90", lambda: self.rotate_by(90), width=4).pack(side="left", padx=2)
        self._button(row, self.t("editor_rotate_go"), self.apply_rotate, width=8, primary=True).pack(side="left", padx=(8, 0))

    def _build_resize_bar(self):
        row = tk.Frame(self.sub_toolbar_content, bg=EDITOR_THEME["bg"])
        row.pack(fill="x")
        for preset, label in (
            ("baja", "quality_baja"),
            ("media", "quality_media"),
            ("alta", "quality_alta"),
            ("original", "editor_resize_original"),
            ("custom", "editor_resize_custom"),
        ):
            self._button(row, self.t(label), lambda p=preset: self.var("resize_preset").set(p), width=8).pack(side="left", padx=2)
        self._label(row, "W").pack(side="left", padx=(8, 2))
        tk.Entry(row, textvariable=self.var("resize_w"), width=5, bg=EDITOR_THEME["surface"], fg=EDITOR_THEME["text"]).pack(side="left")
        self._label(row, "H").pack(side="left", padx=(4, 2))
        tk.Entry(row, textvariable=self.var("resize_h"), width=5, bg=EDITOR_THEME["surface"], fg=EDITOR_THEME["text"]).pack(side="left")
        self._button(row, self.t("editor_apply"), self.apply_resize, width=8, primary=True).pack(side="left", padx=(8, 0))

    def _build_draw_bar(self):
        row = tk.Frame(self.sub_toolbar_content, bg=EDITOR_THEME["bg"])
        row.pack(fill="x")
        self._label(row, self.t("editor_draw_mode")).pack(side="left", padx=(0, 4))
        for mode, label in (("pencil", "editor_draw_pencil"), ("bucket", "editor_draw_bucket")):
            self._icon_button(
                row,
                mode,
                lambda m=mode: self.var("draw_mode").set(m),
                size=20,
                tooltip_key=label,
            ).pack(side="left", padx=2)
        self._label(row, self.t("editor_tolerance")).pack(side="left", padx=(6, 2))
        tk.Scale(
            row,
            from_=0,
            to=80,
            orient="horizontal",
            variable=self.var("draw_tolerance"),
            length=70,
            bg=EDITOR_THEME["bg"],
            fg=EDITOR_THEME["text"],
            highlightthickness=0,
            troughcolor=EDITOR_THEME["surface"],
        ).pack(side="left", padx=(0, 6))
        self._label(row, self.t("editor_opacity")).pack(side="left")
        tk.Scale(row, from_=5, to=100, orient="horizontal", variable=self.var("draw_opacity"), length=80, bg=EDITOR_THEME["bg"], fg=EDITOR_THEME["text"], highlightthickness=0, troughcolor=EDITOR_THEME["surface"]).pack(side="left", padx=4)
        self._label(row, self.t("editor_size")).pack(side="left")
        tk.Scale(row, from_=1, to=40, orient="horizontal", variable=self.var("draw_size"), length=80, bg=EDITOR_THEME["bg"], fg=EDITOR_THEME["text"], highlightthickness=0, troughcolor=EDITOR_THEME["surface"]).pack(side="left", padx=4)
        self._button(row, self.t("editor_color"), self.pick_draw_color, width=8).pack(side="left", padx=4)

    def _build_eraser_bar(self):
        row = tk.Frame(self.sub_toolbar_content, bg=EDITOR_THEME["bg"])
        row.pack(fill="x")
        self._label(row, self.t("editor_eraser_manual")).pack(side="left", padx=(0, 8))
        self._label(row, self.t("editor_size")).pack(side="left", padx=(4, 2))
        tk.Scale(
            row,
            from_=4,
            to=60,
            orient="horizontal",
            variable=self.var("eraser_size"),
            length=160,
            bg=EDITOR_THEME["bg"],
            fg=EDITOR_THEME["text"],
            highlightthickness=0,
            troughcolor=EDITOR_THEME["surface"],
        ).pack(side="left")

    def _build_shape_bar(self):
        row = tk.Frame(self.sub_toolbar_content, bg=EDITOR_THEME["bg"])
        row.pack(fill="x")
        self._label(row, self.t("editor_shape_hint")).pack(side="left")

    def _build_text_bar(self):
        row = tk.Frame(self.sub_toolbar_content, bg=EDITOR_THEME["bg"])
        row.pack(fill="x")
        self._label(row, self.t("editor_text_hint")).pack(side="left")

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
        self.exit_tool()
        self.invalidate_preview()
        self.refresh_canvas()
        message = self.t("editor_loaded", name=path.name)
        self.app.detail_var.set(message)
        self.app._log(message)

    def metrics(self):
        width = max(self.canvas.winfo_width(), 1)
        height = max(self.canvas.winfo_height(), 1)
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

    def refresh_canvas(self, overlay_only: bool = False):
        canvas = self.canvas
        width, height, scale, offset_x, offset_y, img_w, img_h = self.metrics()
        if overlay_only and self.canvas_photo is not None:
            canvas.delete("overlay")
            if self.active_tool == "crop" and self.crop_box is not None:
                self._draw_crop_overlay(scale, offset_x, offset_y)
            return

        if not self._preview_dirty and self.canvas_photo is not None:
            canvas.delete("overlay")
            canvas.delete("stroke_preview")
            if self.active_tool == "crop" and self.crop_box is not None:
                self._draw_crop_overlay(scale, offset_x, offset_y)
            return

        canvas.delete("all")
        image = self.session.composite()
        if image is None:
            canvas.create_text(
                width / 2,
                height / 2,
                text=self.t("editor_click_add"),
                fill=EDITOR_THEME["muted"],
                font=("Segoe UI", 11),
            )
            self.canvas_photo = None
            self._preview_dirty = False
            return

        fast = self.stroke_active or self.crop_handle or self.crop_drag_active
        resample = Image.Resampling.BILINEAR if fast else Image.Resampling.LANCZOS
        preview = image.copy()
        preview.thumbnail(
            (max(1, int(img_w * scale)), max(1, int(img_h * scale))),
            resample,
        )
        self.canvas_photo = ImageTk.PhotoImage(preview)
        canvas.create_image(offset_x, offset_y, anchor="nw", image=self.canvas_photo, tags="base")
        self._preview_dirty = False
        if self.active_tool == "crop" and self.crop_box is not None:
            self._draw_crop_overlay(scale, offset_x, offset_y)

    def _draw_stroke_preview(self, points: list[tuple[float, float]], tool: str):
        if not points:
            return
        width, height, scale, offset_x, offset_y, img_w, img_h = self.metrics()
        if tool == "draw":
            color = self.draw_color
            line_width = max(1, int(self.var("draw_size").get() * scale))
        else:
            color = "#ffffff"
            line_width = max(1, int(self.var("eraser_size").get() * scale))
        coords: list[float] = []
        for px, py in points:
            cx, cy = editor.image_to_canvas(px, py, width, height, img_w, img_h)
            coords.extend((cx, cy))
        if len(coords) >= 4:
            self.canvas.create_line(
                *coords,
                fill=color,
                width=line_width,
                capstyle="round",
                joinstyle="round",
                tags="stroke_preview",
            )
        elif len(coords) == 2:
            x, y = coords
            self.canvas.create_oval(
                x - line_width,
                y - line_width,
                x + line_width,
                y + line_width,
                fill=color,
                outline="",
                tags="stroke_preview",
            )

    def _commit_stroke(self, tool: str):
        if not self.stroke_points:
            return
        if tool == "draw":
            self.session.apply_draw(
                self.stroke_points,
                self.draw_color,
                self.var("draw_size").get(),
                self.var("draw_opacity").get(),
                "pencil",
            )
        elif tool == "eraser":
            self.session.apply_eraser(
                "manual",
                self.stroke_points[-1][0],
                self.stroke_points[-1][1],
                self.stroke_points,
                0,
                self.var("eraser_size").get(),
            )

    def _draw_crop_overlay(self, scale, offset_x, offset_y):
        left, top, right, bottom = self.crop_box
        width, height, _, _, _, img_w, img_h = self.metrics()
        x0 = offset_x + left * scale
        y0 = offset_y + top * scale
        x1 = offset_x + right * scale
        y1 = offset_y + bottom * scale
        shade = "#0d0d0d"
        if top > 0:
            self.canvas.create_rectangle(0, 0, width, y0, fill=shade, outline="", tags="overlay")
        if bottom * scale < img_h * scale:
            self.canvas.create_rectangle(0, y1, width, height, fill=shade, outline="", tags="overlay")
        if left > 0:
            self.canvas.create_rectangle(0, y0, x0, y1, fill=shade, outline="", tags="overlay")
        if right * scale < img_w * scale:
            self.canvas.create_rectangle(x1, y0, width, y1, fill=shade, outline="", tags="overlay")
        self.canvas.create_rectangle(x0, y0, x1, y1, outline=EDITOR_THEME["accent"], width=2, tags="overlay")
        for cx, cy in ((x0, y0), (x1, y0), (x0, y1), (x1, y1)):
            self.canvas.create_rectangle(cx - 6, cy - 6, cx + 6, cy + 6, fill=EDITOR_THEME["accent"], outline="", tags="overlay")

    def _safe_canvas(self, handler, event):
        try:
            handler(event)
        except Exception as error:
            messagebox.showerror(self.app._app_title(), str(error))

    def _canvas_press(self, event):
        if self.session.image is None:
            self.pick_file()
            return
        point = self.canvas_point(event)
        if point is None:
            return
        tool = self.active_tool
        if tool == "crop":
            if self.crop_box is None:
                return
            mode = self.var("crop_mode").get()
            if mode == "handles":
                width, height, scale, offset_x, offset_y, img_w, img_h = self.metrics()
                handle = editor_ops.hit_crop_handle(
                    event.x,
                    event.y,
                    self.crop_box,
                    scale,
                    offset_x,
                    offset_y,
                    handle_size=14.0,
                )
                if handle:
                    self.crop_handle = handle
                    self.crop_drag_origin = self.crop_box
                    self.crop_drag_start = (event.x, event.y)
                return
            if mode == "drag":
                self.crop_drag_active = True
                self.shape_start_canvas = (event.x, event.y)
                self.shape_start_image = point
            return
        if tool == "text":
            from tkinter import simpledialog

            text = simpledialog.askstring(self.t("editor_text_title"), self.t("editor_text_prompt"), parent=self.app)
            if text:
                self.session.snapshot()
                self.session.add_text(point, text)
                self.invalidate_preview()
                self.refresh_canvas()
            return
        if tool == "draw":
            mode = self.var("draw_mode").get()
            if mode == "bucket":
                self.session.bucket_fill_at(
                    point[0],
                    point[1],
                    self.draw_color,
                    self.var("draw_opacity").get(),
                    self.var("draw_tolerance").get(),
                )
                self.invalidate_preview()
                self.refresh_canvas()
                return
            self.session.snapshot()
            self.stroke_active = True
            self.stroke_points = [point]
            self.last_point = point
            return
        if tool == "eraser":
            self.session.snapshot()
            self.stroke_active = True
            self.stroke_points = [point]
            self.last_point = point
            return
        if tool == "shape":
            self.shape_start_canvas = (event.x, event.y)
            self.shape_start_image = point

    def _canvas_drag(self, event):
        tool = self.active_tool
        if tool == "crop" and self.crop_box is not None:
            width, height, scale, offset_x, offset_y, img_w, img_h = self.metrics()
            aspect_key = self.var("crop_aspect").get()
            aspect = editor_ops.CROP_ASPECTS.get(aspect_key)
            mode = self.var("crop_mode").get()
            if mode == "handles" and self.crop_handle and self.crop_drag_origin and self.crop_drag_start:
                dx = (event.x - self.crop_drag_start[0]) / scale
                dy = (event.y - self.crop_drag_start[1]) / scale
                left, top, right, bottom = self.crop_drag_origin
                if self.crop_handle == "move":
                    self.crop_box = editor_ops.move_crop_box(self.crop_drag_origin, dx, dy, img_w, img_h)
                else:
                    box = list(self.crop_drag_origin)
                    if "l" in self.crop_handle:
                        box[0] = left + dx
                    if "r" in self.crop_handle:
                        box[2] = right + dx
                    if "t" in self.crop_handle:
                        box[1] = top + dy
                    if "b" in self.crop_handle:
                        box[3] = bottom + dy
                    adjusted = editor_ops.apply_aspect_ratio(tuple(box), aspect, self.crop_handle, img_w, img_h)
                    self.crop_box = editor_ops.clamp_crop_box(adjusted, img_w, img_h)
                self.refresh_canvas(overlay_only=True)
                return
            if mode == "drag" and self.crop_drag_active and self.shape_start_image is not None:
                end = self.canvas_point(event)
                if end is not None:
                    x0, y0 = self.shape_start_image
                    x1, y1 = end
                    box = editor_ops.clamp_crop_box((x0, y0, x1, y1), img_w, img_h)
                    aspect = editor_ops.CROP_ASPECTS.get(self.var("crop_aspect").get())
                    self.crop_box = editor_ops.fit_crop_box_to_aspect(box, aspect, img_w, img_h)
                    self.refresh_canvas(overlay_only=True)
                return
        if tool == "shape" and self.shape_start_canvas is not None:
            self.canvas.delete("overlay")
            x0, y0 = self.shape_start_canvas
            self.canvas.create_rectangle(x0, y0, event.x, event.y, outline="#e74c3c", width=2, tags="overlay")
            return
        if not self.stroke_active or self.last_point is None:
            return
        point = self.canvas_point(event)
        if point is None:
            return
        if tool == "draw" or tool == "eraser":
            segment = editor_ops.interpolate_segment(self.last_point, point, step=0.5)
            self.stroke_points.extend(segment)
            self._draw_stroke_preview(segment, tool)
            self.last_point = point
            return

    def _canvas_release(self, event):
        if self.active_tool == "shape" and self.shape_start_image is not None:
            end = self.canvas_point(event)
            if end is not None:
                box = editor_ops.normalize_shape_box(self.shape_start_image, end)
                if box is not None:
                    self.session.snapshot()
                    self.session.draw_shape("rectangle", self.shape_start_image, end, (231, 76, 60, 255))
            self.shape_start_image = None
            self.shape_start_canvas = None
            self.canvas.delete("overlay")
            self.invalidate_preview()
            self.refresh_canvas()
        self.crop_handle = None
        self.crop_drag_origin = None
        self.crop_drag_start = None
        if self.active_tool == "crop":
            self.crop_drag_active = False
            if self.var("crop_mode").get() == "drag":
                self.shape_start_image = None
                self.shape_start_canvas = None
        elif self.active_tool != "shape":
            self.shape_start_image = None
            self.shape_start_canvas = None
        if self.stroke_active and self.active_tool in {"draw", "eraser"}:
            self.canvas.delete("stroke_preview")
            self._commit_stroke(self.active_tool)
            self.invalidate_preview()
            self.refresh_canvas()
        self.stroke_active = False
        self.last_point = None
        self.stroke_points = []

    def apply_crop(self):
        if self.crop_box is None or not self.session.is_editable_image():
            return
        width, height = self.session.image.size
        if self.crop_box == (0, 0, width, height):
            messagebox.showinfo(self.app._app_title(), self.t("editor_crop_no_change"))
            return
        self.session.crop(self.crop_box)
        img_w, img_h = self.session.image.size
        self.crop_box = editor_ops.initial_crop_box(img_w, img_h)
        self.invalidate_preview()
        self.refresh_canvas()

    def apply_rotate(self):
        try:
            degrees = float(self.var("rotate_degrees").get().strip())
        except ValueError:
            messagebox.showwarning(self.app._app_title(), self.t("editor_invalid_size"))
            return
        if abs(degrees) < 0.01:
            return
        self.session.rotate(degrees)
        self.var("rotate_degrees").set("0")
        self.invalidate_preview()
        self.refresh_canvas()

    def rotate_by(self, degrees: float):
        self.session.rotate(degrees)
        self.invalidate_preview()
        self.refresh_canvas()

    def apply_resize(self):
        preset = self.var("resize_preset").get()
        try:
            if preset == "custom":
                custom_w = int(self.var("resize_w").get().strip())
                custom_h = int(self.var("resize_h").get().strip())
                self.session.resize_preset("custom", custom_w, custom_h)
            elif preset in {"baja", "media", "alta", "original"}:
                self.session.resize_preset(preset)
            else:
                self.session.resize_preset("media")
        except ValueError as error:
            messagebox.showwarning(self.app._app_title(), str(error))
            return
        if self.session.image is not None:
            self.var("resize_w").set(str(self.session.image.width))
            self.var("resize_h").set(str(self.session.image.height))
        self.invalidate_preview()
        self.refresh_canvas()

    def pick_draw_color(self):
        color = colorchooser.askcolor(color=self.draw_color, title=self.t("editor_color"))
        if color and color[1]:
            self.draw_color = color[1]

    def undo(self):
        if self.session.undo():
            self.invalidate_preview()
            self.refresh_canvas()

    def redo(self):
        if self.session.redo():
            self.invalidate_preview()
            self.refresh_canvas()

    def save(self):
        if self.session.image is None:
            self.pick_file()
            return
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
            return
        try:
            saved = self.session.save_copy(Path(selected))
        except Exception as error:
            messagebox.showerror(self.app._app_title(), str(error))
            return
        message = self.t("editor_saved", name=saved.name)
        self.app.detail_var.set(message)
        self.app._log(message)
        self.refresh_history()
