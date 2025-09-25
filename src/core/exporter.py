from __future__ import annotations

import os
from pathlib import Path
from typing import Tuple

from PIL import Image, ImageDraw, ImageFont

from .models import ExportOptions, TextWatermarkConfig


def _calc_grid_position(img_w: int, img_h: int, text_w: int, text_h: int, slot: int, margin: int = 24) -> Tuple[int, int]:
    col = slot % 3
    row = slot // 3
    x = {0: margin, 1: (img_w - text_w) // 2, 2: img_w - text_w - margin}[col]
    y = {0: margin + text_h, 1: (img_h + text_h) // 2, 2: img_h - margin}[row]
    return x, y


def _overlay_text(img: Image.Image, cfg: TextWatermarkConfig) -> Image.Image:
    if not cfg.enabled or not cfg.content:
        return img
    base = img.convert("RGBA")
    overlay = Image.new("RGBA", base.size, (0, 0, 0, 0))
    draw = ImageDraw.Draw(overlay)

    # Basic font; advanced font options will be added later
    try:
        font = ImageFont.truetype("segoeui.ttf", 36)
    except Exception:
        font = ImageFont.load_default()

    text_w, text_h = draw.textsize(cfg.content, font=font)

    if cfg.position_mode == "grid":
        x, y = _calc_grid_position(base.width, base.height, text_w, text_h, cfg.grid_slot)
    else:
        cx = int((cfg.rel_x if cfg.rel_x is not None else 0.5) * base.width)
        cy = int((cfg.rel_y if cfg.rel_y is not None else 0.5) * base.height)
        x = cx - text_w // 2
        y = cy + text_h // 2

    alpha = max(0, min(100, cfg.opacity))
    fill = (255, 255, 255, int(255 * alpha / 100))
    draw.text((x, y - text_h), cfg.content, font=font, fill=fill)
    return Image.alpha_composite(base, overlay)


def export_image(src_path: str, options: ExportOptions, text_cfg: TextWatermarkConfig) -> str:
    img = Image.open(src_path)
    result = _overlay_text(img, text_cfg)

    out_dir = Path(options.output_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    src = Path(src_path)
    stem = src.stem
    if options.naming_mode == "prefix":
        stem = f"{options.naming_value}{stem}"
    elif options.naming_mode == "suffix":
        stem = f"{stem}{options.naming_value}"

    if options.format == "jpeg":
        out_path = out_dir / f"{stem}.jpg"
        rgb = result.convert("RGB")
        rgb.save(out_path, format="JPEG", quality=options.jpeg_quality)
    else:
        out_path = out_dir / f"{stem}.png"
        result.save(out_path, format="PNG")

    return str(out_path)


