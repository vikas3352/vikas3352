"""
tests/test_config_and_assets.py

Unit tests verifying:
1. config/profile_config.json schema, types, and required fields.
2. README.md asset links resolve to existing non-empty files.
3. .gitignore contains mandatory privacy patterns.
"""

import unittest
import os
import json
import re

ROOT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


class TestConfigAndAssets(unittest.TestCase):

    def test_config_schema(self):
        cfg_path = os.path.join(ROOT_DIR, "config", "profile_config.json")
        self.assertTrue(os.path.exists(cfg_path))
        with open(cfg_path, "r", encoding="utf-8") as f:
            data = json.load(f)

        self.assertIn("developer", data)
        self.assertIn("tech_stack", data)
        self.assertIn("featured_projects", data)

        dev = data["developer"]
        self.assertEqual(dev["username"], "vikas3352")
        self.assertEqual(dev["name"], "Vikas Jangid")
        self.assertIsInstance(dev["titles"], list)
        self.assertGreater(len(dev["titles"]), 0)

        projects = data["featured_projects"]
        self.assertGreater(len(projects), 0)
        for p in projects:
            self.assertIn("name", p)
            self.assertIn("description", p)
            self.assertIn("url", p)
            self.assertTrue(p["url"].startswith("http"))

    def test_readme_asset_links(self):
        readme_path = os.path.join(ROOT_DIR, "README.md")
        self.assertTrue(os.path.exists(readme_path))
        with open(readme_path, "r", encoding="utf-8") as f:
            content = f.read()

        # Find all references to assets/
        asset_refs = re.findall(r'assets/[\w\-\.]+', content)
        self.assertGreater(len(asset_refs), 0, "README should reference generated assets")

        for ref in set(asset_refs):
            target_path = os.path.join(ROOT_DIR, ref)
            self.assertTrue(os.path.exists(target_path), f"Referenced asset does not exist: {ref}")
            self.assertGreater(os.path.getsize(target_path), 0, f"Referenced asset is empty: {ref}")

    def test_gitignore_rules(self):
        gi_path = os.path.join(ROOT_DIR, ".gitignore")
        self.assertTrue(os.path.exists(gi_path))
        with open(gi_path, "r", encoding="utf-8") as f:
            rules = f.read()

        mandatory_patterns = [
            ".venv/",
            "__pycache__/",
            "*.py",
            ".env",
            "item_5.png",
            "source-photo.*",
            "source-prepped.png"
        ]
        for pattern in mandatory_patterns:
            self.assertIn(pattern.split()[0], rules, f"Missing mandatory gitignore pattern: {pattern}")


if __name__ == "__main__":
    unittest.main()

