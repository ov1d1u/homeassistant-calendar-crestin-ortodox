"""Shared fixtures. The engine is loaded without Home Assistant."""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))

# Make sure Home Assistant tests find this repository's custom_components
# (pytest-homeassistant-custom-component ships its own, empty one).
sys.path.insert(0, str(ROOT))
_loaded = sys.modules.get("custom_components")
if _loaded is not None and str(ROOT) not in str(getattr(_loaded, "__file__", "")):
    del sys.modules["custom_components"]
import custom_components  # noqa: E402,F401

from engine_loader import FIXTURES, load_engine  # noqa: E402
from site_parser import parse_year  # noqa: E402


@pytest.fixture(scope="session")
def engine():
    return load_engine()


@pytest.fixture(scope="session")
def calendar(engine):
    return engine.OrthodoxCalendar(time_zone="Europe/Bucharest")


@pytest.fixture(scope="session")
def site_pages():
    """Parsed noutati-ortodoxe.ro pages, by year."""
    pages = {}
    for path in sorted(FIXTURES.glob("calendar_*.html")):
        year = int(path.stem.split("_")[1])
        pages[year] = parse_year(path.read_text(encoding="utf-8"), year)
    return pages
