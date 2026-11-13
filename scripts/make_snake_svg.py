#!/usr/bin/env python3
"""
scripts/make_snake_svg.py

Renders a Synthwave-themed contribution grid with a moving neon snake animation:
- Synthwave palette (#0b0217 background, #ff007f snake, #01cdfe / #ff71ce dots)
- Animated SMIL snake head and trailing body
- Based on real contribution calendar data from data/contributions.json
- Saves to assets/contribution-snake.svg
"""

import os
import json
import xml.etree.ElementTree as ET

DATA_PATH = "data/contributions.json"
OUTPUT_PATH = "assets/contribution-snake.svg"

# Synthwave colors for contribution levels
SYNTH_LEVELS = {
    0: "#160728",
    1: "#3c1053",
    2: "#721b82",
    3: "#b967ff",
    4: "#ff71ce"
}

def make_snake_svg():
    if not os.path.exists(DATA_PATH):
        raise FileNotFoundError(f"Missing {DATA_PATH}")

    with open(DATA_PATH, "r", encoding="utf-8") as f:
        data = json.load(f)

    weeks = data.get("weeks", [])
    num_weeks = len(weeks)

    cell_size = 11
    cell_gap = 3
    pad_x = 24
    pad_y = 30

    grid_w = num_weeks * (cell_size + cell_gap) - cell_gap
    grid_h = 7 * (cell_size + cell_gap) - cell_gap

    width = grid_w + pad_x * 2
    height = grid_h + pad_y * 2

    svg_lines = [
        f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {width} {height}" width="100%" height="{height}" style="background-color: #0b0217; border-radius: 8px; border: 1px solid #3d1259;">',
        '  <defs>',
        '    <filter id="snakeGlow" x="-50%" y="-50%" width="200%" height="200%">',
        '      <feGaussianBlur stdDeviation="3" result="blur" />',
        '      <feMerge>',
        '        <feMergeNode in="blur" />',
        '        <feMergeNode in="SourceGraphic" />',
        '      </feMerge>',
        '    </filter>',
        '  </defs>',
        '  <!-- Contribution Grid Cells -->'
    ]

    # Render grid cells
    for col_idx, week in enumerate(weeks):
        cx = pad_x + col_idx * (cell_size + cell_gap)
        for row_idx, day in enumerate(week):
            if day is None:
                continue
            cy = pad_y + row_idx * (cell_size + cell_gap)
            lvl = day.get("level", 0)
            fill_col = SYNTH_LEVELS.get(lvl, SYNTH_LEVELS[0])
            svg_lines.append(
                f'  <rect x="{cx}" y="{cy}" width="{cell_size}" height="{cell_size}" rx="2" fill="{fill_col}" />'
            )

    # Calculate an animated path for the snake across active cells
    # Pick a sequence of waypoints across the grid
    waypoints = []
    # Start around week 10, weave through the grid
    coords = [
        (pad_x + 5 * 14, pad_y + 2 * 14),
        (pad_x + 12 * 14, pad_y + 2 * 14),
        (pad_x + 12 * 14, pad_y + 5 * 14),
        (pad_x + 22 * 14, pad_y + 5 * 14),
        (pad_x + 22 * 14, pad_y + 1 * 14),
        (pad_x + 35 * 14, pad_y + 1 * 14),
        (pad_x + 35 * 14, pad_y + 6 * 14),
        (pad_x + 48 * 14, pad_y + 6 * 14),
        (pad_x + 48 * 14, pad_y + 3 * 14),
        (pad_x + 52 * 14, pad_y + 3 * 14),
        (pad_x + 52 * 14, pad_y + 0 * 14),
        (pad_x + 5 * 14, pad_y + 0 * 14),
        (pad_x + 5 * 14, pad_y + 2 * 14),
    ]
    path_d = "M " + " L ".join(f"{x},{y}" for x, y in coords) + " Z"

    # Snake Head & Body Segments
    svg_lines.append('  <!-- Animated Neon Snake -->')
    # Head (Glowing Cyan & Magenta)
    svg_lines.append(f'''  <rect width="{cell_size}" height="{cell_size}" rx="2" fill="#01cdfe" filter="url(#snakeGlow)">
    <animateMotion path="{path_d}" dur="12s" repeatCount="indefinite" />
  </rect>''')

    # Body Segment 1
    svg_lines.append(f'''  <rect width="{cell_size}" height="{cell_size}" rx="2" fill="#ff007f" opacity="0.9">
    <animateMotion path="{path_d}" dur="12s" begin="-0.15s" repeatCount="indefinite" />
  </rect>''')

    # Body Segment 2
    svg_lines.append(f'''  <rect width="{cell_size}" height="{cell_size}" rx="2" fill="#ff71ce" opacity="0.8">
    <animateMotion path="{path_d}" dur="12s" begin="-0.30s" repeatCount="indefinite" />
  </rect>''')

    # Body Segment 3
    svg_lines.append(f'''  <rect width="{cell_size}" height="{cell_size}" rx="2" fill="#b967ff" opacity="0.7">
    <animateMotion path="{path_d}" dur="12s" begin="-0.45s" repeatCount="indefinite" />
  </rect>''')

    # Body Segment 4 (Tail)
    svg_lines.append(f'''  <rect width="{cell_size}" height="{cell_size}" rx="2" fill="#05ffa1" opacity="0.5">
    <animateMotion path="{path_d}" dur="12s" begin="-0.60s" repeatCount="indefinite" />
  </rect>''')

    svg_lines.append('</svg>')

    full_svg = "\n".join(svg_lines)
    ET.fromstring(full_svg)

    os.makedirs(os.path.dirname(OUTPUT_PATH), exist_ok=True)
    with open(OUTPUT_PATH, "w", encoding="utf-8") as f:
        f.write(full_svg)
    print(f"Snake SVG successfully generated at {OUTPUT_PATH}")

if __name__ == "__main__":
    make_snake_svg()
