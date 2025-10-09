from ui.main_window import MainWindow

def main():
    """Main function to run the application."""
    # For now, we will just instantiate the classes to show the structure.
    print("Application starting...")
    main_window = MainWindow()
    main_window.run()
    print("Application finished.")

if __name__ == "__main__":
    main()