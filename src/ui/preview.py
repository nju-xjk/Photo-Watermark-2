from __future__ import annotations

from typing import Optional

from PySide6.QtCore import Qt, QPoint, QRect
from PySide6.QtGui import QPainter, QColor, QFont, QPixmap
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
        # image watermark
        self._imgwm_enabled = False
        self._imgwm_path: Optional[str] = None
        self._imgwm_scale = 0.3  # relative to drawn image width
        self._imgwm_opacity = 0.5
        self._imgwm_rotation = 0.0
        self._imgwm_grid_slot = 8
        self._imgwm_pixmap: Optional[QPixmap] = None
        # dragging
        self._dragging = False
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

    # image watermark setters
    def set_image_watermark(
        self,
        enabled: bool,
        path: Optional[str],
        scale: float,
        opacity01: float,
        rotation: float,
        grid_slot: int,
    ) -> None:
        self._imgwm_enabled = enabled
        self._imgwm_path = path
        self._imgwm_scale = max(0.01, min(5.0, scale))
        self._imgwm_opacity = max(0.0, min(1.0, opacity01))
        self._imgwm_rotation = rotation
        self._imgwm_grid_slot = max(0, min(8, grid_slot))
        if path:
            try:
                self._imgwm_pixmap = QPixmap(path)
            except Exception:
                self._imgwm_pixmap = None
        else:
            self._imgwm_pixmap = None
        self.update()

    def mousePressEvent(self, event) -> None:
        if event.button() == Qt.LeftButton:
            self._dragging = True
            self._wm_pos = event.position().toPoint()
            self.update()
        super().mousePressEvent(event)

    def mouseMoveEvent(self, event) -> None:
        if self._dragging and (event.buttons() & Qt.LeftButton):
            self._wm_pos = event.position().toPoint()
            self.update()
        super().mouseMoveEvent(event)

    def mouseReleaseEvent(self, event) -> None:
        if event.button() == Qt.LeftButton:
            self._dragging = False
        super().mouseReleaseEvent(event)

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

        # draw image watermark in preview
        if self._imgwm_enabled and self._imgwm_pixmap is not None and scaled is not None:
            # placement within image area using grid
            img_x = (self.width() - scaled.width()) // 2
            img_y = (self.height() - scaled.height()) // 2
            target_w = max(1, int(scaled.width() * self._imgwm_scale))
            wm_scaled = self._imgwm_pixmap.scaledToWidth(target_w, Qt.SmoothTransformation)
            wm_w = wm_scaled.width()
            wm_h = wm_scaled.height()
            col = self._imgwm_grid_slot % 3
            row = self._imgwm_grid_slot // 3
            if col == 0:
                px = img_x + 24 + wm_w // 2
            elif col == 1:
                px = img_x + scaled.width() // 2
            else:
                px = img_x + scaled.width() - 24 - wm_w // 2
            if row == 0:
                py = img_y + 24 + wm_h // 2
            elif row == 1:
                py = img_y + scaled.height() // 2
            else:
                py = img_y + scaled.height() - 24 - wm_h // 2
            center = QPoint(px, py)

            painter.save()
            painter.setOpacity(self._imgwm_opacity)
            painter.translate(center)
            painter.rotate(self._imgwm_rotation)
            painter.drawPixmap(-wm_w // 2, -wm_h // 2, wm_scaled)
            painter.restore()


