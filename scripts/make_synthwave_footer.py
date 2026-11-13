#!/usr/bin/env python3
"""
scripts/make_synthwave_footer.py

Generates an aesthetic Synthwave wave gradient footer SVG banner.
Matches the neon pink/purple/cyan palette seen in the reference video.
"""

import os
import xml.etree.ElementTree as ET

OUTPUT_PATH = "assets/footer-banner.svg"

def make_footer():
    width = 850
    height = 90

    svg = f'''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {width} {height}" width="100%" height="{height}" style="background-color: transparent;">
  <defs>
    <!-- Wave Gradients -->
    <linearGradient id="waveGrad1" x1="0%" y1="0%" x2="100%" y2="0%">
      <stop offset="0%" stop-color="#0b0217" />
      <stop offset="30%" stop-color="#3d0c5a" />
      <stop offset="70%" stop-color="#ff007f" />
      <stop offset="100%" stop-color="#ffb900" />
    </linearGradient>

    <linearGradient id="waveGrad2" x1="0%" y1="0%" x2="100%" y2="0%">
      <stop offset="0%" stop-color="#01cdfe" />
      <stop offset="40%" stop-color="#b967ff" />
      <stop offset="80%" stop-color="#ff71ce" />
      <stop offset="100%" stop-color="#ff007f" />
    </linearGradient>
  </defs>

  <!-- Background Wave -->
  <path d="M 0,35 Q 210,0 425,35 T 850,25 L 850,90 L 0,90 Z" fill="url(#waveGrad1)" opacity="0.4" />

  <!-- Mid Wave -->
  <path d="M 0,45 Q 210,65 425,35 T 850,45 L 850,90 L 0,90 Z" fill="url(#waveGrad2)" opacity="0.7" />

  <!-- Foreground Crisp Wave -->
  <path d="M 0,55 Q 210,35 425,60 T 850,50 L 850,90 L 0,90 Z" fill="#0d1117" />
</svg>'''

    # Validate XML
    ET.fromstring(svg)

    os.makedirs(os.path.dirname(OUTPUT_PATH), exist_ok=True)
    with open(OUTPUT_PATH, "w", encoding="utf-8") as f:
        f.write(svg)
    print(f"Footer banner successfully generated at {OUTPUT_PATH}")

if __name__ == "__main__":
    make_footer()
