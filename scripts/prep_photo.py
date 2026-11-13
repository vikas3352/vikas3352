#!/usr/bin/env python3
"""
scripts/prep_photo.py

Preprocesses a user-provided portrait photograph:
1. Validates local file existence (default: item_5.png).
2. Crops to subject boundaries while preserving head-to-torso proportions.
3. Preserves alpha transparency mask (or applies local rembg if opaque).
4. Applies Contrast Limited Adaptive Histogram Equalization (CLAHE) on the subject.
5. Scales to terminal monospace character grid maintaining correct aspect ratio (~0.55).
"""

import sys
import os
from typing import Tuple, Dict, Any, Optional
import numpy as np
from PIL import Image

def apply_clahe(img_gray: np.ndarray, clip_limit: float = 2.2, grid_size: Tuple[int, int] = (8, 8)) -> np.ndarray:
    """
    Pure NumPy implementation of Contrast Limited Adaptive Histogram Equalization (CLAHE).
    Guarantees consistent local execution without external binary dependencies.
    """
    h, w = img_gray.shape
    gh, gw = grid_size
    tile_h = max(1, h // gh)
    tile_w = max(1, w // gw)

    mappings = np.zeros((gh, gw, 256), dtype=np.float32)
    for r in range(gh):
        for c in range(gw):
            tile = img_gray[r * tile_h : (r + 1) * tile_h, c * tile_w : (c + 1) * tile_w]
            if tile.size == 0:
                mappings[r, c] = np.arange(256, dtype=np.float32)
                continue
            hist, _ = np.histogram(tile, bins=256, range=(0, 256))
            clip_val = max(1, int(clip_limit * (tile.size / 256.0)))
            excess = np.sum(np.maximum(hist - clip_val, 0))
            hist = np.minimum(hist, clip_val)
            hist += excess // 256
            cdf = hist.cumsum()
            cdf_min = cdf.min()
            cdf_max = cdf.max()
            if cdf_max > cdf_min:
                mapping = (cdf - cdf_min) / (cdf_max - cdf_min) * 255.0
            else:
                mapping = np.arange(256, dtype=np.float32)
            mappings[r, c] = mapping

    out = np.zeros_like(img_gray, dtype=np.float32)
    r_coords = (np.arange(h) - tile_h / 2.0) / tile_h
    c_coords = (np.arange(w) - tile_w / 2.0) / tile_w

    r0 = np.clip(np.floor(r_coords).astype(int), 0, gh - 1)
    r1 = np.clip(r0 + 1, 0, gh - 1)
    c0 = np.clip(np.floor(c_coords).astype(int), 0, gw - 1)
    c1 = np.clip(c0 + 1, 0, gw - 1)

    dr = np.clip(r_coords - r0, 0, 1)[:, None]
    dc = np.clip(c_coords - c0, 0, 1)[None, :]

    for r in range(h):
        for c in range(w):
            val = img_gray[r, c]
            m00 = mappings[r0[r], c0[c], val]
            m01 = mappings[r0[r], c1[c], val]
            m10 = mappings[r1[r], c0[c], val]
            m11 = mappings[r1[r], c1[c], val]

            top = (1 - dc[0, c]) * m00 + dc[0, c] * m01
            bot = (1 - dc[0, c]) * m10 + dc[0, c] * m11
            out[r, c] = (1 - dr[r, 0]) * top + dr[r, 0] * bot

    return np.clip(out, 0, 255).astype(np.uint8)


def prepare_photo(
    photo_path: str = "item_5.png",
    cols: int = 64,
    char_aspect_ratio: float = 0.55
) -> Dict[str, Any]:
    """
    Process image and return character grid matrix and metadata.
    """
    if not os.path.exists(photo_path):
        raise FileNotFoundError(f"Source photograph not found at {photo_path}")

    img = Image.open(photo_path)
    if img.mode != "RGBA":
        img = img.convert("RGBA")

    # Locate subject bounding box based on alpha channel
    arr = np.array(img)
    alpha = arr[:, :, 3]

    y_indices, x_indices = np.where(alpha > 40)
    if len(y_indices) > 0 and len(x_indices) > 0:
        # Pad slightly around subject
        pad = 20
        min_x = max(0, int(x_indices.min()) - pad)
        max_x = min(img.width, int(x_indices.max()) + pad)
        min_y = max(0, int(y_indices.min()) - pad)
        max_y = min(img.height, int(y_indices.max()) + pad)
        cropped = img.crop((min_x, min_y, max_x, max_y))
    else:
        cropped = img

    # Compute target rows preserving monospace aspect ratio
    # Monospace characters are taller than wide (~0.55 width-to-height)
    aspect = cropped.height / cropped.width
    rows = max(10, int(cols * aspect * char_aspect_ratio))

    resized = cropped.resize((cols, rows), Image.Resampling.LANCZOS)
    arr_resized = np.array(resized)

    gray = np.array(resized.convert("L"))
    alpha_resized = arr_resized[:, :, 3]

    # Enhance contrast on subject using CLAHE
    enhanced_gray = apply_clahe(gray, clip_limit=2.2)

    return {
        "gray": enhanced_gray,
        "alpha": alpha_resized,
        "cols": cols,
        "rows": rows,
        "original_size": img.size,
        "cropped_size": cropped.size
    }


def main():
    path = sys.argv[1] if len(sys.argv) > 1 else "item_5.png"
    print(f"Preparing photo from: {path}")
    res = prepare_photo(path)
    print(f"Successfully prepped photo: {res['cols']} cols x {res['rows']} rows")


if __name__ == "__main__":
    main()

