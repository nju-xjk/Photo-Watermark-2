from PIL import Image, ImageDraw, ImageFont

class ImageProcessor:
    """Handles image loading, processing, and saving."""

    def __init__(self):
        pass

    def load_image(self, path):
        """Loads an image from the given path."""
        try:
            return Image.open(path)
        except IOError:
            print(f"Error: Unable to load image at {path}")
            return None

    def create_thumbnail(self, img, size):
        """Creates a thumbnail of the given image."""
        img.thumbnail(size)
        return img

    def resize_to_fit(self, img, box_size):
        """
        Resizes an image to fit within a given box size, maintaining aspect ratio.
        The image is not enlarged if it's smaller than the box.
        """
        box_width, box_height = box_size
        img_width, img_height = img.size

        if img_width <= box_width and img_height <= box_height:
            return img

        w_ratio = box_width / img_width
        h_ratio = box_height / img_height
        scale_factor = min(w_ratio, h_ratio)

        new_width = int(img_width * scale_factor)
        new_height = int(img_height * scale_factor)

        return img.resize((new_width, new_height), Image.Resampling.LANCZOS)

    def apply_watermark(self, image, watermark):
        """Applies a text watermark to the image."""
        if image.mode != 'RGBA':
            image = image.convert('RGBA')
        
        txt_layer = Image.new('RGBA', image.size, (255, 255, 255, 0))
        draw = ImageDraw.Draw(txt_layer)
        
        try:
            font = ImageFont.truetype(watermark.font_path, watermark.font_size)
        except (IOError, FileNotFoundError, AttributeError):
            try:
                font = ImageFont.truetype("arial.ttf", watermark.font_size)
            except (IOError, FileNotFoundError):
                print("Arial font not found. Using default font.")
                font = ImageFont.load_default()

        text_bbox = draw.textbbox((0, 0), watermark.text, font=font)
        text_width = text_bbox[2] - text_bbox[0]
        text_height = text_bbox[3] - text_bbox[1]

        position = self.calculate_position(image.size, (text_width, text_height), watermark.position)

        draw.text(position, watermark.text, font=font, fill=watermark.color)
        return Image.alpha_composite(image, txt_layer)

    def calculate_position(self, image_size, text_size, position_data, margin=10):
        """Calculates the (x, y) coordinates for the watermark."""
        mode, offset = position_data if isinstance(position_data, tuple) else (position_data, {"x": 0, "y": 0})

        img_w, img_h = image_size
        txt_w, txt_h = text_size

        base_positions = {
            "top-left": (margin, margin),
            "top-center": ((img_w - txt_w) // 2, margin),
            "top-right": (img_w - txt_w - margin, margin),
            "mid-left": (margin, (img_h - txt_h) // 2),
            "mid-center": ((img_w - txt_w) // 2, (img_h - txt_h) // 2),
            "mid-right": (img_w - txt_w - margin, (img_h - txt_h) // 2),
            "bottom-left": (margin, img_h - txt_h - margin),
            "bottom-center": ((img_w - txt_w) // 2, img_h - txt_h - margin),
            "bottom-right": (img_w - txt_w - margin, img_h - txt_h - margin)
        }

        if mode == "manual":
            # Start from center and apply offset
            base_x = (img_w - txt_w) // 2
            base_y = (img_h - txt_h) // 2
            return (base_x + offset["x"], base_y + offset["y"])
        
        base_pos = base_positions.get(mode, base_positions["bottom-right"])
        return (base_pos[0] + offset["x"], base_pos[1] + offset["y"])

    def save_image(self, image, path, format='JPEG', quality=95):
        """Saves the image to the given path."""
        try:
            # When saving as JPEG, we need to convert from RGBA to RGB
            if format.upper() == 'JPEG' and image.mode == 'RGBA':
                # Create a white background image
                background = Image.new('RGB', image.size, (255, 255, 255))
                # Paste the RGBA image onto the background, using the alpha channel as a mask
                background.paste(image, (0, 0), image)
                img_to_save = background
            else:
                img_to_save = image

            if format.upper() == 'JPEG':
                img_to_save.save(path, format=format, quality=quality)
            else:
                img_to_save.save(path, format=format)
        except Exception as e:
            print(f"Error saving image {path}: {e}")