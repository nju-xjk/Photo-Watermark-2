import tkinter as tk
from tkinter import filedialog, ttk, colorchooser
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
        self.filepaths = []
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

        self.create_widgets()

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

        self.import_button = ttk.Button(toolbar, text="📷 Select Images", command=self.import_images, style='Primary.TButton')
        self.import_button.pack(side=tk.LEFT, padx=(10, 5), pady=10)

        self.import_folder_button = ttk.Button(toolbar, text="📂 Select Folder", command=self.import_folder, style='Secondary.TButton')
        self.import_folder_button.pack(side=tk.LEFT, padx=5, pady=10)

        self.export_button = ttk.Button(toolbar, text="📤 Export All", command=self.export_images, style='Secondary.TButton')
        self.export_button.pack(side=tk.LEFT, padx=5, pady=10)

        self.export_single_button = ttk.Button(toolbar, text="🖼️ Export Single", command=self.export_single_image, style='Secondary.TButton')
        self.export_single_button.pack(side=tk.LEFT, padx=5, pady=10)

        # Left panel for thumbnails
        left_panel = ttk.Frame(main_frame, style='Card.TFrame', width=280)
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
        self.preview_width = 900
        self.preview_height = 600
        self.image_display_frame = ttk.Frame(self.center_panel, width=self.preview_width, height=self.preview_height)
        self.image_display_frame.pack(padx=20, pady=20)
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
        self.control_panel = ttk.Frame(main_frame, style='Card.TFrame', width=320)
        self.control_panel.pack(side=tk.RIGHT, fill=tk.Y)
        self.control_panel.pack_propagate(False)

        self.create_template_controls()
        self.create_watermark_controls()

    def create_template_controls(self):
        """Creates the widgets for saving and loading templates."""
        template_frame = ttk.LabelFrame(self.control_panel, text="💾 Watermark Templates", style='Modern.TLabelframe')
        template_frame.pack(fill=tk.X, padx=15, pady=(15, 10))

        button_frame = ttk.Frame(template_frame)
        button_frame.pack(fill=tk.X, padx=10, pady=10)

        save_button = ttk.Button(button_frame, text="💾 Save Template", command=self.save_template, style='Secondary.TButton')
        save_button.pack(side=tk.LEFT, expand=True, fill=tk.X, padx=(0, 5))

        load_button = ttk.Button(button_frame, text="📂 Load Template", command=self.load_template, style='Secondary.TButton')
        load_button.pack(side=tk.RIGHT, expand=True, fill=tk.X, padx=(5, 0))

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
        
        ttk.Label(opacity_frame, text="👁️ Opacity (0% - 100%):", font=('Segoe UI', 9, 'bold')).pack(anchor="w")
        self.opacity = tk.IntVar(value=50)
        opacity_scale = ttk.Scale(opacity_frame, from_=0, to=100, orient=tk.HORIZONTAL, variable=self.opacity, command=self.schedule_preview)
        opacity_scale.pack(fill=tk.X, pady=(5, 0))

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
        
        for i, pos in enumerate(positions):
            btn = ttk.Button(pos_grid_frame, text=pos.replace("-", "\n"), 
                          command=lambda p=pos: self.set_watermark_position(p), 
                          style='Secondary.TButton',
                          width=8)
            btn.grid(row=i//3, column=i%3, sticky="nsew", padx=2, pady=2)
            pos_grid_frame.grid_columnconfigure(i%3, weight=1)
        
        pos_grid_frame.grid_rowconfigure(0, weight=1)
        pos_grid_frame.grid_rowconfigure(1, weight=1)
        pos_grid_frame.grid_rowconfigure(2, weight=1)


    def save_template(self):
        """Saves the current watermark settings to a template file."""
        settings = {
            "text": self.watermark_text.get(),
            "font_size": self.font_size.get(),
            "opacity": self.opacity.get(),
            "color": self.watermark_color,
            "position_mode": self.watermark_position_mode,
            "offset_x": self.watermark_offset["x"],
            "offset_y": self.watermark_offset["y"],
        }
        filepath = filedialog.asksaveasfilename(
            title="Save Watermark Template",
            defaultextension=".json",
            filetypes=[("JSON files", "*.json"), ("All files", "*.*")]
        )
        if filepath:
            self.config_manager.save_watermark_template(settings, filepath)
            print(f"Template saved to {filepath}")

    def load_template(self):
        """Loads watermark settings from a template file."""
        filepath = filedialog.askopenfilename(
            title="Load Watermark Template",
            filetypes=[("JSON files", "*.json"), ("All files", "*.*")]
        )
        if filepath:
            settings = self.config_manager.load_watermark_template(filepath)
            if settings:
                self.watermark_text.set(settings.get("text", ""))
                self.font_size.set(settings.get("font_size", 40))
                self.opacity.set(settings.get("opacity", 128))
                self.watermark_color = tuple(settings.get("color", (255, 255, 255)))
                self.watermark_position_mode = settings.get("position_mode", "bottom-right")
                self.watermark_offset["x"] = settings.get("offset_x", 0)
                self.watermark_offset["y"] = settings.get("offset_y", 0)
                self.preview_watermark()
                print(f"Template loaded from {filepath}")

    def export_images(self):
        """Exports all imported images with the current watermark settings."""
        if not self.filepaths:
            print("No images to export.")
            return

        output_dir = filedialog.askdirectory(title="Select Output Directory")
        if not output_dir:
            return

        alpha = int(max(0, min(100, self.opacity.get())) * 255 / 100)
        watermark = Watermark(
            text=self.watermark_text.get(),
            font_size=self.font_size.get(),
            color=self.watermark_color + (alpha,),
            position=(self.watermark_position_mode, self.watermark_offset)
        )

        for path in self.filepaths:
            try:
                original_image = self.image_processor.load_image(path)
                if original_image is None: continue

                watermarked_image = self.image_processor.apply_watermark(original_image, watermark)

                base_filename = os.path.basename(path)
                new_filename = f"{self.export_prefix.get()}{base_filename}"
                output_path = os.path.join(output_dir, new_filename)

                self.image_processor.save_image(
                    watermarked_image, 
                    output_path, 
                    self.export_format.get(), 
                    self.export_quality.get()
                )
                print(f"Successfully exported {output_path}")
            except Exception as e:
                print(f"Error exporting {path}: {e}")
        print("Export complete.")

    def export_single_image(self):
        """Exports the current preview image with the watermark."""
        if not self.current_image_path or not self.original_image:
            print("No image in preview to export.")
            return

        output_path = filedialog.asksaveasfilename(
            title="Save As",
            defaultextension=f".{self.export_format.get().lower()}",
            filetypes=[(f"{self.export_format.get()} files", f"*.{self.export_format.get().lower()}"), ("All files", "*.*")]
        )
        if not output_path:
            return

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
                self.export_format.get(),
                self.export_quality.get()
            )
            print(f"Successfully exported {output_path}")
        except Exception as e:
            print(f"Error exporting single image: {e}")



    def on_drag_start(self, event):
        """Starts the dragging process for the watermark."""
        self.is_dragging = True
        self.drag_start_pos["x"] = event.x
        self.drag_start_pos["y"] = event.y
        self.watermark_position_mode = "manual" # Switch to manual positioning

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
            new_paths = [p for p in filepaths if p not in self.filepaths]
            self.filepaths.extend(new_paths)
            if new_paths:
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
                img_container.bind("<Button-1>", lambda e, p=path: self.on_image_select(p))

                # Fixed-size text container and label (uniform text area)
                text_container = tk.Frame(thumb_frame, width=150, height=110, bg='white')
                text_container.pack(side=tk.LEFT, padx=(0, 8), pady=8)
                text_container.pack_propagate(False)

                filename_label = tk.Label(text_container, text=os.path.basename(path), 
                                        wraplength=140, font=('Segoe UI', 9), 
                                        bg='white', fg='#212529', justify='left', anchor='nw')
                filename_label.pack(fill=tk.BOTH, expand=True)
                filename_label.bind("<Button-1>", lambda e, p=path: self.on_image_select(p))
                text_container.bind("<Button-1>", lambda e, p=path: self.on_image_select(p))
            except Exception as e:
                print(f"Error processing {path}: {e}")

    def on_image_select(self, path):
        """Handles image selection."""
        self.save_current_image_state() # Save state of the previous image
        self.current_image_path = path
        self.load_image_state(path) # Load state for the new image
        try:
            self.original_image = self.image_processor.load_image(path)
            if self.original_image is None: return
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

        watermark = Watermark(
            text=self.watermark_text.get(),
            font_size=self.font_size.get(),
            color=self.watermark_color + (self.opacity.get(),),
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
            self.opacity.set(state.get("opacity", 128))
            self.watermark_color = tuple(state.get("color", (255, 255, 255)))
            self.watermark_position_mode = state.get("position_mode", "bottom-right")
            self.watermark_offset["x"] = state.get("offset_x", 0)
            self.watermark_offset["y"] = state.get("offset_y", 0)
        else:
            # Reset to default if no state is found
            self.watermark_text.set("Your Watermark")
            self.font_size.set(40)
            self.opacity.set(128)
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