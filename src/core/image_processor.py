from PIL import Image, ImageDraw, ImageFont
import os

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
        
        font = self._load_font_with_fallbacks(watermark)

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
            "bottom-left": (margin, img_h - txt_h - margin - 20),
            "bottom-center": ((img_w - txt_w) // 2, img_h - txt_h - margin - 20),
            "bottom-right": (img_w - txt_w - margin, img_h - txt_h - margin - 20)
        }

        if mode == "manual":
            # For manual mode, use the offset directly as the position
            # The offset already contains the actual position relative to the image
            return (offset["x"], offset["y"])
        
        if mode == "relative":
            # Interpret offset as relative fractions (0..1) of available drawing area
            try:
                rel_x = float(offset.get("x", 0))
                rel_y = float(offset.get("y", 0))
            except Exception:
                rel_x, rel_y = 0.5, 0.5
            rel_x = max(0.0, min(1.0, rel_x))
            rel_y = max(0.0, min(1.0, rel_y))
            x_min = margin
            x_max = img_w - txt_w - margin
            y_min = margin
            y_max = img_h - txt_h - margin - 20
            x_range = max(0, x_max - x_min)
            y_range = max(0, y_max - y_min)
            x = x_min + int(round(rel_x * x_range))
            y = y_min + int(round(rel_y * y_range))
            return (x, y)
        
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

    def _load_font_with_fallbacks(self, watermark):
        """Loads a truetype font with sensible fallbacks that support CJK (Chinese) characters on Windows."""
        # 1) Explicit path on the watermark, if provided and exists
        if getattr(watermark, 'font_path', None):
            try:
                if watermark.font_path and os.path.exists(watermark.font_path):
                    return ImageFont.truetype(watermark.font_path, watermark.font_size)
            except Exception:
                pass

        # 2) Try common CJK fonts on Windows first (to avoid garbled Chinese)
        windows_fonts_dir = os.path.join(os.environ.get('WINDIR', r'C:\Windows'), 'Fonts')
        cjk_candidates = [
            'msyh.ttc',            # Microsoft YaHei (collection)
            'MSYH.TTC',
            'msyh.ttf',            # Sometimes shipped as ttf
            'MicrosoftYaHei.ttf',
            'simhei.ttf',          # SimHei
            'SIMHEI.TTF',
            'simsun.ttc',          # SimSun (collection)
            'SIMSUN.TTC',
            'Deng.ttf',            # DengXian
            'DENG.TTF',
            'NotoSansCJK-Regular.ttc', # Noto CJK
        ]
        for fname in cjk_candidates:
            candidate_path = os.path.join(windows_fonts_dir, fname)
            try:
                if os.path.exists(candidate_path):
                    return ImageFont.truetype(candidate_path, watermark.font_size)
            except Exception:
                continue

        # 3) Try common Western font
        try:
            return ImageFont.truetype("arial.ttf", watermark.font_size)
        except Exception:
            pass

        # 4) Final fallback – PIL default (may not support all glyphs)
        print("Warning: No CJK-capable font found. Falling back to PIL default font; Chinese characters may not render correctly.")
        return ImageFont.load_default()