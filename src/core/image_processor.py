from PIL import Image, ImageDraw, ImageFont

class ImageProcessor:
    """Handles image loading, processing, and saving."""

    def __init__(self):
        pass

    def load_image(self, path):
        """Loads an image from the given path."""
        # Placeholder for loading image
        print(f"Loading image from {path}")
        return None

    def apply_watermark(self, image, watermark):
        """Applies a watermark to the given image."""
        # Placeholder for applying watermark
        print(f"Applying watermark '{watermark.text}' to image")
        return image

    def save_image(self, image, path, format, quality=95):
        """Saves the image to the given path."""
        # Placeholder for saving image
        print(f"Saving image to {path} in {format} format with quality {quality}")