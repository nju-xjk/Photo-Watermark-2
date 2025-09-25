from __future__ import annotations

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import QWidget, QVBoxLayout, QLineEdit, QSlider, QLabel


class TextWatermarkPanel(QWidget):
    textChanged = Signal(str)
    opacityChanged = Signal(int)

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


