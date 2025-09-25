from __future__ import annotations

from dataclasses import dataclass, field
from typing import List, Optional


SUPPORTED_INPUT_EXTS = {".jpg", ".jpeg", ".png", ".bmp", ".tif", ".tiff"}


@dataclass
class TextWatermarkConfig:
    enabled: bool = True
    content: str = "Watermark"
    opacity: int = 50  # 0-100


@dataclass
class ImageItem:
    path: str
    thumbnail_key: Optional[str] = None


@dataclass
class ProjectState:
    images: List[ImageItem] = field(default_factory=list)
    image_path_set: set[str] = field(default_factory=set)
    text_wm: TextWatermarkConfig = field(default_factory=TextWatermarkConfig)


