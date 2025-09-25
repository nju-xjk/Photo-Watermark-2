from __future__ import annotations

from pathlib import Path
from typing import List

from PySide6.QtCore import Qt, QMimeData, QUrl, Signal
from PySide6.QtGui import QDragEnterEvent, QDropEvent, QPixmap, QIcon
from PySide6.QtWidgets import QListWidget, QListWidgetItem
from PySide6.QtGui import QIcon, QPixmap


class ImageListWidget(QListWidget):
    fileDropped = Signal(list)

    def __init__(self) -> None:
        super().__init__()
        self.setAcceptDrops(True)
        self.setSelectionMode(QListWidget.SingleSelection)

    def dragEnterEvent(self, event: QDragEnterEvent) -> None:
        if event.mimeData().hasUrls():
            event.acceptProposedAction()
        else:
            super().dragEnterEvent(event)

    def dropEvent(self, event: QDropEvent) -> None:
        paths: List[str] = []
        for url in event.mimeData().urls():
            p = url.toLocalFile()
            if p:
                paths.append(p)
        if paths:
            self.fileDropped.emit(paths)
        super().dropEvent(event)

    def add_path_item(self, path: str) -> None:
        item = QListWidgetItem(Path(path).name)
        item.setToolTip(path)
        # try thumbnail icon
        try:
            pix = QPixmap(path)
            if not pix.isNull():
                icon = QIcon(pix.scaled(64, 64, Qt.KeepAspectRatio, Qt.SmoothTransformation))
                item.setIcon(icon)
        except Exception:
            pass
        self.addItem(item)


