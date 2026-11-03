"""Compare the offline engine with the saved noutati-ortodoxe.ro pages."""

from __future__ import annotations

import pytest
from compare_site import compare_year

# The site generates these years from its current data, so they should match.
# Known, intentional differences (the engine follows the official printed
# calendar of the Romanian Orthodox Church where it disagrees with the site's
# generator): Moșii de toamnă, the Sunday of the 7th Council and the extra
# Sunday in early December.
GENERATED_YEARS = range(2027, 2038)
GENERATED_MIN = 99.0

# Earlier years were edited by hand or use an older list of saints; they are
# compared loosely. "Nu se fac nunți" is missing from 2024-2026 on the site.
OLDER_MIN = {
    "saints": 80.0,
    "red": 99.0,
    "notes": 95.0,
    "fasting": 95.0,
    "sunday_title": 99.0,
    "apostle": 98.0,
    "gospel": 98.0,
    "tone": 99.0,
}


def _percentages(calendar, engine, year, pages):
    matches, totals, diffs = compare_year(calendar, engine, year, pages[year])
    return {field: 100 * matches[field] / totals[field] for field in totals}, diffs


@pytest.mark.parametrize("year", GENERATED_YEARS)
def test_generated_years(calendar, engine, site_pages, year):
    if year not in site_pages:
        pytest.skip(f"no saved page for {year}")
    percentages, diffs = _percentages(calendar, engine, year, site_pages)
    low = {f: round(p, 1) for f, p in percentages.items() if p < GENERATED_MIN}
    assert not low, f"{year}: {low}; first differences: {diffs[:5]}"


@pytest.mark.parametrize("year", range(2021, 2027))
def test_older_years(calendar, engine, site_pages, year):
    if year not in site_pages:
        pytest.skip(f"no saved page for {year}")
    percentages, _ = _percentages(calendar, engine, year, site_pages)
    low = {
        f: round(percentages[f], 1)
        for f, minimum in OLDER_MIN.items()
        if percentages[f] < minimum
    }
    assert not low, f"{year}: {low}"
