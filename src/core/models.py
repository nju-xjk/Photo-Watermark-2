from __future__ import annotations

from dataclasses import dataclass, field
from typing import List, Optional, Literal


SUPPORTED_INPUT_EXTS = {".jpg", ".jpeg", ".png", ".bmp", ".tif", ".tiff"}


@dataclass
class TextWatermarkConfig:
    enabled: bool = True
    content: str = "Watermark"
    opacity: int = 50  # 0-100
    position_mode: Literal["grid", "free"] = "grid"
    grid_slot: int = 8  # default bottom-right (0..8, row-major)
    # free position as relative coords in image rect (0..1). None means center
    rel_x: Optional[float] = None
    rel_y: Optional[float] = None


@dataclass
class ImageItem:
    path: str
    thumbnail_key: Optional[str] = None


@dataclass
class ProjectState:
    images: List[ImageItem] = field(default_factory=list)
    image_path_set: set[str] = field(default_factory=set)
    text_wm: TextWatermarkConfig = field(default_factory=TextWatermarkConfig)


@dataclass
class ExportOptions:
    output_dir: str = ""
    format: Literal["jpeg", "png"] = "png"
    naming_mode: Literal["keep", "prefix", "suffix"] = "suffix"
    naming_value: str = "_watermarked"
    jpeg_quality: int = 90



