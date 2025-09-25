from __future__ import annotations

from typing import Optional

from PySide6.QtCore import Qt, QPoint, QRect
from PySide6.QtGui import QPainter, QColor, QFont
from PySide6.QtWidgets import QWidget


class PreviewWidget(QWidget):
    def __init__(self) -> None:
        super().__init__()
        self._pixmap = None
        self._wm_text = "Watermark"
        self._wm_opacity = 0.5
        self._wm_rotation = 0.0
        self._wm_pos = None  # type: Optional[QPoint]
        self.setMinimumSize(200, 200)
        self.setMouseTracking(True)

    def set_pixmap(self, pixmap) -> None:
        self._pixmap = pixmap
        self.update()

    def set_watermark_text(self, text: str) -> None:
        self._wm_text = text
        self.update()

    def set_watermark_opacity(self, opacity01: float) -> None:
        self._wm_opacity = max(0.0, min(1.0, opacity01))
        self.update()

    def set_watermark_rotation(self, degrees: float) -> None:
        self._wm_rotation = degrees
        self.update()

    def mousePressEvent(self, event) -> None:
        if event.button() == Qt.LeftButton:
            self._wm_pos = event.position().toPoint()
            self.update()
        super().mousePressEvent(event)

    def paintEvent(self, event) -> None:
        painter = QPainter(self)
        painter.fillRect(self.rect(), QColor(34, 34, 34))

        if self._pixmap:
            # fit to widget while preserving aspect ratio
            scaled = self._pixmap.scaled(self.size(), Qt.KeepAspectRatio, Qt.SmoothTransformation)
            x = (self.width() - scaled.width()) // 2
            y = (self.height() - scaled.height()) // 2
            painter.drawPixmap(x, y, scaled)

        if self._wm_text:
            painter.setOpacity(self._wm_opacity)
            painter.setPen(QColor(255, 255, 255))
            font = QFont()
            font.setPointSize(20)
            painter.setFont(font)
            text_rect = painter.fontMetrics().boundingRect(self._wm_text)

            pos = self._wm_pos or QPoint(self.width()//2, self.height()//2)
            painter.save()
            painter.translate(pos)
            painter.rotate(self._wm_rotation)
            draw_x = - text_rect.width() // 2
            draw_y = + text_rect.height() // 2
            painter.drawText(draw_x, draw_y, self._wm_text)
            painter.restore()


