import tkinter as tk
from tkinterdnd2 import TkinterDnD
from ui.main_window import MainWindow

def main():
    """Main function to run the application."""
    root = TkinterDnD.Tk()
    main_window = MainWindow(root)
    # Start in fullscreen (maximized) on Windows
    root.state('zoomed')
    main_window.run()

if __name__ == "__main__":
    main()