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
        self._wm_position_mode = "grid"
        self._wm_grid_slot = 8
        self._wm_color = QColor(255, 255, 255)
        self._wm_font_family = ""
        self._wm_font_size = 20
        self._wm_bold = False
        self._wm_italic = False
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

    def set_watermark_grid_slot(self, slot: int) -> None:
        self._wm_grid_slot = max(0, min(8, slot))
        self._wm_position_mode = "grid"
        self._wm_pos = None
        self.update()

    def set_watermark_font(self, family: str, size: int, bold: bool, italic: bool) -> None:
        self._wm_font_family = family or ""
        self._wm_font_size = size
        self._wm_bold = bold
        self._wm_italic = italic
        self.update()

    def set_watermark_color(self, color: QColor) -> None:
        self._wm_color = color
        self.update()

    def mousePressEvent(self, event) -> None:
        if event.button() == Qt.LeftButton:
            self._wm_pos = event.position().toPoint()
            self.update()
        super().mousePressEvent(event)

    def paintEvent(self, event) -> None:
        painter = QPainter(self)
        painter.fillRect(self.rect(), QColor(34, 34, 34))

        scaled = None
        if self._pixmap:
            # fit to widget while preserving aspect ratio
            scaled = self._pixmap.scaled(self.size(), Qt.KeepAspectRatio, Qt.SmoothTransformation)
            x = (self.width() - scaled.width()) // 2
            y = (self.height() - scaled.height()) // 2
            painter.drawPixmap(x, y, scaled)

        if self._wm_text:
            painter.setOpacity(self._wm_opacity)
            painter.setPen(self._wm_color)
            font = QFont(self._wm_font_family, self._wm_font_size)
            font.setBold(self._wm_bold)
            font.setItalic(self._wm_italic)
            painter.setFont(font)
            text_rect = painter.fontMetrics().boundingRect(self._wm_text)
            # position
            if self._wm_pos is not None:
                pos = self._wm_pos
            elif self._wm_position_mode == "grid" and scaled is not None:
                img_x = (self.width() - scaled.width()) // 2
                img_y = (self.height() - scaled.height()) // 2
                col = self._wm_grid_slot % 3
                row = self._wm_grid_slot // 3
                if col == 0:
                    px = img_x + 24 + text_rect.width() // 2
                elif col == 1:
                    px = img_x + scaled.width() // 2
                else:
                    px = img_x + scaled.width() - 24 - text_rect.width() // 2
                if row == 0:
                    py = img_y + 24 + text_rect.height() // 2
                elif row == 1:
                    py = img_y + scaled.height() // 2
                else:
                    py = img_y + scaled.height() - 24 - text_rect.height() // 2
                pos = QPoint(px, py)
            else:
                pos = QPoint(self.width()//2, self.height()//2)
            painter.save()
            painter.translate(pos)
            painter.rotate(self._wm_rotation)
            draw_x = - text_rect.width() // 2
            draw_y = + text_rect.height() // 2
            painter.drawText(draw_x, draw_y, self._wm_text)
            painter.restore()


