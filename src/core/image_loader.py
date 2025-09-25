from __future__ import annotations

import os
from pathlib import Path
from typing import Iterable, List

from PIL import Image

from .models import SUPPORTED_INPUT_EXTS, ImageItem


def is_supported_image(path: str) -> bool:
    ext = Path(path).suffix.lower()
    return ext in SUPPORTED_INPUT_EXTS


def scan_directory_for_images(directory: str) -> List[str]:
    results: List[str] = []
    for root, _, files in os.walk(directory):
        for name in files:
            p = str(Path(root) / name)
            if is_supported_image(p):
                results.append(p)
    return results


def load_thumbnail_key(path: str) -> str:
    # We will use a simple key (path) for now; a cache layer can be added later
    return path


def create_image_items(paths: Iterable[str]) -> List[ImageItem]:
    items: List[ImageItem] = []
    for p in paths:
        if not is_supported_image(p):
            continue
        items.append(ImageItem(path=p, thumbnail_key=load_thumbnail_key(p)))
    return items


