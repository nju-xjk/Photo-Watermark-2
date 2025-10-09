import tkinter as tk
from ui.main_window import MainWindow

def main():
    """Main function to run the application."""
    root = tk.Tk()
    main_window = MainWindow(root)
    main_window.run()

if __name__ == "__main__":
    main()