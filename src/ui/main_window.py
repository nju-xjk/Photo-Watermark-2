from __future__ import annotations

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QMainWindow,
    QWidget,
    QHBoxLayout,
    QVBoxLayout,
    QListWidget,
    QLabel,
    QTabWidget,
    QPushButton,
    QFileDialog,
    QToolBar,
    QStatusBar,
)
from PySide6.QtGui import QPixmap
from pathlib import Path

from ..core.models import ProjectState
from ..core.image_loader import scan_directory_for_images, create_image_items
from .image_list import ImageListWidget
from .preview import PreviewWidget
from .panels import TextWatermarkPanel, ExportPanel, ImageWatermarkPanel, TemplatesPanel
from ..core.models import ExportOptions
from ..core.exporter import export_image
from ..core.templates import save_last, load_last, save_named, list_templates, delete_template


class MainWindow(QMainWindow):
    def __init__(self) -> None:
        super().__init__()
        self.setWindowTitle("Photo Watermark 2")
        self.resize(1200, 800)

        self._init_actions()
        self._init_ui()

    def _init_actions(self) -> None:
        toolbar = QToolBar("Main Toolbar")
        self.addToolBar(toolbar)

        import_action = QPushButton("导入图片")
        import_action.clicked.connect(self._on_import_files)
        toolbar.addWidget(import_action)

        import_dir_action = QPushButton("导入文件夹")
        import_dir_action.clicked.connect(self._on_import_dir)
        toolbar.addWidget(import_dir_action)

        export_action = QPushButton("导出")
        export_action.clicked.connect(self._on_export)
        toolbar.addWidget(export_action)

        self.setStatusBar(QStatusBar())

    def _init_ui(self) -> None:
        central = QWidget()
        self.setCentralWidget(central)

        root_layout = QHBoxLayout(central)

        # Left: image list
        left_panel = QWidget()
        left_layout = QVBoxLayout(left_panel)
        self.image_list = ImageListWidget()
        self.image_list.fileDropped.connect(self._on_files_dropped)
        self.image_list.currentRowChanged.connect(self._on_image_selected)
        left_layout.addWidget(QLabel("已导入图片"))
        left_layout.addWidget(self.image_list)

        # Center: preview placeholder
        center_panel = QWidget()
        center_layout = QVBoxLayout(center_panel)
        self.preview_widget = PreviewWidget()
        center_layout.addWidget(self.preview_widget)

        # Right: properties tabs
        right_panel = QWidget()
        right_layout = QVBoxLayout(right_panel)
        tabs = QTabWidget()
        self.text_panel = TextWatermarkPanel()
        self.text_panel.textChanged.connect(self._on_text_changed)
        self.text_panel.opacityChanged.connect(self._on_opacity_changed)
        self.text_panel.gridChanged.connect(self._on_grid_changed)
        self.text_panel.fontChanged.connect(self._on_font_changed)
        self.text_panel.styleChanged.connect(self._on_style_changed)
        self.text_panel.colorChanged.connect(self._on_color_changed)
        self.text_panel.rotationChanged.connect(self._on_rotation_changed)
        tabs.addTab(self.text_panel, "文本水印")
        self.image_panel = ImageWatermarkPanel()
        self.image_panel.changed.connect(self._on_image_wm_changed)
        tabs.addTab(self.image_panel, "图片水印")
        self.export_panel = ExportPanel()
        tabs.addTab(self.export_panel, "导出设置")
        self.templates_panel = TemplatesPanel()
        self.templates_panel.saveRequested.connect(self._on_template_save)
        self.templates_panel.loadRequested.connect(self._on_template_load)
        self.templates_panel.deleteRequested.connect(self._on_template_delete)
        tabs.addTab(self.templates_panel, "模板")
        right_layout.addWidget(tabs)

        root_layout.addWidget(left_panel, 2)
        root_layout.addWidget(center_panel, 5)
        root_layout.addWidget(right_panel, 3)

    def _on_import_files(self) -> None:
        files, _ = QFileDialog.getOpenFileNames(self, "选择图片", "", "Images (*.png *.jpg *.jpeg *.bmp *.tif *.tiff)")
        if not files:
            return
        self._add_paths(files)
        self.statusBar().showMessage(f"已导入 {len(files)} 张图片", 3000)

    def _on_import_dir(self) -> None:
        directory = QFileDialog.getExistingDirectory(self, "选择文件夹")
        if not directory:
            return
        paths = scan_directory_for_images(directory)
        self._add_paths(paths)
        self.statusBar().showMessage(f"从文件夹导入 {len(paths)} 张图片", 3000)

    def _on_export(self) -> None:
        out_dir = QFileDialog.getExistingDirectory(self, "选择输出文件夹")
        if not out_dir:
            return
        if not hasattr(self, "state") or not self.state.images:
            self.statusBar().showMessage("请先导入图片", 3000)
            return
        # 禁止与任一输入目录相同
        import_dirs = {str(Path(item.path).parent) for item in self.state.images}
        if out_dir in import_dirs:
            self.statusBar().showMessage("输出目录不能与原目录相同", 4000)
            return

        options = ExportOptions(
            output_dir=out_dir,
            format=self.export_panel.format_combo.currentText(),
            naming_mode=self.export_panel.naming_mode.currentText(),
            naming_value=self.export_panel.naming_value.text(),
            jpeg_quality=self.export_panel.jpeg_quality.value(),
            resize_mode=self.export_panel.resize_mode.currentText(),
            resize_value=self.export_panel.resize_value.value(),
        )

        count = 0
        errors = 0
        for item in self.state.images:
            try:
                export_image(item.path, options, self.state.text_wm, self.state)
                count += 1
            except Exception as e:
                errors += 1
        if errors:
            self.statusBar().showMessage(f"已导出 {count} 张，失败 {errors} 张（查看日志或权限）", 6000)
        else:
            self.statusBar().showMessage(f"已导出 {count} 张图片到: {out_dir}", 4000)
        try:
            save_last(self.state, options)
        except Exception:
            pass

    # ----- helpers & callbacks -----
    def _on_files_dropped(self, paths: list[str]) -> None:
        self._add_paths(paths)

    def _add_paths(self, paths: list[str]) -> None:
        if not hasattr(self, "state"):
            self.state = ProjectState()
        added = 0
        for item in create_image_items(paths):
            if item.path in self.state.image_path_set:
                continue
            self.state.image_path_set.add(item.path)
            self.state.images.append(item)
            self.image_list.add_path_item(item.path)
            added += 1
        if added and self.image_list.count() == added:
            self.image_list.setCurrentRow(0)

    def _on_image_selected(self, row: int) -> None:
        if row < 0 or not hasattr(self, "state"):
            return
        try:
            path = self.state.images[row].path
            pixmap = QPixmap(path)
            self.preview_widget.set_pixmap(pixmap)
        except Exception:
            pass

    def _on_text_changed(self, text: str) -> None:
        self.preview_widget.set_watermark_text(text)
        if hasattr(self, "state"):
            self.state.text_wm.content = text

    def _on_opacity_changed(self, value: int) -> None:
        self.preview_widget.set_watermark_opacity(value / 100.0)
        if hasattr(self, "state"):
            self.state.text_wm.opacity = value

    def _on_grid_changed(self, idx: int) -> None:
        if not hasattr(self, "state"):
            return
        self.state.text_wm.position_mode = "grid"
        self.state.text_wm.grid_slot = idx
        self.preview_widget.set_watermark_grid_slot(idx)

    def _on_font_changed(self) -> None:
        if not hasattr(self, "state"):
            return
        family = self.text_panel.font_family.text().strip()
        size = self.text_panel.font_size.value()
        self.state.text_wm.font_family = family or None
        self.state.text_wm.font_size = size
        self.preview_widget.set_watermark_font(family, size, self.state.text_wm.bold, self.state.text_wm.italic)

    def _on_style_changed(self) -> None:
        if not hasattr(self, "state"):
            return
        self.state.text_wm.bold = self.text_panel.bold_cb.isChecked()
        self.state.text_wm.italic = self.text_panel.italic_cb.isChecked()
        self.state.text_wm.shadow = self.text_panel.shadow_cb.isChecked()
        self.state.text_wm.stroke = self.text_panel.stroke_cb.isChecked()
        self.state.text_wm.stroke_width = self.text_panel.stroke_w.value()
        self.preview_widget.set_watermark_font(self.text_panel.font_family.text().strip(), self.text_panel.font_size.value(), self.state.text_wm.bold, self.state.text_wm.italic)

    def _on_color_changed(self) -> None:
        if not hasattr(self, "state"):
            return
        # Pull color from dialog's current color stored on widget palette
        # Simpler: use a standard color dialog fetch
        from PySide6.QtWidgets import QColorDialog
        c = QColorDialog.getColor()
        if c.isValid():
            self.state.text_wm.color_rgba = (c.red(), c.green(), c.blue(), 255)
            self.preview_widget.set_watermark_color(c)

    def _on_rotation_changed(self, deg: int) -> None:
        if not hasattr(self, "state"):
            return
        self.state.text_wm.rotation = float(deg)
        self.preview_widget.set_watermark_rotation(float(deg))

    def _on_image_wm_changed(self) -> None:
        if not hasattr(self, "state"):
            return
        self.state.image_wm_enabled = self.image_panel.enable_cb.isChecked()
        btn_text = self.image_panel.choose_btn.text()
        self.state.image_wm_path = btn_text if btn_text and btn_text != "选择图片…" else None
        self.state.image_wm_scale = self.image_panel.scale_slider.value() / 100.0
        self.state.image_wm_opacity = self.image_panel.opacity_slider.value()
        self.state.image_wm_rotation = float(self.image_panel.rotation_slider.value())
        # grid index
        for i, btn in enumerate(self.image_panel.grid_buttons):
            if btn.isChecked():
                self.state.image_wm_grid_slot = i
                break

    # ----- templates -----
    def _on_template_save(self, name: str) -> None:
        if not hasattr(self, "state"):
            return
        if not name.strip():
            name = "template"
        opts = ExportOptions(
            output_dir="",
            format=self.export_panel.format_combo.currentText(),
            naming_mode=self.export_panel.naming_mode.currentText(),
            naming_value=self.export_panel.naming_value.text(),
            jpeg_quality=self.export_panel.jpeg_quality.value(),
            resize_mode=self.export_panel.resize_mode.currentText(),
            resize_value=self.export_panel.resize_value.value(),
        )
        save_named(name, self.state, opts)
        self._refresh_templates_list()
        self.statusBar().showMessage("模板已保存", 3000)

    def _on_template_load(self, name: str) -> None:
        try:
            p, e = load_last() if not name.strip() else self._load_named(name)
        except Exception:
            p, e = None, None
        if p is not None and e is not None:
            self.state = p
            # Reflect export options to panel
            self.export_panel.format_combo.setCurrentText(e.format)
            self.export_panel.naming_mode.setCurrentText(e.naming_mode)
            self.export_panel.naming_value.setText(e.naming_value)
            self.export_panel.jpeg_quality.setValue(e.jpeg_quality)
            self.export_panel.resize_mode.setCurrentText(e.resize_mode)
            self.export_panel.resize_value.setValue(e.resize_value)
            # Refresh list and preview
            self.image_list.clear()
            for it in self.state.images:
                self.image_list.add_path_item(it.path)
            if self.state.images:
                self.image_list.setCurrentRow(0)
            self.statusBar().showMessage("模板已加载", 3000)

    def _on_template_delete(self, name: str) -> None:
        if not name.strip():
            return
        delete_template(f"{name}.json" if not name.endswith(".json") else name)
        self._refresh_templates_list()
        self.statusBar().showMessage("模板已删除", 3000)

    def _load_named(self, name: str):
        from json import loads
        p = self._templates_dir() / (f"{name}.json" if not name.endswith(".json") else name)
        if not p.exists():
            return None, None
        from dataclasses import asdict
        data = loads(p.read_text(encoding="utf-8"))
        from ..core.models import ProjectState, ExportOptions
        try:
            return ProjectState(**data["project"]), ExportOptions(**data["export"])  # type: ignore[arg-type]
        except Exception:
            return None, None

    def _templates_dir(self):
        import os
        from pathlib import Path
        base = Path(os.getenv("APPDATA", str(Path.home() / "AppData" / "Roaming")))
        d = base / "PhotoWatermark2" / "templates"
        d.mkdir(parents=True, exist_ok=True)
        return d

    def _refresh_templates_list(self) -> None:
        try:
            items = list_templates()
            self.templates_panel.list_label.setText("\n".join(items))
        except Exception:
            self.templates_panel.list_label.setText("")

    # TODO: connect more advanced text and image controls to state and preview


