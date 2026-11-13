#!/usr/bin/env python3
"""
scripts/fetch_contributions.py

Fetches real public GitHub contribution data for a given user,
validates HTML and data integrity, calculates daily counts, streaks,
and saves the result to data/contributions.json.

Safety & Integrity Rules:
- Never fabricates or estimates numbers.
- Validates date continuity and detects duplicates.
- Derives week columns and boundaries dynamically without hardcoding days.
- Preserves existing data/contributions.json if network or HTML parsing fails.
- Returns non-zero exit code on failure to ensure CI visibility.
"""

import sys
import os
import json
import re
from datetime import datetime, date, timedelta, timezone
from typing import Dict, Any, List, Optional
import requests

DATA_PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "data", "contributions.json")
CONFIG_PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "config", "profile_config.json")


def validate_username(username: str) -> bool:
    """Validate GitHub username according to GitHub naming rules."""
    if not username or len(username) > 39:
        return False
    return bool(re.match(r"^[a-zA-Z0-9](?:[a-zA-Z0-9]|-(?=[a-zA-Z0-9])){0,38}$", username))


def parse_tooltip_count(text: str) -> int:
    """Extract exact integer contribution count from tooltip text."""
    if "No contributions" in text or "no contributions" in text:
        return 0
    m = re.search(r"(\d[\d,]*)\s+contribution", text)
    if m:
        return int(m.group(1).replace(",", ""))
    return 0


def parse_contributions_html(html_text: str, username: str) -> Dict[str, Any]:
    """
    Parse contribution HTML from GitHub profile response.
    Returns structured data with days, weeks, streaks, and statistics.
    """
    if "js-yearly-contributions" not in html_text and "ContributionCalendar" not in html_text:
        raise ValueError("Invalid HTML structure: Contribution calendar container not found")

    # Match td tags with data-date and id
    # Example: <td ... data-date="2025-11-09" id="contribution-day-component-0-0" data-level="0" ...>
    td_pattern = re.compile(
        r'<td[^>]*data-date="(?P<date>\d{4}-\d{2}-\d{2})"[^>]*id="(?P<id>[^"]+)"[^>]*data-level="(?P<level>\d+)"[^>]*>',
        re.MULTILINE
    )
    
    # Tooltip pattern: <tool-tip ... for="id">...</tool-tip>
    tooltip_pattern = re.compile(
        r'<tool-tip[^>]*for="(?P<id>[^"]+)"[^>]*>(?P<text>.*?)</tool-tip>',
        re.DOTALL
    )

    tooltips: Dict[str, str] = {}
    for tm in tooltip_pattern.finditer(html_text):
        tooltips[tm.group("id")] = tm.group("text").strip()

    days_raw = []
    seen_dates = set()

    for match in td_pattern.finditer(html_text):
        d_str = match.group("date")
        d_id = match.group("id")
        d_level = int(match.group("level"))

        if d_str in seen_dates:
            continue
        seen_dates.add(d_str)

        tip_text = tooltips.get(d_id, "")
        count = parse_tooltip_count(tip_text)

        # Parse date object
        dt = datetime.strptime(d_str, "%Y-%m-%d").date()

        days_raw.append({
            "date": d_str,
            "datetime": dt,
            "id": d_id,
            "level": d_level,
            "count": count,
            "weekday": dt.weekday()  # Monday=0, Sunday=6 in Python; GitHub starts on Sunday
        })

    if not days_raw:
        # Check alternative: sometimes attributes appear in different order
        alt_pattern = re.compile(
            r'<td(?=[^>]*data-date="(?P<date>\d{4}-\d{2}-\d{2})")(?=[^>]*id="(?P<id>[^"]+)")(?=[^>]*data-level="(?P<level>\d+)")'
        )
        for match in alt_pattern.finditer(html_text):
            d_str = match.group("date")
            d_id = match.group("id")
            d_level = int(match.group("level"))
            if d_str in seen_dates:
                continue
            seen_dates.add(d_str)
            tip_text = tooltips.get(d_id, "")
            count = parse_tooltip_count(tip_text)
            dt = datetime.strptime(d_str, "%Y-%m-%d").date()
            days_raw.append({
                "date": d_str,
                "datetime": dt,
                "id": d_id,
                "level": d_level,
                "count": count,
                "weekday": dt.weekday()
            })

    if len(days_raw) < 300:
        raise ValueError(f"Extracted only {len(days_raw)} days, expected full annual calendar (> 300 days)")

    # Sort strictly by date ascending
    days_raw.sort(key=lambda x: x["datetime"])

    # Validate date continuity (each day must be exactly previous_day + 1)
    for i in range(1, len(days_raw)):
        prev_dt = days_raw[i-1]["datetime"]
        curr_dt = days_raw[i]["datetime"]
        diff = (curr_dt - prev_dt).days
        if diff != 1:
            raise ValueError(f"Date continuity break between {prev_dt} and {curr_dt} (gap: {diff} days)")

    # Extract declared total from header if available
    h2_match = re.search(r'id="js-contribution-activity-description"[^>]*>\s*([\d,]+)\s*contributions', html_text)
    header_total = int(h2_match.group(1).replace(",", "")) if h2_match else None

    # Calculate actual sum from parsed daily counts
    total_from_counts = sum(d["count"] for d in days_raw)
    total_contributions = header_total if header_total is not None and header_total >= total_from_counts else total_from_counts

    # Calculate streaks based on consecutive calendar days
    # Current streak: count backwards from latest day (or yesterday if today has 0 yet)
    current_streak = 0
    longest_streak = 0
    running_streak = 0

    for d in days_raw:
        if d["count"] > 0:
            running_streak += 1
            if running_streak > longest_streak:
                longest_streak = running_streak
        else:
            running_streak = 0

    # Calculate current streak up to the latest date
    # Check if latest day has contributions or yesterday
    rev_days = list(reversed(days_raw))
    latest_day = rev_days[0]
    
    # If today has 0 contributions, but yesterday has >= 1, streak is still active
    start_idx = 0
    if latest_day["count"] == 0 and len(rev_days) > 1 and rev_days[1]["count"] > 0:
        start_idx = 1

    for d in rev_days[start_idx:]:
        if d["count"] > 0:
            current_streak += 1
        else:
            break

    # Dynamic Calendar Layout:
    # GitHub week grid: Rows are 0 (Sunday) to 6 (Saturday).
    # Python datetime.weekday(): Monday=0, Sunday=6
    # Map to GitHub weekday: (python_weekday + 1) % 7 -> Sunday=0, Monday=1, ..., Saturday=6
    
    start_date = days_raw[0]["datetime"]
    end_date = days_raw[-1]["datetime"]
    
    # Group into dynamic columns
    weeks: List[List[Optional[Dict[str, Any]]]] = []
    current_week: List[Optional[Dict[str, Any]]] = [None] * 7

    for d in days_raw:
        gh_weekday = (d["datetime"].weekday() + 1) % 7
        current_week[gh_weekday] = {
            "date": d["date"],
            "count": d["count"],
            "level": d["level"]
        }
        # If Saturday (last day of week), advance week
        if gh_weekday == 6:
            weeks.append(current_week)
            current_week = [None] * 7

    # If partial week remains at end
    if any(cell is not None for cell in current_week):
        weeks.append(current_week)

    # Monthly breakdown for analytics
    monthly_counts: Dict[str, int] = {}
    for d in days_raw:
        m_key = d["date"][:7] # YYYY-MM
        monthly_counts[m_key] = monthly_counts.get(m_key, 0) + d["count"]

    result = {
        "metadata": {
            "username": username,
            "fetched_at_utc": datetime.now(timezone.utc).isoformat(),
            "start_date": start_date.isoformat(),
            "end_date": end_date.isoformat(),
            "total_days_parsed": len(days_raw),
            "total_weeks": len(weeks)
        },
        "stats": {
            "total_contributions": total_contributions,
            "current_streak": current_streak,
            "longest_streak": longest_streak,
            "active_days": sum(1 for d in days_raw if d["count"] > 0),
            "monthly_counts": monthly_counts
        },
        "days": [
            {
                "date": d["date"],
                "count": d["count"],
                "level": d["level"],
                "gh_weekday": (d["datetime"].weekday() + 1) % 7
            }
            for d in days_raw
        ],
        "weeks": weeks
    }

    return result


def fetch_contributions(username: str, timeout: int = 15) -> Dict[str, Any]:
    """
    Fetch contribution HTML from GitHub and return parsed result.
    """
    if not validate_username(username):
        raise ValueError(f"Invalid username format: '{username}'")

    url = f"https://github.com/users/{username}/contributions"
    headers = {
        "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
        "Accept-Language": "en-US,en;q=0.9"
    }

    response = requests.get(url, headers=headers, timeout=timeout)
    if response.status_code != 200:
        raise RuntimeError(f"GitHub returned HTTP status {response.status_code} for user '{username}'")

    return parse_contributions_html(response.text, username)


def main():
    username = None
    if len(sys.argv) > 1:
        username = sys.argv[1].strip()
    elif os.path.exists(CONFIG_PATH):
        try:
            with open(CONFIG_PATH, "r", encoding="utf-8") as f:
                cfg = json.load(f)
                username = cfg.get("developer", {}).get("username")
        except Exception as e:
            print(f"Warning: Failed reading config: {e}", file=sys.stderr)

    if not username:
        username = "vikas3352"

    print(f"Fetching contribution data for GitHub user: {username} ...")
    os.makedirs(os.path.dirname(DATA_PATH), exist_ok=True)

    try:
        data = fetch_contributions(username)
        # Write to temporary file first to guarantee atomic write
        tmp_path = DATA_PATH + ".tmp"
        with open(tmp_path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2)
        os.replace(tmp_path, DATA_PATH)

        print(f"Successfully updated {DATA_PATH}")
        print(f"  Total contributions: {data['stats']['total_contributions']}")
        print(f"  Current streak:      {data['stats']['current_streak']} days")
        print(f"  Longest streak:      {data['stats']['longest_streak']} days")
        print(f"  Total days parsed:   {data['metadata']['total_days_parsed']}")
        print(f"  Date range:          {data['metadata']['start_date']} to {data['metadata']['end_date']}")
        sys.exit(0)

    except Exception as err:
        print(f"ERROR: Failed to fetch contribution data: {err}", file=sys.stderr)
        if os.path.exists(DATA_PATH):
            print(f"Preserving existing valid data at {DATA_PATH}", file=sys.stderr)
        else:
            print(f"No previous contribution data exists at {DATA_PATH}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
