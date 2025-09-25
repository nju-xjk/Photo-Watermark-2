import sys
from PySide6.QtWidgets import QApplication
from .ui.main_window import MainWindow
from .core.templates import load_last


def main() -> None:
    app = QApplication(sys.argv)
    window = MainWindow()
    # auto load last settings if available
    try:
        p, e = load_last()
        if p is not None and e is not None:
            window.state = p
            # reflect minimal UI (image list)
            window.image_list.clear()
            for it in window.state.images:
                window.image_list.add_path_item(it.path)
            if window.state.images:
                window.image_list.setCurrentRow(0)
    except Exception:
        pass
    window.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()

