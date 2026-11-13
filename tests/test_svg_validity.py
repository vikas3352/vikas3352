"""
tests/test_svg_validity.py

Unit tests for validating SVG XML syntax, dimensions, viewBox,
and SMIL animation tags across all generated SVG assets.
"""

import unittest
import os
import xml.etree.ElementTree as ET

ASSETS_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "assets")


class TestSvgValidity(unittest.TestCase):

    def test_contribution_heatmap_svg(self):
        path = os.path.join(ASSETS_DIR, "contribution-heatmap.svg")
        self.assertTrue(os.path.exists(path), f"File {path} does not exist")
        
        # Test XML validity
        tree = ET.parse(path)
        root = tree.getroot()
        self.assertTrue(root.tag.endswith("svg"))
        self.assertIn("viewBox", root.attrib)
        self.assertIn("width", root.attrib)
        self.assertIn("height", root.attrib)

        # Ensure SMIL animations exist
        animations = root.findall(".//{http://www.w3.org/2000/svg}animate")
        self.assertGreater(len(animations), 0, "Heatmap SVG should contain SMIL animation elements")

    def test_ascii_portrait_svg(self):
        path = os.path.join(ASSETS_DIR, "ascii-portrait.svg")
        self.assertTrue(os.path.exists(path), f"File {path} does not exist")
        
        tree = ET.parse(path)
        root = tree.getroot()
        self.assertTrue(root.tag.endswith("svg"))
        self.assertIn("viewBox", root.attrib)

        animations = root.findall(".//{http://www.w3.org/2000/svg}animate")
        self.assertGreater(len(animations), 0, "Animated ASCII SVG should contain SMIL animation elements")

    def test_ascii_portrait_static_svg(self):
        path = os.path.join(ASSETS_DIR, "ascii-portrait-static.svg")
        self.assertTrue(os.path.exists(path), f"File {path} does not exist")
        
        tree = ET.parse(path)
        root = tree.getroot()
        self.assertTrue(root.tag.endswith("svg"))

    def test_info_card_svg(self):
        path = os.path.join(ASSETS_DIR, "info-card.svg")
        self.assertTrue(os.path.exists(path), f"File {path} does not exist")
        
        tree = ET.parse(path)
        root = tree.getroot()
        self.assertTrue(root.tag.endswith("svg"))
        self.assertIn("viewBox", root.attrib)

    def test_ascii_portrait_gif(self):
        path = os.path.join(ASSETS_DIR, "ascii-portrait.gif")
        self.assertTrue(os.path.exists(path), f"File {path} does not exist")
        size = os.path.getsize(path)
        # Ensure it is lightweight (< 1.5MB)
        self.assertLess(size, 1.5 * 1024 * 1024, f"GIF file size {size} exceeds 1.5MB")
        self.assertGreater(size, 1024, "GIF file appears empty")


if __name__ == "__main__":
    unittest.main()

