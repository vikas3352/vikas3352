#!/usr/bin/env python3
"""
scripts/make_info_card.py

Generates a Neofetch-style developer information card as an animated SVG.
Reads configuration from config/profile_config.json and verified contribution
stats from data/contributions.json.

Design:
- Dark terminal aesthetic (#0d1117)
- macOS window title bar with colored action buttons
- Fastfetch/Neofetch layout with terminal prompt
- Color palette badges
- CSS/SMIL staggered line fade-in animations
- Validated XML output
"""

import sys
import os
import json
import xml.etree.ElementTree as ET
from typing import Dict, Any

CONFIG_PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "config", "profile_config.json")
DATA_PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "data", "contributions.json")
OUTPUT_PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "assets", "info-card.svg")


def make_info_card(config_path: str = CONFIG_PATH, data_path: str = DATA_PATH, output_path: str = OUTPUT_PATH) -> str:
    with open(config_path, "r", encoding="utf-8") as f:
        config = json.load(f)

    contrib_stats = {}
    if os.path.exists(data_path):
        try:
            with open(data_path, "r", encoding="utf-8") as f:
                cdata = json.load(f)
                contrib_stats = cdata.get("stats", {})
        except Exception:
            pass

    dev = config.get("developer", {})
    tech = config.get("tech_stack", {})
    name = dev.get("name", "Vikas Jangid")
    username = dev.get("username", "vikas3352")
    titles = " • ".join(dev.get("titles", ["Full Stack Developer", "Software Engineer"]))
    sys_info = dev.get("system_info", {})

    total_contribs = contrib_stats.get("total_contributions", 605)
    current_streak = contrib_stats.get("current_streak", 0)

    # Info rows to display
    info_rows = [
        ("Host", f"developer-station ({sys_info.get('os', 'macOS / Linux')})"),
        ("Role", titles),
        ("Location", dev.get("location", "India")),
        ("Languages", ", ".join(tech.get("languages", ["TypeScript", "JavaScript", "Python", "SQL"]))),
        ("Frontend", ", ".join(tech.get("frontend", ["React", "Next.js", "Redux", "Tailwind CSS"]))),
        ("Backend", ", ".join(tech.get("backend", ["Node.js", "Express.js", "REST APIs", "JWT Auth"]))),
        ("Databases", ", ".join(tech.get("databases", ["MongoDB", "PostgreSQL"]))),
        ("DevOps / CI/CD", ", ".join(tech.get("devops_tools", ["GitHub Actions", "Docker", "Git"]))),
        ("Featured Work", "DebugFlow, InterviewPAL, DWPS Alwar, Zoniraz, Shine Limos"),
        ("GitHub Stats", f"{total_contribs} contributions • {current_streak}-day current streak"),
        ("Uptime", sys_info.get("uptime", "99.98% active coding"))
    ]

    width = 720
    row_height = 24
    start_y = 92
    height = start_y + len(info_rows) * row_height + 60

    svg_lines = []
    svg_lines.append(f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {width} {height}" width="{width}" height="{height}" style="background-color: #0d1117; border-radius: 8px; border: 1px solid #30363d; font-family: -apple-system, BlinkMacSystemFont, \'Fira Code\', \'Cascadia Code\', monospace, sans-serif;">')

    # CSS Animations
    svg_lines.append('''
  <defs>
    <style>
      .title-bar-text { fill: #8b949e; font-size: 11px; font-weight: 600; font-family: -apple-system, BlinkMacSystemFont, sans-serif; }
      .prompt-user { fill: #58a6ff; font-weight: 600; font-size: 13px; font-family: 'Fira Code', monospace; }
      .prompt-cmd { fill: #39d353; font-weight: 500; font-size: 13px; font-family: 'Fira Code', monospace; }
      .prompt-at { fill: #8b949e; }
      .header-name { fill: #39d353; font-size: 16px; font-weight: 700; font-family: 'Fira Code', monospace; }
      .header-sep { fill: #30363d; }
      .key-text { fill: #58a6ff; font-size: 12px; font-weight: 600; font-family: 'Fira Code', monospace; }
      .val-text { fill: #c9d1d9; font-size: 12px; font-family: 'Fira Code', monospace; }
      .tag-accent { fill: #79c0ff; }
      
      @keyframes fadeInLine {
        from { opacity: 0; transform: translateY(4px); }
        to { opacity: 1; transform: translateY(0); }
      }
      .anim-row {
        opacity: 0;
        animation: fadeInLine 0.4s ease-out forwards;
      }
    </style>
  </defs>''')

    # Window Title Bar
    svg_lines.append('  <rect x="0" y="0" width="100%" height="32" fill="#161b22" rx="8" />')
    svg_lines.append('  <rect x="0" y="24" width="100%" height="8" fill="#161b22" />')
    svg_lines.append('  <line x1="0" y1="32" x2="100%" y2="32" stroke="#30363d" stroke-width="1" />')

    # Action dots
    svg_lines.append('  <circle cx="16" cy="16" r="5" fill="#ff5f56" />')
    svg_lines.append('  <circle cx="32" cy="16" r="5" fill="#ffbd2e" />')
    svg_lines.append('  <circle cx="48" cy="16" r="5" fill="#27c93f" />')

    # Window title
    svg_lines.append(f'  <text x="{width // 2}" y="20" text-anchor="middle" class="title-bar-text">{username}@dev-station: ~ (neofetch)</text>')

    # Terminal Prompt
    svg_lines.append(f'  <text x="24" y="58"><tspan class="prompt-user">{username}</tspan><tspan class="prompt-at">@</tspan><tspan class="prompt-user">station</tspan><tspan class="prompt-at">:~$</tspan> <tspan class="prompt-cmd">neofetch --dev-profile</tspan></text>')

    # Developer Header & separator
    svg_lines.append(f'  <text x="24" y="82" class="header-name">{name} <tspan style="fill:#8b949e; font-size:12px; font-weight:normal;">(@{username})</tspan></text>')
    svg_lines.append(f'  <line x1="24" y1="90" x2="{width - 24}" y2="90" stroke="#30363d" stroke-width="1" />')

    # Rows with staggered animations
    current_y = start_y + 24
    for idx, (key, val) in enumerate(info_rows):
        anim_delay = round(0.1 + idx * 0.05, 2)
        # Escape XML entities in values
        clean_val = val.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
        row_svg = (
            f'  <g class="anim-row" style="animation-delay: {anim_delay}s;">'
            f'<text x="24" y="{current_y}" class="key-text">{key}:</text>'
            f'<text x="160" y="{current_y}" class="val-text">{clean_val}</text>'
            f'<animate attributeName="opacity" from="0" to="1" dur="0.3s" begin="{anim_delay}s" fill="freeze" />'
            f'</g>'
        )
        svg_lines.append(row_svg)
        current_y += row_height

    # Terminal Color Blocks Palette at bottom
    palette_y = current_y + 12
    palette_colors = ["#161b22", "#ff5555", "#50fa7b", "#f1fa8c", "#bd93f9", "#ff79c6", "#8be9fd", "#f8f8f2"]
    bright_palette = ["#44475a", "#ff6e6e", "#69ff94", "#ffffa5", "#d6acff", "#ff92df", "#a4ffff", "#ffffff"]
    
    box_w = 26
    box_h = 10
    start_x = 24
    
    svg_lines.append(f'  <!-- Terminal Color Blocks -->')
    svg_lines.append(f'  <g id="color-palette">')
    for c_idx, color in enumerate(palette_colors):
        x = start_x + c_idx * (box_w + 4)
        svg_lines.append(f'    <rect x="{x}" y="{palette_y}" width="{box_w}" height="{box_h}" fill="{color}" rx="2" />')
        svg_lines.append(f'    <rect x="{x}" y="{palette_y + box_h + 3}" width="{box_w}" height="{box_h}" fill="{bright_palette[c_idx]}" rx="2" />')
    svg_lines.append('  </g>')

    svg_lines.append('</svg>')

    full_svg = "\n".join(svg_lines)

    # Validate XML
    try:
        ET.fromstring(full_svg)
    except ET.ParseError as err:
        raise ValueError(f"Generated Info Card SVG is not valid XML: {err}")

    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    with open(output_path, "w", encoding="utf-8") as f:
        f.write(full_svg)

    return output_path


def main():
    out = make_info_card()
    print(f"Successfully generated validated Neofetch Info Card at: {out}")


if __name__ == "__main__":
    main()

