#!/usr/bin/env python3
"""
scripts/make_polaroid.py

Takes item_5.png and creates an aesthetic Polaroid-framed photo
with a dark background, glowing neon border, and handwritten caption.
Saves to assets/profile-polaroid.png.
"""

import os
from PIL import Image, ImageDraw, ImageFont, ImageFilter, ImageOps
import numpy as np

PHOTO_PATH = "item_5.png"
OUTPUT_PATH = "assets/profile-polaroid.png"

def create_polaroid():
    if not os.path.exists(PHOTO_PATH):
        raise FileNotFoundError(f"Missing {PHOTO_PATH}")

    img = Image.open(PHOTO_PATH).convert("RGBA")
    
    # Locate subject bounding box
    arr = np.array(img)
    alpha = arr[:, :, 3]
    y_idx, x_idx = np.where(alpha > 40)
    
    if len(y_idx) > 0 and len(x_idx) > 0:
        pad = 20
        min_x = max(0, int(x_idx.min()) - pad)
        max_x = min(img.width, int(x_idx.max()) + pad)
        min_y = max(0, int(y_idx.min()) - pad)
        max_y = min(img.height, int(y_idx.max()) + pad)
        cropped = img.crop((min_x, min_y, max_x, max_y))
    else:
        cropped = img

    # Composite subject onto a deep synthwave gradient background
    target_photo_w = 260
    target_photo_h = 280
    
    # Resize photo maintaining aspect ratio
    cropped.thumbnail((target_photo_w, target_photo_h), Image.Resampling.LANCZOS)
    
    # Create dark gradient photo canvas
    photo_canvas = Image.new("RGBA", (target_photo_w, target_photo_h), "#0d1117")
    # Draw subtle gradient
    draw_canvas = ImageDraw.Draw(photo_canvas)
    for y in range(target_photo_h):
        # Deep violet to midnight dark
        r = int(18 + 15 * (1 - y / target_photo_h))
        g = int(14 + 10 * (1 - y / target_photo_h))
        b = int(28 + 25 * (1 - y / target_photo_h))
        draw_canvas.line([(0, y), (target_photo_w, y)], fill=(r, g, b, 255))

    # Paste subject centered
    paste_x = (target_photo_w - cropped.width) // 2
    paste_y = (target_photo_h - cropped.height) // 2
    photo_canvas.paste(cropped, (paste_x, paste_y), cropped)

    # Polaroid Dimensions
    polaroid_w = target_photo_w + 32  # 292
    polaroid_h = target_photo_h + 84  # 364
    
    # Create polaroid image (aesthetic retro white paper with subtle texture)
    polaroid = Image.new("RGBA", (polaroid_w, polaroid_h), "#faf9f6")
    
    # Paste photo onto polaroid
    polaroid.paste(photo_canvas, (16, 16))
    
    # Draw photo inner border (subtle neon pink accent)
    draw_pol = ImageDraw.Draw(polaroid)
    draw_pol.rectangle([15, 15, 16 + target_photo_w, 16 + target_photo_h], outline="#ff71ce", width=2)

    # Add handwritten-style caption
    caption = "Vikas  ✨"
    try:
        font = None
        for font_candidate in [
            "/System/Library/Fonts/Supplemental/Comic Sans MS.ttf",
            "/System/Library/Fonts/Supplemental/MarkerFelt.ttc",
            "/System/Library/Fonts/Supplemental/Chalkboard.ttc",
            "/System/Library/Fonts/Helvetica.ttc"
        ]:
            if os.path.exists(font_candidate):
                font = ImageFont.truetype(font_candidate, 20)
                break
        if font is None:
            font = ImageFont.load_default()
    except Exception:
        font = ImageFont.load_default()

    # Center caption below photo
    bbox = draw_pol.textbbox((0, 0), caption, font=font)
    tw = bbox[2] - bbox[0]
    tx = (polaroid_w - tw) // 2
    ty = 16 + target_photo_h + 22
    draw_pol.text((tx, ty), caption, fill="#241734", font=font)

    # Add rounded corners and outer neon drop glow on dark background
    canvas_w = polaroid_w + 24
    canvas_h = polaroid_h + 24
    
    final_img = Image.new("RGBA", (canvas_w, canvas_h), (0, 0, 0, 0))
    
    # Subtle drop shadow/glow
    glow_mask = Image.new("RGBA", (canvas_w, canvas_h), (0, 0, 0, 0))
    glow_draw = ImageDraw.Draw(glow_mask)
    glow_draw.rounded_rectangle([12, 12, 12 + polaroid_w, 12 + polaroid_h], radius=10, fill=(255, 0, 127, 90))
    blurred_glow = glow_mask.filter(ImageFilter.GaussianBlur(8))
    
    final_img.paste(blurred_glow, (0, 0), blurred_glow)

    # Round polaroid corners
    mask = Image.new("L", (polaroid_w, polaroid_h), 0)
    mask_draw = ImageDraw.Draw(mask)
    mask_draw.rounded_rectangle([0, 0, polaroid_w, polaroid_h], radius=8, fill=255)

    final_img.paste(polaroid, (12, 12), mask)

    os.makedirs(os.path.dirname(OUTPUT_PATH), exist_ok=True)
    final_img.save(OUTPUT_PATH, "PNG", optimize=True)
    print(f"Polaroid successfully generated at {OUTPUT_PATH} ({final_img.size})")

if __name__ == "__main__":
    create_polaroid()
