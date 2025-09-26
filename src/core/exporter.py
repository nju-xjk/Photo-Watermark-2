from __future__ import annotations

import os
from pathlib import Path
from typing import Tuple

from PIL import Image, ImageDraw, ImageFont

from .models import ExportOptions, TextWatermarkConfig, ProjectState


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
    # font selection
    font: ImageFont.FreeTypeFont | ImageFont.ImageFont
    ttf_name = cfg.font_family or "segoeui.ttf"
    try:
        font = ImageFont.truetype(ttf_name, cfg.font_size)
    except Exception:
        try:
            font = ImageFont.truetype("arial.ttf", cfg.font_size)
        except Exception:
            font = ImageFont.load_default()

    # compute text bounding box (Pillow 10+)
    stroke_w = cfg.stroke_width if getattr(cfg, "stroke", False) else 0
    bbox = draw.textbbox((0, 0), cfg.content, font=font, stroke_width=stroke_w)
    text_w = bbox[2] - bbox[0]
    text_h = bbox[3] - bbox[1]

    if cfg.position_mode == "grid":
        x, y = _calc_grid_position(base.width, base.height, text_w, text_h, cfg.grid_slot)
    else:
        cx = int((cfg.rel_x if cfg.rel_x is not None else 0.5) * base.width)
        cy = int((cfg.rel_y if cfg.rel_y is not None else 0.5) * base.height)
        x = cx - text_w // 2
        y = cy + text_h // 2

    alpha = max(0, min(100, cfg.opacity))
    r, g, b, a = cfg.color_rgba
    fill = (r, g, b, int(a * alpha / 100))

    # rotation: draw rotated text onto its own layer to rotate accurately
    text_layer = Image.new("RGBA", (text_w + 8, text_h + 8), (0, 0, 0, 0))
    text_draw = ImageDraw.Draw(text_layer)

    # draw order: shadow -> stroke -> fill
    if cfg.shadow:
        sh = cfg.shadow_color_rgba
        text_draw.text((6, 6), cfg.content, font=font, fill=sh)
    if cfg.stroke and cfg.stroke_width > 0:
        sc = cfg.stroke_color_rgba
        text_draw.text((4, 4), cfg.content, font=font, fill=fill, stroke_width=cfg.stroke_width, stroke_fill=sc)
    else:
        text_draw.text((4, 4), cfg.content, font=font, fill=fill)
    if cfg.rotation:
        text_layer = text_layer.rotate(cfg.rotation, expand=True, resample=Image.BICUBIC)

    base_pos = (x - 4, y - text_h - 4)
    overlay.alpha_composite(text_layer, base_pos)
    return Image.alpha_composite(base, overlay)


def _calc_grid_position_box(img_w: int, img_h: int, box_w: int, box_h: int, slot: int, margin: int = 24) -> Tuple[int, int]:
    col = slot % 3
    row = slot // 3
    x = {0: margin, 1: (img_w - box_w) // 2, 2: img_w - box_w - margin}[col]
    y = {0: margin, 1: (img_h - box_h) // 2, 2: img_h - box_h - margin}[row]
    return x, y


def _overlay_image_watermark(base: Image.Image, state: ProjectState) -> Image.Image:
    if not state.image_wm_enabled or not state.image_wm_path:
        return base
    try:
        wm = Image.open(state.image_wm_path).convert("RGBA")
    except Exception:
        return base

    # scale
    scale = max(0.01, state.image_wm_scale)
    new_w = int(base.width * scale)
    new_h = int(wm.height * (new_w / wm.width))
    wm = wm.resize((new_w, new_h), Image.LANCZOS)

    # rotation
    if state.image_wm_rotation:
        wm = wm.rotate(state.image_wm_rotation, expand=True, resample=Image.BICUBIC)

    # opacity
    if state.image_wm_opacity < 100:
        alpha = wm.split()[-1]
        alpha = alpha.point(lambda p: p * state.image_wm_opacity / 100)
        wm.putalpha(alpha)

    x, y = _calc_grid_position_box(base.width, base.height, wm.width, wm.height, state.image_wm_grid_slot)
    out = Image.new("RGBA", base.size, (0, 0, 0, 0))
    out.alpha_composite(base.convert("RGBA"))
    out.alpha_composite(wm, (x, y))
    return out


def export_image(src_path: str, options: ExportOptions, text_cfg: TextWatermarkConfig, state: ProjectState | None = None) -> str:
    img = Image.open(src_path)
    # optional resizing on load (operate on original)
    if options.resize_mode != "none":
        w, h = img.size
        if options.resize_mode == "width" and options.resize_value > 0:
            new_w = options.resize_value
            new_h = int(h * (new_w / w))
            img = img.resize((new_w, new_h), Image.LANCZOS)
        elif options.resize_mode == "height" and options.resize_value > 0:
            new_h = options.resize_value
            new_w = int(w * (new_h / h))
            img = img.resize((new_w, new_h), Image.LANCZOS)
        elif options.resize_mode == "percent" and options.resize_value > 0:
            scale = options.resize_value / 100.0
            new_w = max(1, int(w * scale))
            new_h = max(1, int(h * scale))
            img = img.resize((new_w, new_h), Image.LANCZOS)
    result = _overlay_text(img, text_cfg)
    if state is not None:
        result = _overlay_image_watermark(result, state)

    out_dir = Path(options.output_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    src = Path(src_path)
    stem = src.stem
    if options.naming_mode == "prefix":
        stem = f"{options.naming_value}{stem}"
    elif options.naming_mode == "suffix":
        stem = f"{stem}{options.naming_value}"

    if options.format == "jpeg":
        out_path = out_dir / f"{stem}.jpeg"
        rgb = result.convert("RGB")
        rgb.save(out_path, format="JPEG", quality=options.jpeg_quality)
    else:
        out_path = out_dir / f"{stem}.png"
        result.save(out_path, format="PNG")

    return str(out_path)


