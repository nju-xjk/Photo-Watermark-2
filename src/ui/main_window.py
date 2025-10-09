import tkinter as tk
from tkinter import filedialog, ttk, colorchooser
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
        self.root.title("Photo Watermark 2")
        self.root.geometry("1400x800")

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

        self.root.drop_target_register('DND_FILES')
        self.root.dnd_bind('<<Drop>>', self.on_drop)

    def create_widgets(self):
        """Creates the widgets for the main window."""
        main_frame = tk.Frame(self.root)
        main_frame.pack(fill=tk.BOTH, expand=True)

        # Left panel for thumbnails
        left_panel = tk.Frame(main_frame, width=250)
        left_panel.pack(side=tk.LEFT, fill=tk.Y, padx=5, pady=5)
        left_panel.pack_propagate(False)

        self.import_button = tk.Button(left_panel, text="Import Images", command=self.import_images)
        self.import_button.pack(pady=5, fill=tk.X)

        self.import_folder_button = tk.Button(left_panel, text="Import Folder", command=self.import_folder)
        self.import_folder_button.pack(pady=5, fill=tk.X)

        canvas = tk.Canvas(left_panel)
        scrollbar = ttk.Scrollbar(left_panel, orient="vertical", command=canvas.yview)
        self.scrollable_frame = ttk.Frame(canvas)
        self.scrollable_frame.bind("<Configure>", lambda e: canvas.configure(scrollregion=canvas.bbox("all")))
        canvas.create_window((0, 0), window=self.scrollable_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)
        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")

        # Center panel for the main image view
        self.center_panel = tk.Frame(main_frame)
        self.center_panel.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=5, pady=5)

        self.image_label = tk.Label(self.center_panel, text="Workspace - Select an image to view")
        self.image_label.pack(fill=tk.BOTH, expand=True)
        self.image_label.bind("<Button-1>", self.on_drag_start)
        self.image_label.bind("<B1-Motion>", self.on_drag_motion)
        self.image_label.bind("<ButtonRelease-1>", self.on_drag_end)

        # Right panel for controls
        self.control_panel = tk.Frame(main_frame, width=300)
        self.control_panel.pack(side=tk.RIGHT, fill=tk.Y, padx=5, pady=5)
        self.control_panel.pack_propagate(False)

        self.create_template_controls()
        self.create_watermark_controls()
        self.create_export_controls()

    def create_template_controls(self):
        """Creates the widgets for saving and loading templates."""
        template_frame = ttk.LabelFrame(self.control_panel, text="Watermark Templates")
        template_frame.pack(fill=tk.X, pady=(10, 0))

        save_button = tk.Button(template_frame, text="Save Template", command=self.save_template)
        save_button.pack(side=tk.LEFT, expand=True, fill=tk.X, padx=5, pady=5)

        load_button = tk.Button(template_frame, text="Load Template", command=self.load_template)
        load_button.pack(side=tk.RIGHT, expand=True, fill=tk.X, padx=5, pady=5)

    def create_watermark_controls(self):
        """Creates the widgets for the watermark control panel."""
        watermark_frame = ttk.LabelFrame(self.control_panel, text="Watermark Settings")
        watermark_frame.pack(fill=tk.X, pady=10)

        ttk.Label(watermark_frame, text="Watermark Text:").pack(anchor="w", pady=(5, 2), padx=5)
        self.watermark_text = tk.StringVar(value="Your Watermark")
        self.watermark_text.trace_add("write", self.schedule_preview)
        ttk.Entry(watermark_frame, textvariable=self.watermark_text).pack(fill=tk.X, padx=5)

        ttk.Label(watermark_frame, text="Font Size:").pack(anchor="w", pady=(10, 2), padx=5)
        self.font_size = tk.IntVar(value=40)
        self.font_size.trace_add("write", self.schedule_preview)
        ttk.Spinbox(watermark_frame, from_=1, to=500, textvariable=self.font_size).pack(fill=tk.X, padx=5)

        ttk.Label(watermark_frame, text="Opacity (0-255):").pack(anchor="w", pady=(10, 2), padx=5)
        self.opacity = tk.IntVar(value=128)
        ttk.Scale(watermark_frame, from_=0, to=255, orient=tk.HORIZONTAL, variable=self.opacity, command=self.schedule_preview).pack(fill=tk.X, padx=5)

        self.color_button = tk.Button(watermark_frame, text="Choose Color", command=self.choose_color_and_preview)
        self.color_button.pack(pady=10, fill=tk.X, padx=5)
        self.watermark_color = (255, 255, 255)

        ttk.Label(watermark_frame, text="Position:").pack(anchor="w", pady=(10, 5), padx=5)
        position_frame = ttk.Frame(watermark_frame)
        position_frame.pack(fill=tk.X, padx=5)
        positions = ["top-left", "top-center", "top-right",
                     "mid-left", "mid-center", "mid-right",
                     "bottom-left", "bottom-center", "bottom-right"]
        for i, pos in enumerate(positions):
            btn = tk.Button(position_frame, text=pos.replace("-", "\n"), 
                          command=lambda p=pos: self.set_watermark_position(p), 
                          width=10, height=3)
            btn.grid(row=i//3, column=i%3, sticky="nsew")
            position_frame.grid_columnconfigure(i%3, weight=1)
        position_frame.grid_rowconfigure(0, weight=1)
        position_frame.grid_rowconfigure(1, weight=1)
        position_frame.grid_rowconfigure(2, weight=1)

    def create_export_controls(self):
        """Creates the widgets for the export control panel."""
        export_frame = ttk.LabelFrame(self.control_panel, text="Export Settings")
        export_frame.pack(fill=tk.X, pady=10)

        ttk.Label(export_frame, text="Filename Prefix:").pack(anchor="w", padx=5)
        self.export_prefix = tk.StringVar(value="watermarked_")
        ttk.Entry(export_frame, textvariable=self.export_prefix).pack(fill=tk.X, padx=5, pady=2)

        ttk.Label(export_frame, text="Format:").pack(anchor="w", padx=5, pady=(5,0))
        self.export_format = tk.StringVar(value="JPEG")
        format_menu = ttk.Combobox(export_frame, textvariable=self.export_format, values=["JPEG", "PNG", "BMP", "TIFF"])
        format_menu.pack(fill=tk.X, padx=5, pady=2)

        ttk.Label(export_frame, text="Quality (JPEG only):").pack(anchor="w", padx=5, pady=(5,0))
        self.export_quality = tk.IntVar(value=95)
        ttk.Scale(export_frame, from_=1, to=100, orient=tk.HORIZONTAL, variable=self.export_quality).pack(fill=tk.X, padx=5, pady=2)

        export_button = tk.Button(export_frame, text="Export All Images", command=self.export_images)
        export_button.pack(pady=10, fill=tk.X, padx=5)

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

        watermark = Watermark(
            text=self.watermark_text.get(),
            font_size=self.font_size.get(),
            color=self.watermark_color + (self.opacity.get(),),
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
            self.filepaths.extend(filepaths)
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
                thumb_frame = tk.Frame(self.scrollable_frame)
                thumb_frame.pack(fill=tk.X, pady=5, padx=5)
                label = tk.Label(thumb_frame, image=tk_thumb)
                label.pack(side=tk.LEFT)
                label.bind("<Button-1>", lambda e, p=path: self.on_image_select(p))
                filename_label = tk.Label(thumb_frame, text=os.path.basename(path), wraplength=120)
                filename_label.pack(side=tk.LEFT, padx=5)
                filename_label.bind("<Button-1>", lambda e, p=path: self.on_image_select(p))
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
        workspace_size = (self.center_panel.winfo_width(), self.center_panel.winfo_height())
        if workspace_size[0] > 1 and workspace_size[1] > 1:
            self.display_to_original_ratio = min(workspace_size[0] / self.original_image.width, workspace_size[1] / self.original_image.height)
            display_img = self.image_processor.resize_to_fit(img, workspace_size)
        else:
            self.display_to_original_ratio = 1.0
            display_img = img
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