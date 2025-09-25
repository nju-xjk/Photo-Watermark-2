from __future__ import annotations

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import QWidget, QVBoxLayout, QLineEdit, QSlider, QLabel, QGridLayout, QPushButton, QComboBox, QHBoxLayout


class TextWatermarkPanel(QWidget):
    textChanged = Signal(str)
    opacityChanged = Signal(int)
    gridChanged = Signal(int)

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



