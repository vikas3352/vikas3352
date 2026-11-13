#!/usr/bin/env python3
"""
scripts/make_ascii_svg.py

Converts preprocessed photograph into:
1. assets/ascii-portrait.svg        (Animated SMIL SVG with typewriter row-by-row effect)
2. assets/ascii-portrait-static.svg (Clean static SVG fallback)
3. assets/ascii-portrait.gif        (Lightweight animated GIF fallback)

Rules & Quality:
- Transparent pixels strictly map to spaces (' ').
- Brightness ramp evaluated strictly on visible subject pixels.
- Terminal styling: macOS header dots, #0d1117 background, #39d353 phosphor green text.
- Validates XML for all generated SVGs.
"""

import sys
import os
import xml.etree.ElementTree as ET
from typing import List, Dict, Any, Tuple
import numpy as np
from PIL import Image, ImageDraw, ImageFont

# Import prep_photo from same directory
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from prep_photo import prepare_photo

ASSETS_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "assets")
ANIM_SVG_PATH = os.path.join(ASSETS_DIR, "ascii-portrait.svg")
STATIC_SVG_PATH = os.path.join(ASSETS_DIR, "ascii-portrait-static.svg")
GIF_PATH = os.path.join(ASSETS_DIR, "ascii-portrait.gif")

# Tuned 10-level density ramp for dark terminal background
RAMP = " .:-=+*#%@"


def generate_ascii_lines(gray: np.ndarray, alpha: np.ndarray, ramp: str = RAMP, alpha_thresh: int = 60) -> List[str]:
    """Convert matrix into lines of ASCII characters."""
    rows, cols = gray.shape
    lines = []
    ramp_len = len(ramp)

    for r in range(rows):
        chars = []
        for c in range(cols):
            if alpha[r, c] < alpha_thresh:
                chars.append(" ")
            else:
                val = gray[r, c]
                idx = int((val / 255.0) * (ramp_len - 1))
                chars.append(ramp[idx])
        lines.append("".join(chars))
    return lines


def render_svg_portrait(
    ascii_lines: List[str],
    animated: bool = True,
    output_path: str = ANIM_SVG_PATH,
    username: str = "vikas3352"
) -> str:
    """Generate SVG ASCII portrait (animated with SMIL or static)."""
    rows = len(ascii_lines)
    cols = max(len(line) for line in ascii_lines) if rows > 0 else 60

    char_w = 7.8
    char_h = 13.5
    pad_x = 24
    top_header = 56
    bottom_pad = 20

    width = int(cols * char_w + pad_x * 2)
    height = int(top_header + rows * char_h + bottom_pad)

    svg_lines = []
    svg_lines.append(f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {width} {height}" width="{width}" height="{height}" style="background-color: #0d1117; border-radius: 8px; border: 1px solid #30363d; font-family: \'Fira Code\', \'Courier New\', monospace;">')

    # Styles
    svg_lines.append('''
  <defs>
    <style>
      .terminal-title { fill: #8b949e; font-size: 11px; font-weight: 600; font-family: -apple-system, BlinkMacSystemFont, sans-serif; }
      .prompt-user { fill: #58a6ff; font-weight: 600; font-size: 12px; }
      .prompt-cmd { fill: #39d353; font-weight: 500; font-size: 12px; }
      .prompt-at { fill: #8b949e; }
      .ascii-row { fill: #39d353; font-size: 11.5px; font-family: 'Fira Code', 'Courier New', monospace; white-space: pre; }
    </style>
  </defs>''')

    # Window Title Bar
    svg_lines.append('  <rect x="0" y="0" width="100%" height="32" fill="#161b22" rx="8" />')
    svg_lines.append('  <rect x="0" y="24" width="100%" height="8" fill="#161b22" />')
    svg_lines.append('  <line x1="0" y1="32" x2="100%" y2="32" stroke="#30363d" stroke-width="1" />')

    # macOS window action dots
    svg_lines.append('  <circle cx="16" cy="16" r="5" fill="#ff5f56" />')
    svg_lines.append('  <circle cx="32" cy="16" r="5" fill="#ffbd2e" />')
    svg_lines.append('  <circle cx="48" cy="16" r="5" fill="#27c93f" />')

    # Window title
    svg_lines.append(f'  <text x="{width // 2}" y="20" text-anchor="middle" class="terminal-title">{username}@dev-station: ~ (ascii-portrait)</text>')

    # Terminal prompt
    svg_lines.append(f'  <text x="{pad_x}" y="50"><tspan class="prompt-user">{username}</tspan><tspan class="prompt-at">@</tspan><tspan class="prompt-user">station</tspan><tspan class="prompt-at">:~$</tspan> <tspan class="prompt-cmd">cat portrait.ascii</tspan></text>')

    # ASCII text rows
    svg_lines.append('  <g id="ascii-matrix">')
    for idx, line in enumerate(ascii_lines):
        y_pos = int(top_header + 16 + idx * char_h)
        # XML escape text
        escaped_line = line.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")

        if animated:
            # Typewriter animation delay (approx 0.035s per row, 1.5s total)
            row_delay = round(idx * 0.035, 3)
            row_xml = (
                f'    <text x="{pad_x}" y="{y_pos}" class="ascii-row" opacity="0">{escaped_line}'
                f'<animate attributeName="opacity" from="0" to="1" dur="0.05s" begin="{row_delay}s" fill="freeze" />'
                f'</text>'
            )
        else:
            row_xml = f'    <text x="{pad_x}" y="{y_pos}" class="ascii-row">{escaped_line}</text>'

        svg_lines.append(row_xml)

    svg_lines.append('  </g>')
    svg_lines.append('</svg>')

    full_svg = "\n".join(svg_lines)

    # Validate XML
    try:
        ET.fromstring(full_svg)
    except ET.ParseError as err:
        raise ValueError(f"Generated SVG is not valid XML: {err}")

    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    with open(output_path, "w", encoding="utf-8") as f:
        f.write(full_svg)

    return output_path


def render_animated_gif(
    ascii_lines: List[str],
    output_path: str = GIF_PATH,
    username: str = "vikas3352"
) -> str:
    """
    Generate an optimized, lightweight animated GIF showing progressive typewriter reveal.
    Keeps file size < 1MB for smooth GitHub mobile & web rendering.
    """
    rows = len(ascii_lines)
    cols = max(len(l) for l in ascii_lines)

    char_w = 8
    char_h = 14
    pad_x = 20
    top_header = 52
    bottom_pad = 16

    img_w = cols * char_w + pad_x * 2
    img_h = top_header + rows * char_h + bottom_pad

    # Try loading a system monospace font, fallback to default bitmap font
    font = None
    try:
        # macOS standard monospace fonts
        for font_name in ["/System/Library/Fonts/Menlo.ttc", "/Library/Fonts/Courier New.ttf"]:
            if os.path.exists(font_name):
                font = ImageFont.truetype(font_name, 12)
                break
    except Exception:
        font = None

    if font is None:
        font = ImageFont.load_default()

    # Pre-render base background image
    def draw_base_frame():
        base = Image.new("RGB", (img_w, img_h), color="#0d1117")
        draw = ImageDraw.Draw(base)
        # Header bar
        draw.rectangle([0, 0, img_w, 30], fill="#161b22")
        draw.line([0, 30, img_w, 30], fill="#30363d", width=1)
        # Dots
        draw.ellipse([14, 10, 24, 20], fill="#ff5f56")
        draw.ellipse([30, 10, 40, 20], fill="#ffbd2e")
        draw.ellipse([46, 10, 56, 20], fill="#27c93f")
        # Prompt
        draw.text((pad_x, 36), f"{username}@station:~$ cat portrait.ascii", fill="#39d353", font=font)
        return base

    frames = []
    # Step by 2 or 3 rows per frame to yield ~20-25 frames (lightweight GIF)
    step = max(1, rows // 22)

    for visible_rows in range(step, rows + step, step):
        count = min(visible_rows, rows)
        frame = draw_base_frame()
        draw = ImageDraw.Draw(frame)
        for r_idx in range(count):
            y = top_header + r_idx * char_h
            draw.text((pad_x, y), ascii_lines[r_idx], fill="#39d353", font=font)
        # Quantize to 32 colors for super lightweight file
        q_frame = frame.quantize(colors=32, method=Image.Resampling.NEAREST)
        frames.append(q_frame)

    # Add final frame with longer pause (e.g. 2.5 seconds)
    if frames:
        durations = [70] * (len(frames) - 1) + [2500]
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        frames[0].save(
            output_path,
            save_all=True,
            append_images=frames[1:],
            duration=durations,
            loop=0,
            optimize=True
        )

    return output_path


def main():
    photo_file = sys.argv[1] if len(sys.argv) > 1 else "item_5.png"
    print(f"Generating ASCII portraits from {photo_file}...")

    prepped = prepare_photo(photo_file, cols=64)
    lines = generate_ascii_lines(prepped["gray"], prepped["alpha"])

    # 1. Animated SVG
    anim_svg = render_svg_portrait(lines, animated=True, output_path=ANIM_SVG_PATH)
    print(f"  ✓ Animated SMIL SVG: {anim_svg}")

    # 2. Static SVG
    static_svg = render_svg_portrait(lines, animated=False, output_path=STATIC_SVG_PATH)
    print(f"  ✓ Static fallback SVG: {static_svg}")

    # 3. Animated GIF
    gif = render_animated_gif(lines, output_path=GIF_PATH)
    print(f"  ✓ Optimized animated GIF: {gif}")

    # Display preview in console
    print("\nASCII Silhouette Preview (first 15 rows):")
    for l in lines[:15]:
        print(l)


if __name__ == "__main__":
    main()

