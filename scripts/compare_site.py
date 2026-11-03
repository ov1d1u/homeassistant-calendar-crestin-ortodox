#!/usr/bin/env python3
"""Compare the offline engine with saved noutati-ortodoxe.ro pages.

Usage:
    python scripts/compare_site.py                 # summary for every saved year
    python scripts/compare_site.py 2030 --show 20  # also list differences
    python scripts/compare_site.py --field fasting --show 50
"""
from __future__ import annotations

import argparse
import collections
import sys
from datetime import date
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from engine_loader import FIXTURES, load_engine  # noqa: E402
from site_parser import SiteDay, load_fixtures, parse_year  # noqa: E402

FIELDS = [
    "saints",
    "red",
    "notes",
    "fasting",
    "no_weddings",
    "sunday_title",
    "sunday_subtitle",
    "apostle",
    "gospel",
    "tone",
    "eothinon",
]


def site_values(day: SiteDay, fast_labels) -> dict:
    sunday = day.sunday
    return {
        "saints": day.saints,
        "red": day.is_red,
        "notes": sorted(c for c in day.comments if c not in fast_labels),
        "fasting": next((c for c in day.comments if c in fast_labels), None),
        "no_weddings": day.no_weddings,
        "sunday_title": sunday.title if sunday else None,
        "sunday_subtitle": sunday.subtitle if sunday else None,
        "apostle": sunday.apostle if sunday else None,
        "gospel": sunday.gospel if sunday else None,
        "tone": sunday.tone if sunday else None,
        "eothinon": sunday.eothinon if sunday else None,
    }


def engine_values(day) -> dict:
    sunday = day.sunday
    return {
        "saints": day.saints,
        "red": day.red,
        "notes": sorted(day.notes),
        "fasting": day.fasting,
        "no_weddings": day.no_weddings,
        "sunday_title": sunday.title if sunday else None,
        "sunday_subtitle": sunday.subtitle if sunday else None,
        "apostle": sunday.apostle if sunday else None,
        "gospel": sunday.gospel if sunday else None,
        "tone": sunday.tone if sunday else None,
        "eothinon": sunday.eothinon if sunday else None,
    }


def compare_year(calendar, engine, year: int, site_days: dict[date, SiteDay]):
    """Return (counts of matches per field, list of differences)."""
    matches = collections.Counter()
    totals = collections.Counter()
    diffs = []
    for day, site_day in sorted(site_days.items()):
        expected = site_values(site_day, engine.FAST_LEVEL)
        actual = engine_values(calendar.day(day))
        for field in FIELDS:
            totals[field] += 1
            if expected[field] == actual[field]:
                matches[field] += 1
            else:
                diffs.append((day, field, expected[field], actual[field]))
    return matches, totals, diffs


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("years", nargs="*", type=int)
    parser.add_argument(
        "--show", type=int, default=0, help="number of differences to print"
    )
    parser.add_argument(
        "--field", action="append", help="only show differences for this field"
    )
    args = parser.parse_args()

    engine = load_engine()
    calendar = engine.OrthodoxCalendar()
    if args.years:
        sites = {
            y: parse_year(
                (FIXTURES / f"calendar_{y}.html").read_text(encoding="utf-8"), y
            )
            for y in args.years
        }
    else:
        sites = load_fixtures(FIXTURES)

    all_diffs = []
    print("year  " + " ".join(f"{f[:9]:>9}" for f in FIELDS))
    for year, site_days in sites.items():
        matches, totals, diffs = compare_year(calendar, engine, year, site_days)
        all_diffs += diffs
        print(
            f"{year}  "
            + " ".join(f"{100 * matches[f] / totals[f]:9.1f}" for f in FIELDS)
        )

    if args.show:
        shown = [d for d in all_diffs if not args.field or d[1] in args.field]
        for day, field, expected, actual in shown[: args.show]:
            print(f"{day} {field}\n   site:   {expected!r}\n   engine: {actual!r}")


if __name__ == "__main__":
    main()
