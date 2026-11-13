#!/usr/bin/env python3
"""
scripts/make_activity_graph.py

Generates the Synthwave GitHub Activity Line Graph (matching the video):
- Neon pink glowing stroke with filled gradient
- Month/day points
- Activity metrics header
- Deep dark theme (#0d1117)
- Saves to assets/activity-graph.svg
"""

import os
import json
import xml.etree.ElementTree as ET
from datetime import datetime

DATA_PATH = "data/contributions.json"
OUTPUT_PATH = "assets/activity-graph.svg"

def make_activity_graph():
    if not os.path.exists(DATA_PATH):
        raise FileNotFoundError(f"Missing {DATA_PATH}")

    with open(DATA_PATH, "r", encoding="utf-8") as f:
        data = json.load(f)

    stats = data.get("stats", {})
    total_contribs = stats.get("total_contributions", 605)
    current_streak = stats.get("current_streak", 2)
    longest_streak = stats.get("longest_streak", 8)
    
    # Take the last 30 days of data for high-detail daily activity wave
    days = data.get("days", [])
    recent_days = days[-30:] if len(days) >= 30 else days

    width = 850
    height = 280

    pad_left = 60
    pad_right = 40
    pad_top = 80
    pad_bottom = 50

    plot_w = width - pad_left - pad_right
    plot_h = height - pad_top - pad_bottom

    counts = [d["count"] for d in recent_days]
    max_c = max(max(counts), 10)

    # Calculate coordinates
    num_pts = len(recent_days)
    dx = plot_w / max(1, num_pts - 1)

    pts = []
    for i, c in enumerate(counts):
        x = pad_left + i * dx
        # Invert y: y=0 is at top
        y = pad_top + plot_h - (c / max_c) * plot_h
        pts.append((x, y, c, recent_days[i]["date"]))

    # Generate smooth Bezier curve or polyline
    path_d = [f"M {pts[0][0]},{pts[0][1]}"]
    for i in range(len(pts) - 1):
        x0, y0 = pts[i][0], pts[i][1]
        x1, y1 = pts[i+1][0], pts[i+1][1]
        # Control points for smooth spline
        cx0 = (x0 + x1) / 2
        cy0 = y0
        cx1 = (x0 + x1) / 2
        cy1 = y1
        path_d.append(f"C {cx0},{cy0} {cx1},{cy1} {x1},{y1}")

    line_str = " ".join(path_d)
    area_str = f"{line_str} L {pts[-1][0]},{pad_top + plot_h} L {pts[0][0]},{pad_top + plot_h} Z"

    svg = f'''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {width} {height}" width="100%" height="{height}" style="background-color: #0b0217; border-radius: 10px; border: 1px solid #3d1259; font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', 'Fira Code', sans-serif;">
  <defs>
    <linearGradient id="areaGrad" x1="0%" y1="0%" x2="0%" y2="100%">
      <stop offset="0%" stop-color="#ff007f" stop-opacity="0.5" />
      <stop offset="60%" stop-color="#b967ff" stop-opacity="0.15" />
      <stop offset="100%" stop-color="#0b0217" stop-opacity="0" />
    </linearGradient>

    <filter id="pinkGlow" x="-20%" y="-20%" width="140%" height="140%">
      <feGaussianBlur stdDeviation="3" result="blur" />
      <feMerge>
        <feMergeNode in="blur" />
        <feMergeNode in="SourceGraphic" />
      </feMerge>
    </filter>
  </defs>

  <!-- Title & Subtitle -->
  <text x="{width // 2}" y="36" fill="#ff71ce" font-size="16" font-weight="700" letter-spacing="1" text-anchor="middle">Vikas's Contribution Activity</text>
  <text x="{width // 2}" y="54" fill="#a58dbd" font-size="11" text-anchor="middle">Past 30 Days Activity Wave • Total: {total_contribs} Contributions</text>

  <!-- Horizontal Grid Lines -->
  <g stroke="#241734" stroke-width="1">
    <line x1="{pad_left}" y1="{pad_top}" x2="{width - pad_right}" y2="{pad_top}" />
    <line x1="{pad_left}" y1="{pad_top + plot_h * 0.33}" x2="{width - pad_right}" y2="{pad_top + plot_h * 0.33}" />
    <line x1="{pad_left}" y1="{pad_top + plot_h * 0.66}" x2="{width - pad_right}" y2="{pad_top + plot_h * 0.66}" />
    <line x1="{pad_left}" y1="{pad_top + plot_h}" x2="{width - pad_right}" y2="{pad_top + plot_h}" stroke="#ff007f" stroke-opacity="0.4" />
  </g>

  <!-- Y Axis Labels -->
  <text x="{pad_left - 10}" y="{pad_top + 4}" fill="#7a698f" font-size="10" text-anchor="end">{max_c}</text>
  <text x="{pad_left - 10}" y="{pad_top + plot_h * 0.5 + 4}" fill="#7a698f" font-size="10" text-anchor="end">{max_c // 2}</text>
  <text x="{pad_left - 10}" y="{pad_top + plot_h + 4}" fill="#7a698f" font-size="10" text-anchor="end">0</text>

  <!-- Area Gradient Fill -->
  <path d="{area_str}" fill="url(#areaGrad)" />

  <!-- Smooth Glowing Line -->
  <path d="{line_str}" fill="none" stroke="#ff007f" stroke-width="3" filter="url(#pinkGlow)" />

  <!-- Data Points -->
  <g fill="#01cdfe" stroke="#ffffff" stroke-width="1.5">'''

    for x, y, c, d_str in pts:
        if c > 0:
            svg += f'\n    <circle cx="{x:.1f}" cy="{y:.1f}" r="3.5"><title>{d_str}: {c} contributions</title></circle>'

    # X Axis Labels (sample every 5 days)
    svg += '\n  </g>\n  <g fill="#7a698f" font-size="9" text-anchor="middle">'
    for i, (x, y, c, d_str) in enumerate(pts):
        if i % 5 == 0 or i == len(pts) - 1:
            day_num = d_str[-2:]
            svg += f'\n    <text x="{x:.1f}" y="{pad_top + plot_h + 18}">{day_num}</text>'

    svg += '\n  </g>\n</svg>'

    ET.fromstring(svg)

    os.makedirs(os.path.dirname(OUTPUT_PATH), exist_ok=True)
    with open(OUTPUT_PATH, "w", encoding="utf-8") as f:
        f.write(svg)
    print(f"Activity graph generated at {OUTPUT_PATH}")

if __name__ == "__main__":
    make_activity_graph()
