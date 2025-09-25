from __future__ import annotations

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import QWidget, QVBoxLayout, QLineEdit, QSlider, QLabel, QGridLayout, QPushButton, QComboBox, QHBoxLayout, QFileDialog, QColorDialog, QCheckBox, QSpinBox


class TextWatermarkPanel(QWidget):
    textChanged = Signal(str)
    opacityChanged = Signal(int)
    gridChanged = Signal(int)
    fontChanged = Signal()
    styleChanged = Signal()
    colorChanged = Signal()
    rotationChanged = Signal(int)

    def __init__(self) -> None:
        super().__init__()
        layout = QVBoxLayout(self)

        layout.addWidget(QLabel("文本内容"))
        self.text_input = QLineEdit("Watermark")
        self.text_input.textChanged.connect(self.textChanged)
        layout.addWidget(self.text_input)

        layout.addWidget(QLabel("透明度 (0-100)"))
        self.opacity_slider = QSlider(Qt.Horizontal)
        self.opacity_slider.setRange(0, 100)
        self.opacity_slider.setValue(50)
        self.opacity_slider.valueChanged.connect(self.opacityChanged)
        layout.addWidget(self.opacity_slider)

        layout.addWidget(QLabel("九宫格位置"))
        grid = QGridLayout()
        self.grid_buttons = []
        for i in range(3):
            for j in range(3):
                idx = i * 3 + j
                btn = QPushButton(str(idx + 1))
                btn.setCheckable(True)
                if idx == 8:
                    btn.setChecked(True)
                btn.clicked.connect(lambda checked, k=idx: self._on_grid_clicked(k))
                grid.addWidget(btn, i, j)
                self.grid_buttons.append(btn)
        layout.addLayout(grid)

        # Font family and size
        font_row = QHBoxLayout()
        self.font_family = QLineEdit(placeholderText="系统字体名，如 Segoe UI")
        self.font_size = QSpinBox()
        self.font_size.setRange(6, 300)
        self.font_size.setValue(36)
        self.bold_cb = QCheckBox("粗体")
        self.italic_cb = QCheckBox("斜体")
        for w in (QLabel("字体"), self.font_family, QLabel("字号"), self.font_size, self.bold_cb, self.italic_cb):
            font_row.addWidget(w)
        layout.addLayout(font_row)
        self.font_family.textChanged.connect(lambda _: self.fontChanged.emit())
        self.font_size.valueChanged.connect(lambda _: self.fontChanged.emit())
        self.bold_cb.toggled.connect(lambda _: self.styleChanged.emit())
        self.italic_cb.toggled.connect(lambda _: self.styleChanged.emit())

        # Color, shadow, stroke
        color_row = QHBoxLayout()
        self.color_btn = QPushButton("颜色")
        self.shadow_cb = QCheckBox("阴影")
        self.stroke_cb = QCheckBox("描边")
        self.stroke_w = QSpinBox()
        self.stroke_w.setRange(1, 20)
        self.stroke_w.setValue(2)
        for w in (self.color_btn, self.shadow_cb, self.stroke_cb, QLabel("描边宽度"), self.stroke_w):
            color_row.addWidget(w)
        layout.addLayout(color_row)
        self.color_btn.clicked.connect(self._choose_color)
        self.shadow_cb.toggled.connect(lambda _: self.styleChanged.emit())
        self.stroke_cb.toggled.connect(lambda _: self.styleChanged.emit())
        self.stroke_w.valueChanged.connect(lambda _: self.styleChanged.emit())

        # Rotation
        layout.addWidget(QLabel("旋转(度)"))
        self.rotation_slider = QSlider(Qt.Horizontal)
        self.rotation_slider.setRange(-180, 180)
        self.rotation_slider.setValue(0)
        self.rotation_slider.valueChanged.connect(self.rotationChanged)
        layout.addWidget(self.rotation_slider)

    def _choose_color(self) -> None:
        c = QColorDialog.getColor()
        if c.isValid():
            self.colorChanged.emit()

    def _on_grid_clicked(self, idx: int) -> None:
        # Ensure only one is checked and emit selected index
        if hasattr(self, "grid_buttons"):
            for i, btn in enumerate(self.grid_buttons):
                btn.setChecked(i == idx)
        self.gridChanged.emit(idx)


class ImageWatermarkPanel(QWidget):
    changed = Signal()

    def __init__(self) -> None:
        super().__init__()
        layout = QVBoxLayout(self)
        self.enable_cb = QCheckBox("启用图片水印")
        layout.addWidget(self.enable_cb)
        self.choose_btn = QPushButton("选择图片…")
        layout.addWidget(self.choose_btn)
        self.scale_slider = QSlider(Qt.Horizontal)
        self.scale_slider.setRange(1, 400)
        self.scale_slider.setValue(30)
        layout.addWidget(QLabel("缩放(%)"))
        layout.addWidget(self.scale_slider)
        self.opacity_slider = QSlider(Qt.Horizontal)
        self.opacity_slider.setRange(0, 100)
        self.opacity_slider.setValue(50)
        layout.addWidget(QLabel("透明度(0-100)"))
        layout.addWidget(self.opacity_slider)
        self.rotation_slider = QSlider(Qt.Horizontal)
        self.rotation_slider.setRange(-180, 180)
        self.rotation_slider.setValue(0)
        layout.addWidget(QLabel("旋转(度)"))
        layout.addWidget(self.rotation_slider)

        grid = QGridLayout()
        self.grid_buttons = []
        for i in range(3):
            for j in range(3):
                idx = i * 3 + j
                btn = QPushButton(str(idx + 1))
                btn.setCheckable(True)
                if idx == 8:
                    btn.setChecked(True)
                btn.clicked.connect(lambda checked, k=idx: self._on_grid_clicked(k))
                grid.addWidget(btn, i, j)
                self.grid_buttons.append(btn)
        layout.addWidget(QLabel("九宫格位置"))
        layout.addLayout(grid)

        self.enable_cb.toggled.connect(lambda _: self.changed.emit())
        self.choose_btn.clicked.connect(self._choose_image)
        self.scale_slider.valueChanged.connect(lambda _: self.changed.emit())
        self.opacity_slider.valueChanged.connect(lambda _: self.changed.emit())
        self.rotation_slider.valueChanged.connect(lambda _: self.changed.emit())

    def _on_grid_clicked(self, idx: int) -> None:
        for i, btn in enumerate(self.grid_buttons):
            btn.setChecked(i == idx)
        self.changed.emit()

    def _choose_image(self) -> None:
        path, _ = QFileDialog.getOpenFileName(self, "选择图片水印", "", "Images (*.png *.jpg *.jpeg *.bmp *.tif *.tiff)")
        if path:
            self.choose_btn.setText(path)
            self.changed.emit()


class TemplatesPanel(QWidget):
    saveRequested = Signal(str)
    loadRequested = Signal(str)
    deleteRequested = Signal(str)

    def __init__(self) -> None:
        super().__init__()
        layout = QVBoxLayout(self)
        layout.addWidget(QLabel("模板名称"))
        self.name_edit = QLineEdit()
        layout.addWidget(self.name_edit)
        row = QHBoxLayout()
        self.save_btn = QPushButton("保存模板")
        self.load_btn = QPushButton("加载模板")
        self.delete_btn = QPushButton("删除模板")
        row.addWidget(self.save_btn)
        row.addWidget(self.load_btn)
        row.addWidget(self.delete_btn)
        layout.addLayout(row)
        self.list_label = QLabel("")
        layout.addWidget(self.list_label)
        self.save_btn.clicked.connect(lambda: self.saveRequested.emit(self.name_edit.text()))
        self.load_btn.clicked.connect(lambda: self.loadRequested.emit(self.name_edit.text()))
        self.delete_btn.clicked.connect(lambda: self.deleteRequested.emit(self.name_edit.text()))

    def _on_grid_clicked(self, idx: int) -> None:
        for i, btn in enumerate(self.grid_buttons):
            btn.setChecked(i == idx)
        self.gridChanged.emit(idx)


class ExportPanel(QWidget):
    optionsChanged = Signal()

    def __init__(self) -> None:
        super().__init__()
        layout = QVBoxLayout(self)

        layout.addWidget(QLabel("输出格式"))
        self.format_combo = QComboBox()
        self.format_combo.addItems(["png", "jpeg"])
        layout.addWidget(self.format_combo)

        layout.addWidget(QLabel("命名模式"))
        self.naming_mode = QComboBox()
        self.naming_mode.addItems(["keep", "prefix", "suffix"])
        layout.addWidget(self.naming_mode)

        layout.addWidget(QLabel("命名值(前缀/后缀)"))
        self.naming_value = QLineEdit("_watermarked")
        layout.addWidget(self.naming_value)

        layout.addWidget(QLabel("JPEG 质量 (仅JPEG)"))
        self.jpeg_quality = QSlider(Qt.Horizontal)
        self.jpeg_quality.setRange(1, 100)
        self.jpeg_quality.setValue(90)
        layout.addWidget(self.jpeg_quality)

        layout.addWidget(QLabel("尺寸缩放"))
        self.resize_mode = QComboBox()
        self.resize_mode.addItems(["none", "width", "height", "percent"])
        layout.addWidget(self.resize_mode)
        self.resize_value = QSpinBox()
        self.resize_value.setRange(1, 10000)
        self.resize_value.setValue(100)
        layout.addWidget(self.resize_value)



