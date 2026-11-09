"""Unit tests for the offline calendar engine."""

from __future__ import annotations

from datetime import date, timedelta

import pytest

KNOWN_EASTER = {
    2000: date(2000, 4, 30),
    2010: date(2010, 4, 4),
    2021: date(2021, 5, 2),
    2024: date(2024, 5, 5),
    2025: date(2025, 4, 20),
    2026: date(2026, 4, 12),
    2027: date(2027, 5, 2),
    2050: date(2050, 4, 17),
    2100: date(2100, 5, 2),
}


@pytest.mark.parametrize("year,expected", KNOWN_EASTER.items())
def test_orthodox_easter(engine, year, expected):
    assert engine.orthodox_easter(year) == expected


def test_easter_matches_dateutil(engine):
    easter = pytest.importorskip("dateutil.easter")
    for year in range(1583, 4100):
        assert engine.orthodox_easter(year) == easter.easter(
            year, easter.EASTER_ORTHODOX
        ), year


def test_every_day_computes(calendar):
    """All days from 1925 to 2100 compute and every Sunday has a title or readings."""
    day = date(1925, 1, 1)
    while day <= date(2100, 12, 31):
        info = calendar.day(day)
        assert info.title, day
        if day.weekday() == 6:
            assert info.sunday is not None, day
            assert info.sunday.title or info.sunday.gospel, day
        day += timedelta(days=1)


def test_easter_day(calendar):
    info = calendar.day(date(2026, 4, 12))
    assert info.title == "(†) Învierea Domnului (Sfintele Paști)"
    assert info.feast_level == "great"
    assert info.red and info.no_weddings
    assert info.sunday.gospel == "Ev. Ioan I, 1-17"


def test_movable_feasts(calendar):
    assert calendar.day(date(2026, 5, 21)).title.startswith("(†) Înălțarea Domnului")
    assert calendar.day(date(2026, 6, 1)).title == "(†) Sf. Treime"
    assert calendar.day(date(2026, 4, 17)).title.startswith("†) Izvorul Tămăduirii")


def test_feast_levels(calendar):
    # Great feasts: class="sarbatoare" in HTML (red-letter feasts, regardless of (†), †) or †)
    assert calendar.day(date(2026, 1, 6)).feast_level == "great"   # (†) Botezul Domnului
    assert calendar.day(date(2026, 1, 7)).feast_level == "great"   # † Soborul Sf. Ioan Botezătorul
    assert calendar.day(date(2026, 1, 30)).feast_level == "great"  # †) Sf. Trei Ierarhi
    assert calendar.day(date(2026, 4, 17)).feast_level == "great"  # †) Izvorul Tămăduirii
    assert calendar.day(date(2026, 5, 21)).feast_level == "great"  # (†) Înălțarea / †) Sf. Constantin și Elena
    assert calendar.day(date(2026, 12, 6)).feast_level == "great"  # †) Sf. Ier. Nicolae (on Sunday)

    # Major feasts: class="normal" with (†) or † in text
    assert calendar.day(date(2026, 1, 11)).feast_level == "major"  # † Sf. Cuv. Teodosie (on Sunday)
    assert calendar.day(date(2026, 1, 17)).feast_level == "major"  # †) Sf. Cuv. Antonie cel Mare

    # Normal days: no class="sarbatoare" feast and no cross in text (including ordinary Sundays)
    assert calendar.day(date(2026, 1, 8)).feast_level == "normal"  # ordinary weekday
    assert calendar.day(date(2027, 1, 3)).feast_level == "normal"  # ordinary Sunday
    assert calendar.day(date(2027, 1, 3)).feast_day is True


def test_st_george_moves_to_bright_monday(calendar):
    # 2030: 23 April is Holy Tuesday, Easter is 28 April.
    assert "Gheorghe" not in calendar.day(date(2030, 4, 23)).title
    assert calendar.day(date(2030, 4, 23)).feast_level == "normal"
    assert "Gheorghe" in calendar.day(date(2030, 4, 29)).title
    assert calendar.day(date(2030, 4, 29)).feast_level == "great"
    # 2027: 23 April is in Lent but before Holy Week, so it stays.
    assert "Gheorghe" in calendar.day(date(2027, 4, 23)).title
    assert calendar.day(date(2027, 4, 23)).feast_level == "great"


def test_fasting_rules(calendar):
    assert calendar.day(date(2026, 4, 10)).fasting == "Post negru"  # Good Friday
    assert (
        calendar.day(date(2026, 3, 25)).fasting == "Dezlegare la pește"
    )  # Annunciation in Lent
    assert calendar.day(date(2026, 12, 24)).fasting.startswith("Numai seara")
    assert (
        calendar.day(date(2026, 12, 30)).fasting == "Harți"
    )  # Wednesday after Christmas
    assert calendar.day(date(2026, 11, 4)).fasting == "Post"  # ordinary Wednesday
    assert calendar.day(date(2026, 11, 5)).fasting is None  # ordinary Thursday
    assert calendar.day(date(2026, 1, 5)).fasting == "Post negru"


def test_no_weddings(calendar):
    assert calendar.day(date(2026, 12, 1)).no_weddings  # Nativity fast
    assert calendar.day(date(2026, 1, 6)).no_weddings
    assert not calendar.day(date(2026, 10, 3)).no_weddings  # ordinary Saturday


def test_official_calendar_rules(calendar):
    # Moșii de toamnă: the Saturday before St. Michael (8 Nov).
    assert any("Moşii de toamnă" in n for n in calendar.day(date(2026, 11, 7)).notes)
    # Sunday of the 7th Council Fathers reads the parable of the sower.
    sunday = calendar.day(date(2026, 10, 11)).sunday
    assert sunday.title == "Duminica a XXI-a după Rusalii"
    assert "Sinodul al VII-lea" in sunday.subtitle


def test_tone_cycle(calendar):
    # Thomas Sunday starts tone 1.
    assert calendar.day(date(2026, 4, 19)).sunday.tone == 1
    assert calendar.day(date(2026, 4, 26)).sunday.tone == 2


@pytest.mark.parametrize(
    "day,phase",
    [
        (date(2024, 4, 8), "new_moon"),
        (date(2025, 3, 14), "full_moon"),
        (date(2026, 1, 10), "last_quarter"),
        (date(2026, 1, 26), "first_quarter"),
        (date(2026, 2, 2), "full_moon"),  # 1 Feb 22:09 UTC is 2 Feb in Bucharest
    ],
)
def test_moon_phases(calendar, day, phase):
    assert calendar.day(day).moon_phase == phase


def test_next_day_crosses_year(calendar):
    feast = calendar.next_day(
        date(2026, 12, 31), lambda d: d.feast_level == "great" and d.date.year == 2027
    )
    assert feast is not None and feast.date == date(2027, 1, 1)
