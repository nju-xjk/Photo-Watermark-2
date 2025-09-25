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
from .panels import TextWatermarkPanel, ExportPanel, ImageWatermarkPanel
from ..core.models import ExportOptions
from ..core.exporter import export_image


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
        tabs.addTab(self.text_panel, "文本水印")
        self.image_panel = ImageWatermarkPanel()
        tabs.addTab(self.image_panel, "图片水印")
        self.export_panel = ExportPanel()
        tabs.addTab(self.export_panel, "导出设置")
        tabs.addTab(QWidget(), "模板")
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
        )

        count = 0
        for item in self.state.images:
            try:
                export_image(item.path, options, self.state.text_wm, self.state)
                count += 1
            except Exception:
                pass
        self.statusBar().showMessage(f"已导出 {count} 张图片到: {out_dir}", 4000)

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

    # TODO: connect more advanced text and image controls to state and preview


