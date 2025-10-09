class Watermark:
    """Represents a watermark with its properties."""

    def __init__(self, text, font_size=40, color=(255, 255, 255, 128), position="bottom-right"):
        self.text = text
        self.font_size = font_size
        self.color = color  # RGBA tuple
        self.position = position