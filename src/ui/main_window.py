from core.image_processor import ImageProcessor
from core.config_manager import ConfigManager
from core.watermark import Watermark

class MainWindow:
    """The main window of the application."""

    def __init__(self):
        self.image_processor = ImageProcessor()
        self.config_manager = ConfigManager()

    def run(self):
        """Runs the main application loop."""
        # Placeholder for the main UI loop
        print("Main window is running...")
        # Simulate loading an image and applying a watermark
        image = self.image_processor.load_image("path/to/image.jpg")
        watermark = Watermark("Hello World", (10, 10), 0.5)
        watermarked_image = self.image_processor.apply_watermark(image, watermark)
        self.image_processor.save_image(watermarked_image, "path/to/output.jpg", "JPEG")