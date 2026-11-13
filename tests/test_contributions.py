"""
tests/test_contributions.py

Unit tests for contribution data parsing, streak calculations,
date continuity, leap year handling, and failure persistence.
"""

import unittest
import json
import os
import sys
from datetime import date, timedelta
from unittest.mock import patch, MagicMock

sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "scripts"))
from fetch_contributions import parse_contributions_html, validate_username, parse_tooltip_count, fetch_contributions

ROOT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_PATH = os.path.join(ROOT_DIR, "data", "contributions.json")


class TestContributions(unittest.TestCase):

    def test_validate_username(self):
        self.assertTrue(validate_username("vikas3352"))
        self.assertTrue(validate_username("octocat"))
        self.assertTrue(validate_username("a-b-c"))
        self.assertFalse(validate_username(""))
        self.assertFalse(validate_username("invalid_user!"))
        self.assertFalse(validate_username("-startwithhyphen"))
        self.assertFalse(validate_username("a" * 40))

    def test_parse_tooltip_count(self):
        self.assertEqual(parse_tooltip_count("No contributions on November 9th."), 0)
        self.assertEqual(parse_tooltip_count("1 contribution on August 30th."), 1)
        self.assertEqual(parse_tooltip_count("12 contributions on May 15th."), 12)
        self.assertEqual(parse_tooltip_count("1,234 contributions on January 1st."), 1234)

    def test_synthetic_calendar_parsing_and_streaks(self):
        # Generate valid synthetic HTML with continuous dates
        today = date(2026, 1, 1)
        start_date = today - timedelta(days=364)
        
        html_parts = [
            '<div class="js-yearly-contributions">',
            '<h2 id="js-contribution-activity-description">42 contributions in the last year</h2>',
            '<table class="ContributionCalendar-grid"><tbody><tr>'
        ]

        # Simulate 365 days
        for i in range(365):
            cur_date = start_date + timedelta(days=i)
            d_str = cur_date.isoformat()
            c_id = f"day-{i}"
            # Let days 350..355 have contributions (6-day streak)
            if 350 <= i <= 355:
                level = 2
                tip = "3 contributions on that day"
            else:
                level = 0
                tip = "No contributions on that day"

            html_parts.append(
                f'<td data-date="{d_str}" id="{c_id}" data-level="{level}"></td>'
                f'<tool-tip for="{c_id}">{tip}</tool-tip>'
            )

        html_parts.append('</tr></tbody></table></div>')
        full_html = "\n".join(html_parts)

        parsed = parse_contributions_html(full_html, "testuser")
        
        self.assertEqual(parsed["metadata"]["username"], "testuser")
        self.assertEqual(parsed["metadata"]["total_days_parsed"], 365)
        # Sum of counts = 6 days * 3 = 18 contributions
        self.assertGreaterEqual(parsed["stats"]["total_contributions"], 18)
        self.assertEqual(parsed["stats"]["longest_streak"], 6)

    def test_leap_year_handling(self):
        # Test leap year sequence (Feb 27 -> Feb 28 -> Feb 29 -> Mar 1, 2024)
        leap_start = date(2023, 11, 1)
        days_count = 366  # covers 2024 leap day
        html_parts = [
            '<div class="js-yearly-contributions">',
            '<h2 id="js-contribution-activity-description">10 contributions</h2>'
        ]
        for i in range(days_count):
            cur = leap_start + timedelta(days=i)
            d_str = cur.isoformat()
            c_id = f"leap-{i}"
            html_parts.append(
                f'<td data-date="{d_str}" id="{c_id}" data-level="1"></td>'
                f'<tool-tip for="{c_id}">1 contribution</tool-tip>'
            )
        html_parts.append('</div>')
        parsed = parse_contributions_html("\n".join(html_parts), "testuser")
        self.assertEqual(parsed["metadata"]["total_days_parsed"], 366)
        self.assertIn("2024-02-29", [d["date"] for d in parsed["days"]])

    def test_invalid_html_raises_error(self):
        with self.assertRaises(ValueError):
            parse_contributions_html("<html><body>Not a contribution page</body></html>", "testuser")

    def test_discontinuous_dates_raises_error(self):
        html = '''
        <div class="js-yearly-contributions">
        <td data-date="2026-01-01" id="d1" data-level="0"></td>
        <tool-tip for="d1">No contributions</tool-tip>
        <td data-date="2026-01-05" id="d2" data-level="0"></td>
        <tool-tip for="d2">No contributions</tool-tip>
        </div>
        '''
        with self.assertRaises(ValueError):
            parse_contributions_html(html, "testuser")

    def test_network_failure_preserves_data(self):
        # Verify that if fetch_contributions raises RuntimeError or ConnectionError,
        # existing contributions.json remains intact
        self.assertTrue(os.path.exists(DATA_PATH), "Expected existing data/contributions.json")
        mtime_before = os.path.getmtime(DATA_PATH)

        with patch("requests.get") as mock_get:
            mock_resp = MagicMock()
            mock_resp.status_code = 500
            mock_get.return_value = mock_resp

            with self.assertRaises(RuntimeError):
                fetch_contributions("vikas3352")

        # Confirm file modified time and contents are untouched
        mtime_after = os.path.getmtime(DATA_PATH)
        self.assertEqual(mtime_before, mtime_after, "File was modified despite network failure")


if __name__ == "__main__":
    unittest.main()
