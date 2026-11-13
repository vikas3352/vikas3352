"""
tests/test_svg_validity.py

Unit tests for validating SVG XML syntax, dimensions, viewBox,
and elements across all generated SVG and graphic assets.
"""

import unittest
import os
import xml.etree.ElementTree as ET

ASSETS_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "assets")


class TestSvgValidity(unittest.TestCase):

    def _assert_valid_svg(self, filename: str):
        path = os.path.join(ASSETS_DIR, filename)
        self.assertTrue(os.path.exists(path), f"File {path} does not exist")
        tree = ET.parse(path)
        root = tree.getroot()
        self.assertTrue(root.tag.endswith("svg"), f"{filename} root tag is not svg")
        return root

    def test_header_banner_svg(self):
        root = self._assert_valid_svg("header-banner.svg")
        self.assertIn("viewBox", root.attrib)

    def test_footer_banner_svg(self):
        root = self._assert_valid_svg("footer-banner.svg")
        self.assertIn("viewBox", root.attrib)

    def test_activity_graph_svg(self):
        root = self._assert_valid_svg("activity-graph.svg")
        self.assertIn("viewBox", root.attrib)

    def test_contribution_snake_svg(self):
        root = self._assert_valid_svg("contribution-snake.svg")
        self.assertIn("viewBox", root.attrib)

    def test_profile_polaroid_png(self):
        path = os.path.join(ASSETS_DIR, "profile-polaroid.png")
        self.assertTrue(os.path.exists(path))
        self.assertGreater(os.path.getsize(path), 1000)

    def test_contribution_heatmap_svg(self):
        root = self._assert_valid_svg("contribution-heatmap.svg")
        self.assertIn("viewBox", root.attrib)

    def test_ascii_portrait_svg(self):
        root = self._assert_valid_svg("ascii-portrait.svg")
        self.assertIn("viewBox", root.attrib)

    def test_ascii_portrait_static_svg(self):
        self._assert_valid_svg("ascii-portrait-static.svg")

    def test_info_card_svg(self):
        root = self._assert_valid_svg("info-card.svg")
        self.assertIn("viewBox", root.attrib)

    def test_ascii_portrait_gif(self):
        path = os.path.join(ASSETS_DIR, "ascii-portrait.gif")
        self.assertTrue(os.path.exists(path), f"File {path} does not exist")
        size = os.path.getsize(path)
        self.assertLess(size, 1.5 * 1024 * 1024)
        self.assertGreater(size, 1024)


if __name__ == "__main__":
    unittest.main()
