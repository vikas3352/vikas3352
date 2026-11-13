#!/usr/bin/env python3
"""
scripts/render_heatmap_svg.py

Renders an animated SVG contribution calendar from data/contributions.json.
Features:
- Dynamic column calculation based on actual parsed weeks.
- Terminal window titlebar aesthetic with macOS buttons.
- Diagonal sweep reveal animation using SVG SMIL.
- Stat indicators (Total contributions, current streak, longest streak).
- Dynamic month labels and weekday labels.
- Less / More legend.
- Strict XML well-formedness validation.
"""

import sys
import os
import json
import xml.etree.ElementTree as ET
from typing import Dict, Any, List

DATA_PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "data", "contributions.json")
OUTPUT_PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "assets", "contribution-heatmap.svg")

# Terminal & Color Palette
BG_COLOR = "#0d1117"
BORDER_COLOR = "#30363d"
HEADER_BG = "#161b22"
TEXT_COLOR = "#c9d1d9"
MUTED_TEXT = "#8b949e"
ACCENT_GREEN = "#39d353"

LEVEL_COLORS = {
    0: "#161b22",
    1: "#0e4429",
    2: "#006d32",
    3: "#26a641",
    4: "#39d353"
}

MONTH_NAMES = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]


def render_heatmap(data: Dict[str, Any], output_path: str = OUTPUT_PATH) -> str:
    """Generate and validate SVG heatmap."""
    weeks = data.get("weeks", [])
    num_weeks = len(weeks)
    stats = data.get("stats", {})
    metadata = data.get("metadata", {})

    total_contribs = stats.get("total_contributions", 0)
    current_streak = stats.get("current_streak", 0)
    longest_streak = stats.get("longest_streak", 0)
    username = metadata.get("username", "developer")

    # Layout Dimensions
    CELL_SIZE = 12
    CELL_GAP = 3
    CELL_RADIUS = 2

    LEFT_PAD = 45   # Room for weekday labels
    TOP_PAD = 95    # Header + prompt + month labels
    BOTTOM_PAD = 40 # Legend + date range
    RIGHT_PAD = 30

    grid_width = num_weeks * (CELL_SIZE + CELL_GAP) - CELL_GAP
    grid_height = 7 * (CELL_SIZE + CELL_GAP) - CELL_GAP

    svg_width = LEFT_PAD + grid_width + RIGHT_PAD
    svg_height = TOP_PAD + grid_height + BOTTOM_PAD

    # Month label positions
    # Determine the week column where each new month starts
    month_positions = []
    seen_months = set()
    for col_idx, week in enumerate(weeks):
        for day in week:
            if day and day.get("date"):
                # day["date"] is YYYY-MM-DD
                m_num = int(day["date"][5:7])
                if m_num not in seen_months:
                    seen_months.add(m_num)
                    month_positions.append((col_idx, MONTH_NAMES[m_num - 1]))
                break

    svg_lines = []
    svg_lines.append(f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {svg_width} {svg_height}" width="{svg_width}" height="{svg_height}" style="background-color: {BG_COLOR}; border-radius: 8px; border: 1px solid {BORDER_COLOR}; font-family: -apple-system, BlinkMacSystemFont, \'Segoe UI\', \'Fira Code\', monospace, sans-serif;">')

    # Styles
    svg_lines.append('''
  <defs>
    <style>
      .terminal-title { fill: #8b949e; font-size: 11px; font-weight: 600; }
      .prompt-cmd { fill: #39d353; font-size: 12px; font-family: 'Fira Code', 'Courier New', monospace; font-weight: 500; }
      .prompt-user { fill: #58a6ff; font-size: 12px; font-family: 'Fira Code', monospace; }
      .stat-label { fill: #8b949e; font-size: 11px; }
      .stat-val { fill: #58a6ff; font-weight: 600; font-size: 11px; }
      .month-label { fill: #8b949e; font-size: 10px; }
      .wday-label { fill: #8b949e; font-size: 9px; }
      .legend-text { fill: #8b949e; font-size: 10px; }
    </style>
  </defs>''')

    # Terminal Header Window Bar
    svg_lines.append(f'  <rect x="0" y="0" width="{svg_width}" height="32" fill="{HEADER_BG}" rx="8" />')
    svg_lines.append(f'  <rect x="0" y="24" width="{svg_width}" height="8" fill="{HEADER_BG}" />')
    svg_lines.append(f'  <line x1="0" y1="32" x2="{svg_width}" y2="32" stroke="{BORDER_COLOR}" stroke-width="1" />')

    # macOS window action dots
    svg_lines.append('  <circle cx="16" cy="16" r="5" fill="#ff5f56" />')
    svg_lines.append('  <circle cx="32" cy="16" r="5" fill="#ffbd2e" />')
    svg_lines.append('  <circle cx="48" cy="16" r="5" fill="#27c93f" />')

    # Terminal Window Title
    svg_lines.append(f'  <text x="{svg_width // 2}" y="20" text-anchor="middle" class="terminal-title">{username}@dev-station: ~/contributions</text>')

    # Terminal Prompt & Summary Stats Banner
    svg_lines.append(f'  <text x="20" y="54"><tspan class="prompt-user">{username}@github:~$</tspan> <tspan class="prompt-cmd">git activity --annual</tspan></text>')

    # Summary Stats pills on the right
    stats_x = svg_width - RIGHT_PAD
    stats_y = 54
    stat_str = f'<tspan class="stat-label">Total: </tspan><tspan class="stat-val">{total_contribs}</tspan>  │  <tspan class="stat-label">Current Streak: </tspan><tspan class="stat-val">{current_streak}d</tspan>  │  <tspan class="stat-label">Max Streak: </tspan><tspan class="stat-val">{longest_streak}d</tspan>'
    svg_lines.append(f'  <text x="{stats_x}" y="{stats_y}" text-anchor="end">{stat_str}</text>')

    # Month Labels
    for col_idx, m_name in month_positions:
        x_pos = LEFT_PAD + col_idx * (CELL_SIZE + CELL_GAP)
        svg_lines.append(f'  <text x="{x_pos}" y="{TOP_PAD - 8}" class="month-label">{m_name}</text>')

    # Weekday Labels (Mon=1, Wed=3, Fri=5 in 0-indexed Sunday-first GitHub grid)
    # Sunday=0, Mon=1, Tue=2, Wed=3, Thu=4, Fri=5, Sat=6
    day_labels = [(1, "Mon"), (3, "Wed"), (5, "Fri")]
    for r_idx, w_name in day_labels:
        y_pos = TOP_PAD + r_idx * (CELL_SIZE + CELL_GAP) + 9
        svg_lines.append(f'  <text x="{LEFT_PAD - 8}" y="{y_pos}" text-anchor="end" class="wday-label">{w_name}</text>')

    # Contribution Calendar Grid with Diagonal Reveal Animation
    svg_lines.append('  <!-- Heatmap Cells -->')
    svg_lines.append('  <g id="calendar-grid">')

    for col_idx, week in enumerate(weeks):
        col_x = LEFT_PAD + col_idx * (CELL_SIZE + CELL_GAP)
        for row_idx, day in enumerate(week):
            if day is None:
                continue

            row_y = TOP_PAD + row_idx * (CELL_SIZE + CELL_GAP)
            level = day.get("level", 0)
            fill_color = LEVEL_COLORS.get(level, LEVEL_COLORS[0])
            count = day.get("count", 0)
            d_str = day.get("date", "")

            # Diagonal animation delay: based on Manhattan distance (col + row)
            # Stagger smoothly over ~1.2s total duration
            anim_delay = round((col_idx + row_idx) * 0.02, 3)

            # Cell rect with SMIL animation for diagonal sweep
            # We animate opacity from 0 to 1 and fill color transition
            cell_xml = (
                f'    <rect x="{col_x}" y="{row_y}" width="{CELL_SIZE}" height="{CELL_SIZE}" '
                f'rx="{CELL_RADIUS}" ry="{CELL_RADIUS}" fill="{fill_color}" opacity="0">'
                f'<animate attributeName="opacity" from="0" to="1" dur="0.3s" begin="{anim_delay}s" fill="freeze" />'
                f'<title>{d_str}: {count} contributions</title>'
                f'</rect>'
            )
            svg_lines.append(cell_xml)

    svg_lines.append('  </g>')

    # Footer: Date Range on left, Less -> More Legend on right
    footer_y = TOP_PAD + grid_height + 22
    start_date = metadata.get("start_date", "")
    end_date = metadata.get("end_date", "")
    range_text = f"Activity window: {start_date} → {end_date}"
    svg_lines.append(f'  <text x="{LEFT_PAD}" y="{footer_y}" class="legend-text">{range_text}</text>')

    # Legend
    legend_right = svg_width - RIGHT_PAD
    legend_cells = [0, 1, 2, 3, 4]
    leg_cell_size = 10
    leg_gap = 3
    leg_total_w = len(legend_cells) * (leg_cell_size + leg_gap) - leg_gap + 65
    leg_start_x = legend_right - leg_total_w

    svg_lines.append(f'  <text x="{leg_start_x}" y="{footer_y}" class="legend-text">Less</text>')
    
    cur_x = leg_start_x + 30
    for lvl in legend_cells:
        svg_lines.append(
            f'  <rect x="{cur_x}" y="{footer_y - 8}" width="{leg_cell_size}" height="{leg_cell_size}" '
            f'rx="2" fill="{LEVEL_COLORS[lvl]}" />'
        )
        cur_x += leg_cell_size + leg_gap

    svg_lines.append(f'  <text x="{cur_x + 5}" y="{footer_y}" class="legend-text">More</text>')

    svg_lines.append('</svg>')

    full_svg = "\n".join(svg_lines)

    # Validate XML well-formedness before saving
    try:
        ET.fromstring(full_svg)
    except ET.ParseError as err:
        raise ValueError(f"Generated SVG is not valid XML: {err}")

    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    with open(output_path, "w", encoding="utf-8") as f:
        f.write(full_svg)

    return output_path


def main():
    if not os.path.exists(DATA_PATH):
        print(f"Error: {DATA_PATH} not found. Run fetch_contributions.py first.", file=sys.stderr)
        sys.exit(1)

    with open(DATA_PATH, "r", encoding="utf-8") as f:
        data = json.load(f)

    out_file = render_heatmap(data)
    print(f"Successfully generated validated contribution heatmap at: {out_file}")


if __name__ == "__main__":
    main()

