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
        self.image_list = QListWidget()
        left_layout.addWidget(QLabel("已导入图片"))
        left_layout.addWidget(self.image_list)

        # Center: preview placeholder
        center_panel = QWidget()
        center_layout = QVBoxLayout(center_panel)
        self.preview_label = QLabel("预览区")
        self.preview_label.setAlignment(Qt.AlignCenter)
        self.preview_label.setStyleSheet("background: #222; color: #bbb;")
        center_layout.addWidget(self.preview_label)

        # Right: properties tabs
        right_panel = QWidget()
        right_layout = QVBoxLayout(right_panel)
        tabs = QTabWidget()
        tabs.addTab(QWidget(), "文本水印")
        tabs.addTab(QWidget(), "图片水印")
        tabs.addTab(QWidget(), "导出设置")
        tabs.addTab(QWidget(), "模板")
        right_layout.addWidget(tabs)

        root_layout.addWidget(left_panel, 2)
        root_layout.addWidget(center_panel, 5)
        root_layout.addWidget(right_panel, 3)

    def _on_import_files(self) -> None:
        files, _ = QFileDialog.getOpenFileNames(self, "选择图片", "", "Images (*.png *.jpg *.jpeg *.bmp *.tif *.tiff)")
        if not files:
            return
        for path in files:
            self.image_list.addItem(path)
        self.statusBar().showMessage(f"已导入 {len(files)} 张图片", 3000)

    def _on_import_dir(self) -> None:
        directory = QFileDialog.getExistingDirectory(self, "选择文件夹")
        if not directory:
            return
        # 递归扫描将稍后实现
        self.statusBar().showMessage(f"已选择文件夹: {directory}", 3000)

    def _on_export(self) -> None:
        out_dir = QFileDialog.getExistingDirectory(self, "选择输出文件夹")
        if not out_dir:
            return
        self.statusBar().showMessage(f"输出到: {out_dir}", 3000)


