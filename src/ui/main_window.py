import tkinter as tk
from tkinter import filedialog, ttk, colorchooser, messagebox
from tkinterdnd2 import DND_FILES
from PIL import Image, ImageTk, ImageDraw, ImageFont
import os
import json

from core.image_processor import ImageProcessor
from core.config_manager import ConfigManager
from core.watermark import Watermark

class MainWindow:
    """The main window of the application."""

    def __init__(self, root):
        self.root = root
        self.root.title("Photo Watermark 2.0")
        self.root.geometry("1700x900")
        self.root.configure(bg='#f0f0f0')
        
        # Configure modern styling
        self.setup_styles()

        self.image_processor = ImageProcessor()
        self.config_manager = ConfigManager()
        # Ensure default template exists and force selection to Default on startup
        try:
            self.config_manager.ensure_default_template()
            self.config_manager.set_selected_template('Default')
        except Exception as e:
            print(f"Error initializing templates: {e}")
        self.filepaths = []
        self.filepath_set = set()
        self.tk_thumbnails = []
        self.current_image_path = None
        self.original_image = None
        self.preview_job = None
        self.watermark_position_mode = "bottom-right"
        self.watermark_offset = {"x": 0, "y": 0}
        self.is_dragging = False
        self.drag_start_pos = {"x": 0, "y": 0}
        self.display_to_original_ratio = 1.0
        self.image_states = {}

        # Export settings defaults (used by export actions)
        self.export_prefix = tk.StringVar(value="wm_")
        self.export_format = tk.StringVar(value="JPEG")
        self.export_quality = tk.IntVar(value=95)

        self.create_widgets()
        # Apply the selected (Default) template at startup
        try:
            self.apply_template_by_name(self.config_manager.get_selected_template_name())
        except Exception as e:
            print(f"Error applying default template: {e}")

        self.root.drop_target_register(DND_FILES)
        self.root.dnd_bind('<<Drop>>', self.on_drop)

    def setup_styles(self):
        """Configure modern styling for the application."""
        # Configure ttk styles
        style = ttk.Style()
        
        # Configure modern button style
        style.configure('Modern.TButton',
                       padding=(10, 8),
                       font=('Segoe UI', 9, 'bold'),
                       relief='flat',
                       borderwidth=0)
        
        style.map('Modern.TButton',
                 background=[('active', '#4CAF50'),
                           ('pressed', '#45a049'),
                           ('!active', '#5cb85c')],
                 foreground=[('active', 'white'),
                           ('pressed', 'white'),
                           ('!active', 'white')])
        
        # Configure primary button style
        style.configure('Primary.TButton',
                       padding=(12, 10),
                       font=('Segoe UI', 10, 'bold'),
                       relief='flat',
                       borderwidth=0)
        
        style.map('Primary.TButton',
                 background=[('active', '#2196F3'),
                           ('pressed', '#1976D2'),
                           ('!active', '#2196F3')],
                 foreground=[('active', 'white'),
                           ('pressed', 'white'),
                           ('!active', 'white')])
        
        # Configure secondary button style
        style.configure('Secondary.TButton',
                       padding=(10, 8),
                       font=('Segoe UI', 9),
                       relief='flat',
                       borderwidth=1)
        
        style.map('Secondary.TButton',
                 background=[('active', '#f8f9fa'),
                           ('pressed', '#e9ecef'),
                           ('!active', 'white')],
                 foreground=[('active', '#212529'),
                           ('pressed', '#212529'),
                           ('!active', '#212529')],
                 bordercolor=[('active', '#dee2e6'),
                            ('pressed', '#adb5bd'),
                            ('!active', '#dee2e6')])
        
        # Selected button style for position grid
        style.configure('Selected.TButton',
                       padding=(10, 8),
                       font=('Segoe UI', 9, 'bold'),
                       relief='flat',
                       borderwidth=1)
        
        style.map('Selected.TButton',
                 background=[('active', '#60a5fa'),
                           ('pressed', '#3b82f6'),
                           ('!active', '#93c5fd')],
                 foreground=[('active', '#1e3a8a'),
                           ('pressed', '#1e3a8a'),
                           ('!active', '#1e3a8a')],
                 bordercolor=[('active', '#60a5fa'),
                            ('pressed', '#3b82f6'),
                            ('!active', '#60a5fa')])
        
        # Configure modern frame style
        style.configure('Card.TFrame',
                       background='white',
                       relief='solid',
                       borderwidth=1)
        
        # Configure modern label frame
        style.configure('Modern.TLabelframe',
                       background='white',
                       relief='solid',
                       borderwidth=1)
        
        style.configure('Modern.TLabelframe.Label',
                       background='white',
                       foreground='#212529',
                       font=('Segoe UI', 10, 'bold'))

    def create_widgets(self):
        """Creates the widgets for the main window."""
        main_frame = tk.Frame(self.root, bg='#f0f0f0')
        main_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        # Create a toolbar at the top
        toolbar = ttk.Frame(main_frame, style='Card.TFrame')
        toolbar.pack(side=tk.TOP, fill=tk.X, pady=(0, 10))

        self.import_button = ttk.Button(toolbar, text="📷 Select Images", command=self.import_images, style='Secondary.TButton')
        self.import_button.pack(side=tk.LEFT, padx=(10, 5), pady=10)

        self.import_folder_button = ttk.Button(toolbar, text="📂 Select Folder", command=self.import_folder, style='Secondary.TButton')
        self.import_folder_button.pack(side=tk.LEFT, padx=5, pady=10)

        self.export_button = ttk.Button(toolbar, text="📤 Export All", command=self.export_images, style='Secondary.TButton')
        self.export_button.pack(side=tk.LEFT, padx=5, pady=10)

        self.export_single_button = ttk.Button(toolbar, text="🖼️ Export Single", command=self.export_single_image, style='Secondary.TButton')
        self.export_single_button.pack(side=tk.LEFT, padx=5, pady=10)

        # Left panel for thumbnails (balanced width; filenames will wrap)
        left_panel = ttk.Frame(main_frame, style='Card.TFrame', width=300)
        left_panel.pack(side=tk.LEFT, fill=tk.Y, padx=(0, 10))
        left_panel.pack_propagate(False)

        import_frame = ttk.Frame(left_panel)
        import_frame.pack(fill=tk.X, padx=15, pady=15)

        # Thumbnails scrollable area
        thumbnails_frame = ttk.Frame(left_panel)
        thumbnails_frame.pack(fill=tk.BOTH, expand=True, padx=15, pady=(0, 15))
        
        canvas = tk.Canvas(thumbnails_frame, bg='white', highlightthickness=0)
        scrollbar = ttk.Scrollbar(thumbnails_frame, orient="vertical", command=canvas.yview)
        self.scrollable_frame = ttk.Frame(canvas)
        self.scrollable_frame.bind("<Configure>", lambda e: canvas.configure(scrollregion=canvas.bbox("all")))
        canvas.create_window((0, 0), window=self.scrollable_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)
        canvas.bind_all("<MouseWheel>", lambda e: canvas.yview_scroll(int(-1*(e.delta/120)), "units"))
        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")

        # Center panel for the main image view
        self.center_panel = ttk.Frame(main_frame, style='Card.TFrame')
        self.center_panel.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(0, 10))

        # Image display area
        # Fixed-size preview area to prevent layout from growing with image size
        self.preview_width = 850
        self.preview_height = 600
        self.image_display_frame = ttk.Frame(self.center_panel, width=self.preview_width, height=self.preview_height)
        # Center the preview frame within the center panel (both horizontally and vertically)
        self.image_display_frame.place(relx=0.5, rely=0.5, anchor='center')
        self.image_display_frame.pack_propagate(False)

        self.image_label = tk.Label(self.image_display_frame, 
                                   text="🎨 Workspace\n\nDrag & drop images here or use the import buttons\n\nSelect an image from the list to start editing", 
                                   font=('Segoe UI', 12),
                                   fg='#212529',
                                   bg='white',
                                   justify='center')
        # Center the placeholder/image within the fixed preview area
        self.image_label.place(relx=0.5, rely=0.5, anchor='center')
        self.image_label.bind("<Button-1>", self.on_drag_start)
        self.image_label.bind("<B1-Motion>", self.on_drag_motion)
        self.image_label.bind("<ButtonRelease-1>", self.on_drag_end)

        # Right panel for controls
        self.control_panel = ttk.Frame(main_frame, style='Card.TFrame', width=370)
        self.control_panel.pack(side=tk.RIGHT, fill=tk.Y)
        self.control_panel.pack_propagate(False)

        self.create_template_controls()
        self.create_watermark_controls()
        self.create_export_controls()

    def create_template_controls(self):
        """Creates the widgets for template selection and management."""
        template_frame = ttk.LabelFrame(self.control_panel, text="💾 Watermark Templates", style='Modern.TLabelframe')
        template_frame.pack(fill=tk.X, padx=15, pady=(15, 10))

        inner = ttk.Frame(template_frame)
        inner.pack(fill=tk.X, padx=10, pady=10)

        ttk.Label(inner, text="Template:", font=('Segoe UI', 9, 'bold')).pack(anchor="w")
        self.template_names = self.config_manager.list_templates()
        self.selected_template_var = tk.StringVar(value=self.config_manager.get_selected_template_name())
        self.template_combo = ttk.Combobox(inner, textvariable=self.selected_template_var, values=self.template_names, state="readonly")
        self.template_combo.pack(fill=tk.X, pady=(5, 10))
        self.template_combo.bind("<<ComboboxSelected>>", self.on_template_selected)

        btn_row = ttk.Frame(inner)
        btn_row.pack(fill=tk.X)
        save_btn = ttk.Button(btn_row, text="💾 Save Template", command=self.save_template, style='Secondary.TButton')
        save_btn.pack(side=tk.LEFT, expand=True, fill=tk.X, padx=(0, 5))
        manage_btn = ttk.Button(btn_row, text="⚙️ Manage Templates", command=self.manage_templates, style='Secondary.TButton')
        manage_btn.pack(side=tk.RIGHT, expand=True, fill=tk.X, padx=(5, 0))

    def create_watermark_controls(self):
        """Creates the widgets for the watermark control panel."""
        watermark_frame = ttk.LabelFrame(self.control_panel, text="🎨 Watermark Settings", style='Modern.TLabelframe')
        watermark_frame.pack(fill=tk.X, padx=15, pady=10)

        # Text input
        text_frame = ttk.Frame(watermark_frame)
        text_frame.pack(fill=tk.X, padx=10, pady=(10, 5))
        
        ttk.Label(text_frame, text="📝 Watermark Text:", font=('Segoe UI', 9, 'bold')).pack(anchor="w")
        self.watermark_text = tk.StringVar(value="Your Watermark")
        self.watermark_text.trace_add("write", self.schedule_preview)
        text_entry = ttk.Entry(text_frame, textvariable=self.watermark_text, font=('Segoe UI', 10))
        text_entry.pack(fill=tk.X, pady=(5, 0))

        # Font size
        size_frame = ttk.Frame(watermark_frame)
        size_frame.pack(fill=tk.X, padx=10, pady=5)
        
        ttk.Label(size_frame, text="📏 Font Size:", font=('Segoe UI', 9, 'bold')).pack(anchor="w")
        self.font_size = tk.IntVar(value=40)
        self.font_size.trace_add("write", self.schedule_preview)
        size_spinbox = ttk.Spinbox(size_frame, from_=1, to=500, textvariable=self.font_size, font=('Segoe UI', 10))
        size_spinbox.pack(fill=tk.X, pady=(5, 0))

        # Opacity (percent 0-100)
        opacity_frame = ttk.Frame(watermark_frame)
        opacity_frame.pack(fill=tk.X, padx=10, pady=5)
        
        # Header with label on the left and live value on the right
        header = ttk.Frame(opacity_frame)
        header.pack(fill=tk.X)
        ttk.Label(header, text="👁️ Opacity (0% - 100%):", font=('Segoe UI', 9, 'bold')).pack(side=tk.LEFT)
        
        self.opacity = tk.IntVar(value=50)
        self.opacity_value_var = tk.StringVar(value=f"{self.opacity.get()}%")
        ttk.Label(header, textvariable=self.opacity_value_var, font=('Segoe UI', 9)).pack(side=tk.RIGHT)
        
        opacity_scale = ttk.Scale(opacity_frame, from_=0, to=100, orient=tk.HORIZONTAL, variable=self.opacity, command=self.schedule_preview)
        opacity_scale.pack(fill=tk.X, pady=(5, 0))
        
        # Live update the right-side value when the scale changes or when opacity is set programmatically
        try:
            self.opacity.trace_add('write', lambda *args: self.opacity_value_var.set(f"{self.opacity.get()}%"))
        except Exception:
            # Fallback for older Tk versions
            self.opacity.trace('w', lambda *args: self.opacity_value_var.set(f"{self.opacity.get()}%"))
        # pack is already done above, avoid duplicate pack
        # opacity_scale.pack(fill=tk.X, pady=(5, 0))

        # Color button
        color_frame = ttk.Frame(watermark_frame)
        color_frame.pack(fill=tk.X, padx=10, pady=10)
        
        self.color_button = ttk.Button(color_frame, text="🎨 Choose Color", command=self.choose_color_and_preview, style='Secondary.TButton')
        self.color_button.pack(fill=tk.X)
        self.watermark_color = (255, 255, 255)

        # Position controls
        position_frame = ttk.Frame(watermark_frame)
        position_frame.pack(fill=tk.X, padx=10, pady=10)
        
        ttk.Label(position_frame, text="📍 Position:", font=('Segoe UI', 9, 'bold')).pack(anchor="w", pady=(0, 5))
        
        pos_grid_frame = ttk.Frame(position_frame)
        pos_grid_frame.pack(fill=tk.X)
        
        positions = ["top-left", "top-center", "top-right",
                     "mid-left", "mid-center", "mid-right",
                     "bottom-left", "bottom-center", "bottom-right"]
        
        self.position_buttons = {}
        for i, pos in enumerate(positions):
            btn = ttk.Button(pos_grid_frame, text=pos.replace("-", "\n"), 
                          command=lambda p=pos: self.set_watermark_position(p), 
                          style='Secondary.TButton',
                          width=8,
                          takefocus=False)
            btn.grid(row=i//3, column=i%3, sticky="nsew", padx=2, pady=2)
            pos_grid_frame.grid_columnconfigure(i%3, weight=1)
            self.position_buttons[pos] = btn
        
        pos_grid_frame.grid_rowconfigure(0, weight=1)
        pos_grid_frame.grid_rowconfigure(1, weight=1)
        pos_grid_frame.grid_rowconfigure(2, weight=1)
        
        # Initialize grid selection visual state
        self.update_position_grid_selection(getattr(self, 'watermark_position_mode', 'bottom-right'))
        # Ensure no focus ring remains on any position button initially
        self.clear_position_grid_focus()

    def create_export_controls(self):
        """Creates export settings including naming rules and format/quality."""
        export_frame = ttk.LabelFrame(self.control_panel, text="📤 Export Settings", style='Modern.TLabelframe')
        export_frame.pack(fill=tk.X, padx=15, pady=(0, 15))

        inner = ttk.Frame(export_frame)
        inner.pack(fill=tk.X, padx=10, pady=10)

        # Naming rule
        ttk.Label(inner, text="🧩 Filename rule:", font=('Segoe UI', 9, 'bold')).pack(anchor="w")
        self.naming_rule = tk.StringVar(value="original")  # original | prefix | suffix

        rule_row = ttk.Frame(inner)
        rule_row.pack(fill=tk.X, pady=(5, 2))

        ttk.Radiobutton(rule_row, text="Keep original", value="original", variable=self.naming_rule).pack(side=tk.LEFT)
        ttk.Radiobutton(rule_row, text="Add prefix", value="prefix", variable=self.naming_rule).pack(side=tk.LEFT, padx=(10,0))

        rule_row2 = ttk.Frame(inner)
        rule_row2.pack(fill=tk.X, pady=(0, 8))
        ttk.Radiobutton(rule_row2, text="Add suffix", value="suffix", variable=self.naming_rule).pack(side=tk.LEFT)

        # Prefix / Suffix inputs
        ps_row = ttk.Frame(inner)
        ps_row.pack(fill=tk.X)
        ttk.Label(ps_row, text="Prefix:").pack(side=tk.LEFT)
        self.export_prefix = tk.StringVar(value=self.export_prefix.get() if isinstance(self.export_prefix, tk.Variable) else "wm_")
        ttk.Entry(ps_row, textvariable=self.export_prefix, width=12).pack(side=tk.LEFT, padx=(5, 15))
        ttk.Label(ps_row, text="Suffix:").pack(side=tk.LEFT)
        self.export_suffix = tk.StringVar(value="_watermarked")
        ttk.Entry(ps_row, textvariable=self.export_suffix, width=12).pack(side=tk.LEFT, padx=(5, 0))

        # Format & quality
        fmt_row = ttk.Frame(inner)
        fmt_row.pack(fill=tk.X, pady=(10,0))
        ttk.Label(fmt_row, text="Format:").pack(side=tk.LEFT)
        self.export_format = tk.StringVar(value=self.export_format.get() if isinstance(self.export_format, tk.Variable) else "JPEG")
        fmt_box = ttk.Combobox(fmt_row, textvariable=self.export_format, values=["JPEG", "PNG"], state="readonly", width=6)
        fmt_box.pack(side=tk.LEFT, padx=(5, 15))

        ttk.Label(fmt_row, text="JPEG Quality:").pack(side=tk.LEFT)
        self.export_quality = tk.IntVar(value=self.export_quality.get() if isinstance(self.export_quality, tk.Variable) else 95)
        ttk.Spinbox(fmt_row, from_=1, to=100, textvariable=self.export_quality, width=6).pack(side=tk.LEFT, padx=(5,0))


    def on_template_selected(self, event=None):
        name = self.selected_template_var.get()
        self.apply_template_by_name(name)

    def apply_template_by_name(self, name):
        tmpl = self.config_manager.get_template(name)
        if not tmpl:
            return
        # Persist selection
        self.config_manager.set_selected_template(name)
        # Apply settings
        self.apply_template_settings(tmpl)

    def apply_template_settings(self, settings):
        try:
            self.watermark_text.set(settings.get("text", "Your Watermark"))
            # Handle auto font size
            auto = bool(settings.get("font_size_auto", False))
            if auto and self.original_image is not None:
                img_w, img_h = self.original_image.size
                base = min(img_w, img_h)
                estimated = max(14, int(base * 0.05))
                self.font_size.set(estimated)
            else:
                self.font_size.set(int(settings.get("font_size", 40)))
            # Opacity (percent)
            opacity_val = settings.get("opacity", 50)
            if isinstance(opacity_val, (int, float)):
                if opacity_val > 100:
                    opacity_percent = max(0, min(100, int(round(opacity_val * 100 / 255))))
                else:
                    opacity_percent = max(0, min(100, int(opacity_val)))
                self.opacity.set(opacity_percent)
            else:
                self.opacity.set(50)
            # Color
            color_val = settings.get("color", [255, 255, 255])
            self.watermark_color = tuple(color_val)
            # Position
            pos_mode = settings.get("position_mode", "bottom-right")
            if pos_mode == "relative":
                self.watermark_position_mode = "relative"
                try:
                    self.watermark_offset["x"] = float(settings.get("offset_x", 0.5))
                    self.watermark_offset["y"] = float(settings.get("offset_y", 0.5))
                except Exception:
                    self.watermark_offset["x"], self.watermark_offset["y"] = 0.5, 0.5
            else:
                self.watermark_position_mode = pos_mode
                self.watermark_offset["x"] = settings.get("offset_x", 0)
                self.watermark_offset["y"] = settings.get("offset_y", 0)
            # Sync grid selection and preview
            self.update_position_grid_selection(self.watermark_position_mode)
            self.clear_position_grid_focus()
            self.preview_watermark()
        except Exception as e:
            print(f"Error applying template settings: {e}")

    def save_template(self):
        """Open a dialog to save current settings as a new template (excluding Default)."""
        dlg = tk.Toplevel(self.root)
        dlg.title("Save Template")
        dlg.transient(self.root)
        dlg.grab_set()
        # Center the dialog
        self.center_window(dlg, width=420, height=400)

        container = ttk.Frame(dlg, padding=15)
        container.pack(fill=tk.BOTH, expand=True)

        ttk.Label(container, text="Template Name:", font=('Segoe UI', 9, 'bold')).pack(anchor='w')
        name_var = tk.StringVar(value="New Template")
        ttk.Entry(container, textvariable=name_var).pack(fill=tk.X, pady=(5, 10))

        ttk.Label(container, text="Text:").pack(anchor='w')
        text_var = tk.StringVar(value=self.watermark_text.get())
        ttk.Entry(container, textvariable=text_var).pack(fill=tk.X, pady=(5, 10))

        size_row = ttk.Frame(container)
        size_row.pack(fill=tk.X)
        ttk.Label(size_row, text="Font Size:").pack(side=tk.LEFT)
        size_var = tk.IntVar(value=self.font_size.get())
        size_spin = ttk.Spinbox(size_row, from_=1, to=500, textvariable=size_var, width=8)
        size_spin.pack(side=tk.LEFT, padx=(5, 10))
        auto_var = tk.BooleanVar(value=False)
        ttk.Checkbutton(size_row, text="Auto font size", variable=auto_var).pack(side=tk.LEFT)
        # Disable font size input when auto is selected
        def _toggle_size_spin_save(*args):
            size_spin.configure(state='disabled' if auto_var.get() else 'normal')
        auto_var.trace_add('write', _toggle_size_spin_save)
        _toggle_size_spin_save()

        opacity_row = ttk.Frame(container)
        opacity_row.pack(fill=tk.X, pady=(10, 0))
        ttk.Label(opacity_row, text="Opacity (0-100):").pack(side=tk.LEFT)
        opacity_var = tk.IntVar(value=self.opacity.get())
        ttk.Spinbox(opacity_row, from_=0, to=100, textvariable=opacity_var, width=6).pack(side=tk.LEFT, padx=(5, 10))

        color_row = ttk.Frame(container)
        color_row.pack(fill=tk.X, pady=(10, 0))
        ttk.Label(color_row, text="Color:").pack(side=tk.LEFT)
        color_preview = tk.Label(color_row, text=" ", bg=self.rgb_to_hex(self.watermark_color), width=2, relief='solid')
        color_preview.pack(side=tk.LEFT, padx=(5, 8))
        def pick_color():
            code = colorchooser.askcolor(title="Choose color")
            if code and code[0]:
                rgb = tuple(int(c) for c in code[0])
                color_preview.configure(bg=self.rgb_to_hex(rgb))
                color_selected_var.set(json.dumps(rgb))
        color_selected_var = tk.StringVar(value=json.dumps(self.watermark_color))
        ttk.Button(color_row, text="Choose...", command=pick_color, style='Secondary.TButton').pack(side=tk.LEFT)

        pos_row = ttk.Frame(container)
        pos_row.pack(fill=tk.X, pady=(10, 0))
        ttk.Label(pos_row, text="Position:").pack(side=tk.LEFT)
        positions = [
            "relative",
            "top-left", "top-center", "top-right",
            "mid-left", "mid-center", "mid-right",
            "bottom-left", "bottom-center", "bottom-right",
            "manual"
        ]
        # Default to saving as relative positioning
        pos_var = tk.StringVar(value="relative")
        ttk.Combobox(pos_row, textvariable=pos_var, values=positions, state='readonly', width=15).pack(side=tk.LEFT, padx=(5, 10))

        offset_row = ttk.Frame(container)
        offset_row.pack(fill=tk.X, pady=(10, 0))
        ttk.Label(offset_row, text="Relative X (0-1):").pack(side=tk.LEFT)
        # Initialize relative offsets from current absolute position/mode
        _rx, _ry = self._compute_relative_from_current()
        offx_var = tk.DoubleVar(value=_rx)
        ttk.Entry(offset_row, textvariable=offx_var, width=8).pack(side=tk.LEFT, padx=(5, 10))
        ttk.Label(offset_row, text="Relative Y (0-1):").pack(side=tk.LEFT)
        offy_var = tk.DoubleVar(value=_ry)
        ttk.Entry(offset_row, textvariable=offy_var, width=8).pack(side=tk.LEFT, padx=(5, 10))

        btns = ttk.Frame(container)
        btns.pack(fill=tk.X, pady=(15, 0))
        def _toggle_offset_visibility_save(*args):
            if pos_var.get() == "relative":
                try:
                    offset_row.pack(before=btns, fill=tk.X, pady=(10, 0))
                except Exception:
                    offset_row.pack(fill=tk.X, pady=(10, 0))
            else:
                offset_row.pack_forget()
        pos_var.trace_add('write', _toggle_offset_visibility_save)
        _toggle_offset_visibility_save()
        def do_save():
            name = name_var.get().strip()
            if not name:
                messagebox.showerror("Save Template", "Template name cannot be empty.", parent=dlg)
                return
            if name == 'Default':
                messagebox.showerror("Save Template", "Default template cannot be modified.", parent=dlg)
                return
            # Parse color
            try:
                color_rgb = tuple(json.loads(color_selected_var.get()))
            except Exception:
                color_rgb = self.watermark_color
            tmpl = {
                "text": text_var.get(),
                "font_size": int(size_var.get()),
                "font_size_auto": bool(auto_var.get()),
                "opacity": int(opacity_var.get()),
                "color": list(color_rgb),
                "position_mode": pos_var.get(),
                "offset_x": float(offx_var.get()),
                "offset_y": float(offy_var.get()),
            }
            try:
                self.config_manager.add_template(name, tmpl)
                # Refresh dropdown
                self.template_names = self.config_manager.list_templates()
                self.template_combo.configure(values=self.template_names)
                messagebox.showinfo("Save Template", "Template saved successfully.", parent=dlg)
                dlg.destroy()
            except Exception as e:
                messagebox.showerror("Save Template", f"Failed to save template: {e}", parent=dlg)
        # Make Save button style same as Cancel
        ttk.Button(btns, text="Save", command=do_save, style='Secondary.TButton').pack(side=tk.LEFT, expand=True, fill=tk.X, padx=(0, 5))
        ttk.Button(btns, text="Cancel", command=dlg.destroy, style='Secondary.TButton').pack(side=tk.RIGHT, expand=True, fill=tk.X, padx=(5, 0))

    def manage_templates(self):
        """Open a dialog to edit or delete templates (Default is protected)."""
        dlg = tk.Toplevel(self.root)
        dlg.title("Manage Templates")
        dlg.transient(self.root)
        dlg.grab_set()
        self.center_window(dlg, width=520, height=520)

        container = ttk.Frame(dlg, padding=15)
        container.pack(fill=tk.BOTH, expand=True)

        left = ttk.Frame(container)
        left.pack(side=tk.LEFT, fill=tk.Y)
        ttk.Label(left, text="Templates:", font=('Segoe UI', 9, 'bold')).pack(anchor='w')
        listbox = tk.Listbox(left, height=20)
        listbox.pack(fill=tk.Y, expand=True, pady=(5,0))
        for name in self.config_manager.list_templates():
            listbox.insert(tk.END, name)

        right = ttk.Frame(container)
        right.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(15,0))
        ttk.Label(right, text="Details:", font=('Segoe UI', 9, 'bold')).pack(anchor='w')

        # Fields
        name_var = tk.StringVar()
        ttk.Label(right, text="Name:").pack(anchor='w')
        name_entry = ttk.Entry(right, textvariable=name_var)
        name_entry.pack(fill=tk.X, pady=(5, 8))

        text_var = tk.StringVar()
        ttk.Label(right, text="Text:").pack(anchor='w')
        ttk.Entry(right, textvariable=text_var).pack(fill=tk.X, pady=(5, 8))

        size_row = ttk.Frame(right)
        size_row.pack(fill=tk.X)
        ttk.Label(size_row, text="Font Size:").pack(side=tk.LEFT)
        size_var = tk.IntVar()
        size_spin_m = ttk.Spinbox(size_row, from_=1, to=500, textvariable=size_var, width=8)
        size_spin_m.pack(side=tk.LEFT, padx=(5, 10))
        auto_var = tk.BooleanVar()
        ttk.Checkbutton(size_row, text="Auto font size", variable=auto_var).pack(side=tk.LEFT)
        # Disable font size input when auto is selected
        def _toggle_size_spin_manage(*args):
            size_spin_m.configure(state='disabled' if auto_var.get() else 'normal')
        auto_var.trace_add('write', _toggle_size_spin_manage)
        _toggle_size_spin_manage()

        opacity_row = ttk.Frame(right)
        opacity_row.pack(fill=tk.X, pady=(10, 0))
        ttk.Label(opacity_row, text="Opacity (0-100):").pack(side=tk.LEFT)
        opacity_var = tk.IntVar()
        ttk.Spinbox(opacity_row, from_=0, to=100, textvariable=opacity_var, width=6).pack(side=tk.LEFT, padx=(5, 10))

        color_row = ttk.Frame(right)
        color_row.pack(fill=tk.X, pady=(10, 0))
        ttk.Label(color_row, text="Color:").pack(side=tk.LEFT)
        color_preview = tk.Label(color_row, text=" ", bg=self.rgb_to_hex((255,255,255)), width=2, relief='solid')
        color_preview.pack(side=tk.LEFT, padx=(5, 8))
        color_selected_var = tk.StringVar(value=json.dumps([255,255,255]))
        def pick_color_manage():
            code = colorchooser.askcolor(title="Choose color")
            if code and code[0]:
                rgb = tuple(int(c) for c in code[0])
                color_preview.configure(bg=self.rgb_to_hex(rgb))
                color_selected_var.set(json.dumps(rgb))
        ttk.Button(color_row, text="Choose...", command=pick_color_manage, style='Secondary.TButton').pack(side=tk.LEFT)

        pos_row = ttk.Frame(right)
        pos_row.pack(fill=tk.X, pady=(10, 0))
        ttk.Label(pos_row, text="Position:").pack(side=tk.LEFT)
        positions = [
            "relative",
            "top-left", "top-center", "top-right",
            "mid-left", "mid-center", "mid-right",
            "bottom-left", "bottom-center", "bottom-right",
            "manual"
        ]
        pos_var = tk.StringVar()
        ttk.Combobox(pos_row, textvariable=pos_var, values=positions, state='readonly', width=15).pack(side=tk.LEFT, padx=(5, 10))

        offset_row = ttk.Frame(right)
        offset_row.pack(fill=tk.X, pady=(10, 0))
        ttk.Label(offset_row, text="Relative X (0-1):").pack(side=tk.LEFT)
        offx_var = tk.DoubleVar()
        ttk.Entry(offset_row, textvariable=offx_var, width=8).pack(side=tk.LEFT, padx=(5, 10))
        ttk.Label(offset_row, text="Relative Y (0-1):").pack(side=tk.LEFT)
        offy_var = tk.DoubleVar()
        ttk.Entry(offset_row, textvariable=offy_var, width=8).pack(side=tk.LEFT, padx=(5, 10))

        # Buttons
        current_selected_name = {'val': None}
        btns = ttk.Frame(right)
        btns.pack(fill=tk.X, pady=(15, 0))
        def do_update():
            name = name_var.get().strip()
            if not current_selected_name['val']:
                messagebox.showerror("Manage Templates", "No template selected.", parent=dlg)
                return
            if current_selected_name['val'] == 'Default':
                messagebox.showerror("Manage Templates", "Default template cannot be modified.", parent=dlg)
                return
            try:
                color_rgb = tuple(json.loads(color_selected_var.get()))
            except Exception:
                color_rgb = (255,255,255)
            tmpl = {
                "text": text_var.get(),
                "font_size": int(size_var.get()),
                "font_size_auto": bool(auto_var.get()),
                "opacity": int(opacity_var.get()),
                "color": list(color_rgb),
                "position_mode": pos_var.get(),
                "offset_x": float(offx_var.get()),
                "offset_y": float(offy_var.get()),
            }
            try:
                # Handle rename if name changed
                old_name = current_selected_name['val']
                if name != old_name:
                    # create new key, delete old
                    templates = self.config_manager.config.setdefault('templates', {})
                    if name in templates:
                        messagebox.showerror("Manage Templates", "A template with the new name already exists.", parent=dlg)
                        return
                    templates[name] = tmpl
                    del templates[old_name]
                    # update selected template if needed
                    if self.config_manager.get_selected_template_name() == old_name:
                        self.config_manager.set_selected_template(name)
                    self.config_manager.save_config()
                else:
                    self.config_manager.update_template(name, tmpl)
                messagebox.showinfo("Manage Templates", "Template updated successfully.", parent=dlg)
                # Refresh list and dropdown without clearing fields
                refresh_templates()
                # Reselect the renamed/current template
                idx = None
                for i in range(listbox.size()):
                    if listbox.get(i) == name:
                        idx = i
                        break
                if idx is not None:
                    listbox.select_clear(0, tk.END)
                    listbox.select_set(idx)
                    listbox.event_generate('<<ListboxSelect>>')
            except Exception as e:
                messagebox.showerror("Manage Templates", f"Failed to update template: {e}", parent=dlg)
        def do_delete():
            name = name_var.get().strip()
            if name == 'Default':
                messagebox.showerror("Manage Templates", "Default template cannot be deleted.", parent=dlg)
                return
            try:
                self.config_manager.delete_template(name)
                messagebox.showinfo("Manage Templates", "Template deleted successfully.", parent=dlg)
                refresh_templates()
                clear_fields()
            except Exception as e:
                messagebox.showerror("Manage Templates", f"Failed to delete template: {e}", parent=dlg)
        ttk.Button(btns, text="Save Changes", command=do_update, style='Secondary.TButton').pack(side=tk.LEFT, expand=True, fill=tk.X, padx=(0, 5))
        ttk.Button(btns, text="Delete", command=do_delete, style='Secondary.TButton').pack(side=tk.RIGHT, expand=True, fill=tk.X, padx=(5, 0))

        def _toggle_offset_visibility_manage(*args):
            if pos_var.get() == "relative":
                try:
                    offset_row.pack(before=btns, fill=tk.X, pady=(10, 0))
                except Exception:
                    offset_row.pack(fill=tk.X, pady=(10, 0))
            else:
                offset_row.pack_forget()
        pos_var.trace_add('write', _toggle_offset_visibility_manage)
        _toggle_offset_visibility_manage()

        def clear_fields():
            name_var.set("")
            text_var.set("")
            size_var.set(40)
            auto_var.set(False)
            _toggle_size_spin_manage()
            opacity_var.set(50)
            color_selected_var.set(json.dumps([255,255,255]))
            color_preview.configure(bg=self.rgb_to_hex((255,255,255)))
            pos_var.set("bottom-right")
            offx_var.set(0)
            offy_var.set(0)
            _toggle_offset_visibility_manage()

        def load_selected(evt=None):
            sel = listbox.curselection()
            if not sel:
                # 不清空右侧字段，保持用户正在编辑的内容
                return
            name = listbox.get(sel[0])
            tmpl = self.config_manager.get_template(name)
            if not tmpl:
                # 未找到模板则不动现有字段
                return
            # 记录当前选中的原始模板名，支持重命名
            current_selected_name['val'] = name
            name_var.set(name)
            text_var.set(tmpl.get('text', ''))
            size_var.set(int(tmpl.get('font_size', 40)))
            auto_var.set(bool(tmpl.get('font_size_auto', False)))
            _toggle_size_spin_manage()
            opacity_var.set(int(tmpl.get('opacity', 50)))
            color = tuple(tmpl.get('color', [255,255,255]))
            color_selected_var.set(json.dumps(list(color)))
            color_preview.configure(bg=self.rgb_to_hex(color))
            pos_var.set(tmpl.get('position_mode', 'bottom-right'))
            offx_var.set(float(tmpl.get('offset_x', 0)))
            offy_var.set(float(tmpl.get('offset_y', 0)))
            # Protect Default in UI by disabling entries
            readonly = (name == 'Default')
            name_entry.configure(state='readonly' if readonly else 'normal')
        
        def refresh_templates():
            listbox.delete(0, tk.END)
            for n in self.config_manager.list_templates():
                listbox.insert(tk.END, n)
            # Update main dropdown as well
            self.template_names = self.config_manager.list_templates()
            self.template_combo.configure(values=self.template_names)
            # Keep current selection if exists
            current = self.config_manager.get_selected_template_name()
            self.selected_template_var.set(current)
        
        listbox.bind('<<ListboxSelect>>', load_selected)
        # Initially select the first item
        if listbox.size() > 0:
            listbox.select_set(0)
            load_selected()


    def center_window(self, win, width=400, height=300):
        try:
            win.update_idletasks()
            sw = win.winfo_screenwidth()
            sh = win.winfo_screenheight()
            x = int((sw/2) - (width/2))
            y = int((sh/2) - (height/2))
            win.geometry(f"{width}x{height}+{x}+{y}")
        except Exception:
            pass

    # ------------------------------
    # Relative position helpers
    # ------------------------------
    def _get_text_size(self, text, font_size):
        try:
            tmp_wm = Watermark(text=text, font_size=font_size, color=(255,255,255,255))
            font = self.image_processor._load_font_with_fallbacks(tmp_wm)
            base_img_size = self.original_image.size if getattr(self, 'original_image', None) else (100, 100)
            tmp_img = Image.new('RGBA', base_img_size, (255, 255, 255, 0))
            draw = ImageDraw.Draw(tmp_img)
            bbox = draw.textbbox((0, 0), text, font=font)
            return (bbox[2] - bbox[0], bbox[3] - bbox[1])
        except Exception:
            return (100, 40)

    def _compute_relative_from_current(self):
        try:
            if not getattr(self, 'original_image', None):
                return (0.5, 0.5)
            img_w, img_h = self.original_image.size
            txt_w, txt_h = self._get_text_size(self.watermark_text.get(), self.font_size.get())
            pos = self.image_processor.calculate_position(
                (img_w, img_h), (txt_w, txt_h), (self.watermark_position_mode, self.watermark_offset)
            )
            margin = 10
            x_min = margin
            x_max = img_w - txt_w - margin
            y_min = margin
            y_max = img_h - txt_h - margin - 20
            x_range = max(1, x_max - x_min)
            y_range = max(1, y_max - y_min)
            rel_x = (pos[0] - x_min) / x_range
            rel_y = (pos[1] - y_min) / y_range
            return (max(0.0, min(1.0, rel_x)), max(0.0, min(1.0, rel_y)))
        except Exception:
            return (0.5, 0.5)

    def rgb_to_hex(self, rgb):
        r, g, b = rgb
        return f"#{r:02x}{g:02x}{b:02x}"

    def export_images(self):
        """Exports all imported images with the current watermark settings."""
        if not self.filepaths:
            messagebox.showwarning("Export", "No images to export.")
            return

        # Prevent exporting to any original folder used by imported images
        def _norm(p):
            try:
                return os.path.normcase(os.path.abspath(p))
            except Exception:
                return p
        original_dirs = {_norm(os.path.dirname(p)) for p in self.filepaths}
        while True:
            output_dir = filedialog.askdirectory(title="Select Output Directory")
            if not output_dir:
                return
            if _norm(output_dir) in original_dirs:
                messagebox.showerror("Invalid Output Folder", "To prevent overwriting originals, exporting to the source folder is not allowed. Please choose a different folder.")
                continue
            break
        success_count = 0
        failure_count = 0
        for path in self.filepaths:
            try:
                original_image = self.image_processor.load_image(path)
                if original_image is None: continue

                # Build watermark from per-image state if available; otherwise use current settings
                state = self.image_states.get(path) if hasattr(self, 'image_states') else None
                if state:
                    text = state.get("text", self.watermark_text.get())
                    font_size = state.get("font_size", self.font_size.get())
                    opacity_val = state.get("opacity", self.opacity.get())
                    if isinstance(opacity_val, (int, float)) and opacity_val > 100:
                        alpha = int(max(0, min(255, int(opacity_val))))
                    else:
                        alpha = int(max(0, min(100, int(opacity_val))) * 255 / 100)
                    color_rgb = tuple(state.get("color", self.watermark_color))
                    position_mode = state.get("position_mode", self.watermark_position_mode)
                    offset = {"x": state.get("offset_x", self.watermark_offset.get("x", 0)), "y": state.get("offset_y", self.watermark_offset.get("y", 0))}
                else:
                    text = self.watermark_text.get()
                    font_size = self.font_size.get()
                    alpha = int(max(0, min(100, self.opacity.get())) * 255 / 100)
                    color_rgb = self.watermark_color
                    position_mode = self.watermark_position_mode
                    offset = self.watermark_offset

                watermark = Watermark(
                    text=text,
                    font_size=font_size,
                    color=color_rgb + (alpha,),
                    position=(position_mode, offset)
                )

                watermarked_image = self.image_processor.apply_watermark(original_image, watermark)

                base_filename = os.path.basename(path)
                name, ext = os.path.splitext(base_filename)
                rule = self.naming_rule.get() if hasattr(self, 'naming_rule') else 'original'
                prefix = self.export_prefix.get() if hasattr(self, 'export_prefix') else ''
                suffix = self.export_suffix.get() if hasattr(self, 'export_suffix') else ''
                fmt = (self.export_format.get() if hasattr(self, 'export_format') else 'JPEG').upper()
                output_ext = '.jpg' if fmt == 'JPEG' else '.png'
                if rule == 'prefix':
                    new_name = f"{prefix}{name}{output_ext}"
                elif rule == 'suffix':
                    new_name = f"{name}{suffix}{output_ext}"
                else:
                    new_name = f"{name}{output_ext}"
                new_filename = new_name
                output_path = os.path.join(output_dir, new_filename)

                self.image_processor.save_image(
                    watermarked_image, 
                    output_path, 
                    self.export_format.get(), 
                    self.export_quality.get()
                )
                print(f"Successfully exported {output_path}")
                success_count += 1
            except Exception as e:
                print(f"Error exporting {path}: {e}")
                failure_count += 1
        # Show summary dialog
        if success_count > 0:
            msg = f"Successfully exported {success_count} photo(s)."
            if failure_count > 0:
                msg += f"\n{failure_count} photo(s) failed."
            messagebox.showinfo("Export Complete", msg)
        else:
            messagebox.showerror("Export Failed", "No photos were exported. Please check errors and try again.")

    def export_single_image(self):
        """Exports the current preview image with the watermark."""
        if not self.current_image_path or not self.original_image:
            messagebox.showwarning("Export", "No image in preview to export.")
            return

        # Prevent exporting to the original folder of the current image
        def _norm(p):
            try:
                return os.path.normcase(os.path.abspath(p))
            except Exception:
                return p
        original_dir = _norm(os.path.dirname(self.current_image_path))
        while True:
            output_dir = filedialog.askdirectory(title="Select Output Folder")
            if not output_dir:
                return
            if _norm(output_dir) == original_dir:
                messagebox.showerror("Invalid Output Folder", "To prevent overwriting originals, exporting to the source folder is not allowed. Please choose a different folder.")
                continue
            break
        # Determine output filename based on naming rule and enforce extension by selected format
        base_filename = os.path.basename(self.current_image_path)
        name = os.path.splitext(base_filename)[0]
        rule = self.naming_rule.get() if hasattr(self, 'naming_rule') else 'original'
        prefix = self.export_prefix.get() if hasattr(self, 'export_prefix') else ''
        suffix = self.export_suffix.get() if hasattr(self, 'export_suffix') else ''
        fmt = (self.export_format.get() or 'JPEG').upper()
        output_ext = '.jpg' if fmt == 'JPEG' else '.png'
        if rule == 'prefix':
            new_name = f"{prefix}{name}{output_ext}"
        elif rule == 'suffix':
            new_name = f"{name}{suffix}{output_ext}"
        else:
            new_name = f"{name}{output_ext}"
        output_path = os.path.join(output_dir, new_name)

        alpha = int(max(0, min(100, self.opacity.get())) * 255 / 100)
        watermark = Watermark(
            text=self.watermark_text.get(),
            font_size=self.font_size.get(),
            color=self.watermark_color + (alpha,),
            position=(self.watermark_position_mode, self.watermark_offset)
        )

        try:
            watermarked_image = self.image_processor.apply_watermark(self.original_image.copy(), watermark)
            self.image_processor.save_image(
                watermarked_image,
                output_path,
                fmt,
                self.export_quality.get()
            )
            print(f"Successfully exported {output_path}")
            messagebox.showinfo("Export Complete", "Successfully exported 1 photo.")
        except Exception as e:
            print(f"Error exporting single image: {e}")
            messagebox.showerror("Export Failed", "Failed to export the photo. Please check errors and try again.")



    def on_drag_start(self, event):
        """Starts the dragging process for the watermark."""
        self.is_dragging = True
        self.drag_start_pos["x"] = event.x
        self.drag_start_pos["y"] = event.y
        
        # Calculate current watermark position in image coordinates
        if self.original_image and self.watermark_text.get():
            # Get current watermark position based on current mode
            current_mode = self.watermark_position_mode
            current_offset = self.watermark_offset.copy()
            
            # Calculate the actual position of the watermark
            from core.watermark import Watermark
            temp_watermark = Watermark(
                text=self.watermark_text.get(),
                font_size=self.font_size.get(),
                color=(255, 255, 255, 255),
                position=(current_mode, current_offset)
            )
            
            # Get the actual position from the image processor
            from PIL import ImageDraw, ImageFont
            font = self.image_processor._load_font_with_fallbacks(temp_watermark)
            draw = ImageDraw.Draw(Image.new('RGBA', (1, 1)))
            text_bbox = draw.textbbox((0, 0), temp_watermark.text, font=font)
            text_width = text_bbox[2] - text_bbox[0]
            text_height = text_bbox[3] - text_bbox[1]
            
            actual_pos = self.image_processor.calculate_position(
                self.original_image.size,
                (text_width, text_height),
                (current_mode, current_offset)
            )
            
            # Set the actual position as the offset for manual mode
            self.watermark_offset["x"] = actual_pos[0]
            self.watermark_offset["y"] = actual_pos[1]
        
        self.watermark_position_mode = "manual" # Switch to manual positioning
        # Clear nine-grid selection when switching to manual mode
        self.update_position_grid_selection(None)

    def on_drag_motion(self, event):
        """Handles the dragging motion."""
        if self.is_dragging:
            dx = (event.x - self.drag_start_pos["x"]) / self.display_to_original_ratio
            dy = (event.y - self.drag_start_pos["y"]) / self.display_to_original_ratio
            self.watermark_offset["x"] += dx
            self.watermark_offset["y"] += dy
            self.drag_start_pos["x"] = event.x
            self.drag_start_pos["y"] = event.y
            self.preview_watermark()

    def on_drag_end(self, event):
        """Ends the dragging process."""
        self.is_dragging = False

    def set_watermark_position(self, position):
        """Sets the watermark position and updates the preview."""
        self.watermark_position_mode = position
        self.watermark_offset = {"x": 0, "y": 0} # Reset offset when using presets
        # Update nine-grid visual selection
        self.update_position_grid_selection(position)
        # Remove focus ring to avoid dotted outline sticking around
        self.clear_position_grid_focus()
        self.preview_watermark()

    def choose_color_and_preview(self):
        """Opens a color chooser and triggers a preview."""
        color_code = colorchooser.askcolor(title="Choose watermark color")
        if color_code and color_code[0]:
            self.watermark_color = tuple(int(c) for c in color_code[0])
            self.preview_watermark()

    def schedule_preview(self, *args):
        """Schedules a watermark preview."""
        if self.preview_job:
            self.root.after_cancel(self.preview_job)
        self.preview_job = self.root.after(50, self.preview_watermark) # Short delay for responsiveness

    def import_images(self, filepaths=None):
        """Opens a file dialog to import images or accepts a list of filepaths."""
        if not filepaths:
            filetypes = (('Image files', '*.jpg *.jpeg *.png *.bmp *.tiff'), ('All files', '*.*'))
            filepaths = filedialog.askopenfilenames(title='Select one or more images', filetypes=filetypes)
        
        if filepaths:
            new_paths = []
            for p in filepaths:
                try:
                    norm = os.path.normcase(os.path.abspath(p))
                except Exception:
                    norm = p
                if norm not in self.filepath_set:
                    new_paths.append(p)
                    self.filepath_set.add(norm)
            if new_paths:
                self.filepaths.extend(new_paths)
                self.update_thumbnail_list()

    def import_folder(self):
        """Opens a dialog to select a folder and imports all valid images from it."""
        folder_path = filedialog.askdirectory(title='Select a folder')
        if folder_path:
            filepaths = []
            for filename in os.listdir(folder_path):
                if filename.lower().endswith(('.png', '.jpg', '.jpeg', '.bmp', '.tiff')):
                    filepaths.append(os.path.join(folder_path, filename))
            self.import_images(filepaths)

    def update_thumbnail_list(self):
        """Updates the list of thumbnails."""
        for widget in self.scrollable_frame.winfo_children():
            widget.destroy()
        self.tk_thumbnails.clear()
        for i, path in enumerate(self.filepaths):
            try:
                img = self.image_processor.load_image(path)
                if img is None: continue
                thumbnail = self.image_processor.create_thumbnail(img.copy(), (100, 100))
                tk_thumb = ImageTk.PhotoImage(thumbnail)
                self.tk_thumbnails.append(tk_thumb)
                thumb_frame = ttk.Frame(self.scrollable_frame, style='Card.TFrame')
                thumb_frame.pack(fill=tk.X, pady=3, padx=5)
                
                # Fixed-size image container and label (uniform thumbnail area)
                img_container = tk.Frame(thumb_frame, width=110, height=110, bg='white', relief='solid', borderwidth=1)
                img_container.pack(side=tk.LEFT, padx=8, pady=8)
                img_container.pack_propagate(False)

                label = tk.Label(img_container, image=tk_thumb, bg='white')
                label.pack(expand=True)
                label.bind("<Button-1>", lambda e, p=path: self.on_image_select(p))
                label.bind("<Button-3>", lambda e, p=path: self.show_context_menu(e, p))  # Right-click for context menu
                img_container.bind("<Button-1>", lambda e, p=path: self.on_image_select(p))
                img_container.bind("<Button-3>", lambda e, p=path: self.show_context_menu(e, p))  # Right-click for context menu

                # Fixed-size text container; ensure wrap within available width
                text_container = tk.Frame(thumb_frame, width=160, height=110, bg='white')
                text_container.pack(side=tk.LEFT, padx=(0, 8), pady=8)
                text_container.pack_propagate(False)

                # Format filename: insert newline after every 15 characters for controlled wrapping
                base_name = os.path.basename(path)
                display_name = '\n'.join([base_name[i:i+15] for i in range(0, len(base_name), 15)])

                filename_label = tk.Label(text_container, text=display_name, 
                                        wraplength=150, font=('Segoe UI', 9), 
                                        bg='white', fg='#212529', justify='center', anchor='center')
                # Add extra right padding to visually shift content slightly left
                filename_label.pack(fill=tk.BOTH, expand=True, padx=(0, 10))
                filename_label.bind("<Button-1>", lambda e, p=path: self.on_image_select(p))
                filename_label.bind("<Button-3>", lambda e, p=path: self.show_context_menu(e, p))  # Right-click for context menu
                text_container.bind("<Button-1>", lambda e, p=path: self.on_image_select(p))
                text_container.bind("<Button-3>", lambda e, p=path: self.show_context_menu(e, p))  # Right-click for context menu
            except Exception as e:
                print(f"Error processing {path}: {e}")

    def on_image_select(self, path):
        """Handles image selection."""
        self.save_current_image_state() # Save state of the previous image
        self.current_image_path = path
        self.load_image_state(path) # Load state for the new image
        # Sync nine-grid visual selection with the loaded state
        self.update_position_grid_selection(self.watermark_position_mode)
        # Clear any lingering focus ring from previous button
        self.clear_position_grid_focus()
        try:
            self.original_image = self.image_processor.load_image(path)
            if self.original_image is None: return
            # If using defaults (no prior state), auto-derive an initial font size from image size
            if path not in self.image_states:
                img_w, img_h = self.original_image.size
                # Use shorter side with a sensible ratio for legibility
                base = min(img_w, img_h)
                estimated = max(14, int(base * 0.05))  # ~5% of shorter edge
                self.font_size.set(estimated)
            self.preview_watermark()
        except Exception as e:
            print(f"Error displaying main image {path}: {e}")

    def display_image_in_workspace(self, img):
        """Displays an image in the main workspace."""
        # Use fixed preview area's size to compute scaling, avoid layout growth
        width = self.image_display_frame.winfo_width()
        height = self.image_display_frame.winfo_height()
        if width <= 1 or height <= 1:
            width = getattr(self, 'preview_width', 900)
            height = getattr(self, 'preview_height', 600)
        workspace_size = (width, height)

        self.display_to_original_ratio = min(
            workspace_size[0] / self.original_image.width,
            workspace_size[1] / self.original_image.height
        ) if self.original_image else 1.0
        display_img = self.image_processor.resize_to_fit(img, workspace_size)
        self.main_photo_image = ImageTk.PhotoImage(display_img)
        self.image_label.config(image=self.main_photo_image, text="")

    def preview_watermark(self):
        """Applies the watermark for preview."""
        if not self.original_image:
            return

        self.save_current_image_state()

        position_tuple = (self.watermark_position_mode, self.watermark_offset)

        alpha = int(max(0, min(100, self.opacity.get())) * 255 / 100)
        watermark = Watermark(
            text=self.watermark_text.get(),
            font_size=self.font_size.get(),
            color=self.watermark_color + (alpha,),
            position=position_tuple
        )

        watermarked_image = self.image_processor.apply_watermark(self.original_image.copy(), watermark)
        self.display_image_in_workspace(watermarked_image)

    def run(self):
        """Runs the application loop."""
        self.root.mainloop()

    def save_current_image_state(self):
        """Saves the watermark state for the current image."""
        if self.current_image_path:
            self.image_states[self.current_image_path] = {
                "text": self.watermark_text.get(),
                "font_size": self.font_size.get(),
                "opacity": self.opacity.get(),
                "color": self.watermark_color,
                "position_mode": self.watermark_position_mode,
                "offset_x": self.watermark_offset["x"],
                "offset_y": self.watermark_offset["y"],
            }

    def load_image_state(self, image_path):
        """Loads the watermark state for the given image path."""
        state = self.image_states.get(image_path)
        if state:
            self.watermark_text.set(state.get("text", ""))
            self.font_size.set(state.get("font_size", 40))
            # migrate opacity from 0-255 to 0-100 if needed
            opacity_val = state.get("opacity", 50)
            if isinstance(opacity_val, (int, float)):
                if opacity_val > 100:
                    opacity_percent = max(0, min(100, int(round(opacity_val * 100 / 255))))
                else:
                    opacity_percent = max(0, min(100, int(opacity_val)))
                self.opacity.set(opacity_percent)
            else:
                self.opacity.set(50)
            self.watermark_color = tuple(state.get("color", (255, 255, 255)))
            self.watermark_position_mode = state.get("position_mode", "bottom-right")
            self.watermark_offset["x"] = state.get("offset_x", 0)
            self.watermark_offset["y"] = state.get("offset_y", 0)
        else:
            # Reset to default if no state is found
            self.watermark_text.set("Your Watermark")
            self.font_size.set(40)
            self.opacity.set(50)
            self.watermark_color = (255, 255, 255)
            self.watermark_position_mode = "bottom-right"
            self.watermark_offset = {"x": 0, "y": 0}

    def on_drop(self, event):
        """Handles files dropped onto the window."""
        filepaths = self.root.tk.splitlist(event.data)
        valid_filepaths = []
        for path in filepaths:
            if os.path.isdir(path):
                for filename in os.listdir(path):
                    if filename.lower().endswith(('.png', '.jpg', '.jpeg', '.bmp', '.tiff')):
                        valid_filepaths.append(os.path.join(path, filename))
            elif os.path.isfile(path) and path.lower().endswith(('.png', '.jpg', '.jpeg', '.bmp', '.tiff')):
                valid_filepaths.append(path)
        self.import_images(valid_filepaths)

    def show_context_menu(self, event, image_path):
        """Shows the right-click context menu for an image."""
        context_menu = tk.Menu(self.root, tearoff=0)
        context_menu.add_command(label="🗑️ Remove Image", command=lambda: self.remove_image(image_path))
        
        try:
            context_menu.tk_popup(event.x_root, event.y_root)
        finally:
            context_menu.grab_release()

    def remove_image(self, image_path):
        """Removes an image from the list and updates the UI."""
        if image_path in self.filepaths:
            # Remove from filepaths list
            self.filepaths.remove(image_path)
            
            # Remove normalized path from set to allow re-importing later
            try:
                norm = os.path.normcase(os.path.abspath(image_path))
            except Exception:
                norm = image_path
            if hasattr(self, 'filepath_set'):
                self.filepath_set.discard(norm)
            
            # Remove from image states if it exists
            if image_path in self.image_states:
                del self.image_states[image_path]
            
            # If this was the currently selected image, clear the preview
            if self.current_image_path == image_path:
                self.current_image_path = None
                self.original_image = None
                self.image_label.config(image="", text="🎨 Workspace\n\nDrag & drop images here or use the import buttons\n\nSelect an image from the list to start editing")
            
            # Update the thumbnail list
            self.update_thumbnail_list()
            print(f"Removed image: {os.path.basename(image_path)}")


    def update_position_grid_selection(self, selected_pos):
        """Updates the visual selection state of the nine-grid position buttons.
        If selected_pos is one of the predefined positions, highlight that button;
        otherwise, clear all selections."""
        positions = {"top-left", "top-center", "top-right",
                     "mid-left", "mid-center", "mid-right",
                     "bottom-left", "bottom-center", "bottom-right"}
        for pos, btn in getattr(self, 'position_buttons', {}).items():
            if selected_pos in positions and pos == selected_pos:
                btn.config(style='Selected.TButton')
            else:
                btn.config(style='Secondary.TButton')

    def clear_position_grid_focus(self):
        """Move focus away from position buttons to avoid the dotted focus ring persisting."""
        try:
            # Prefer focusing the main image label if available, else focus root
            if getattr(self, 'image_label', None):
                self.image_label.focus_set()
            else:
                self.root.focus_set()
        except Exception:
            pass
