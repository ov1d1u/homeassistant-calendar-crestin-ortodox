"""Offline Orthodox calendar engine (Romanian Orthodox Church, new calendar).

Everything is computed locally:

* Easter and the movable feasts (Triodion / Pentecostarion) are derived from
  the Julian computus.
* Saints, fixed feasts, fasting exceptions and Sunday readings come from the
  bundled JSON files in ``data/`` (built once by ``scripts/build_data.py``).
* Fasting rules, Sunday numbering (including the Lucan jump), tones and
  moon phases are rule based.

This module must not import Home Assistant, so it can be tested on its own.
"""

from __future__ import annotations

import json
import math
from dataclasses import dataclass, field
from datetime import date, datetime, timedelta, timezone
from functools import lru_cache
from pathlib import Path
from typing import Any, Callable
from zoneinfo import ZoneInfo

DATA_DIR = Path(__file__).parent / "data"

# Fasting labels, exactly as printed in the official calendar.
POST = "Post"
POST_NEGRU = "Post negru"
FISH = "Dezlegare la pește"
OIL = "Dezlegare la ulei și vin"
DAIRY = "Dezlegare la ouă, lactate și pește"
FREE = "Harți"
BREAD_WATER = "Numai seara, pâine și apă"
WHEAT = "Numai seara, grâu fiert îndulcit cu miere, poame, covrigi sau turte de făină"

# Higher level = less strict. ``None`` means no fasting at all.
FAST_LEVEL: dict[str | None, int] = {
    POST_NEGRU: 0,
    BREAD_WATER: 1,
    WHEAT: 1,
    POST: 2,
    OIL: 3,
    FISH: 4,
    DAIRY: 5,
    FREE: 6,
    None: 6,
}

ALITURGICAL = "Zi aliturgică"

# Fasting periods
PERIOD_ORDINARY = "ordinary"
PERIOD_FREE = "fast_free"
PERIOD_CHEESEFARE = "cheesefare"
PERIOD_LENT = "great_lent"
PERIOD_PENTECOSTARION = "pentecostarion"
PERIOD_APOSTLES = "apostles_fast"
PERIOD_DORMITION = "dormition_fast"
PERIOD_NATIVITY_1 = "nativity_fast_1"
PERIOD_NATIVITY_2 = "nativity_fast_2"
PERIOD_NATIVITY_3 = "nativity_fast_3"

FASTING_PERIODS = {
    PERIOD_CHEESEFARE,
    PERIOD_LENT,
    PERIOD_APOSTLES,
    PERIOD_DORMITION,
    PERIOD_NATIVITY_1,
    PERIOD_NATIVITY_2,
    PERIOD_NATIVITY_3,
}

FAST_PERIOD_NAMES = {
    PERIOD_LENT: "Sfintelor Paști",
    PERIOD_APOSTLES: "Sf. Ap. Petru și Pavel",
    PERIOD_DORMITION: "Adormirii Maicii Domnului",
    PERIOD_NATIVITY_1: "Nașterii Domnului",
    PERIOD_NATIVITY_2: "Nașterii Domnului",
    PERIOD_NATIVITY_3: "Nașterii Domnului",
}

# Easter offsets with special meaning
OFFSET_PALM_SUNDAY = -7
OFFSET_EASTER = 0
OFFSET_BRIGHT_MONDAY = 1
OFFSET_PENTECOST = 49
OFFSET_ALL_SAINTS = 56
# Days on which feasts never relax the fast.
STRICT_OFFSETS = {-48, -47, -6, -5, -4, -3, -2, -1}
# Pentecostarion Sundays have their own eothinon (offset -> eothinon).
PENTECOSTARION_EOTHINA = {7: 1, 14: 4, 21: 5, 28: 7, 35: 8, 42: 10}

# St. George is moved to Bright Monday when 23 April falls in Holy Week or on Easter.
ST_GEORGE_DATE = (4, 23)
ST_GEORGE_MOVE_OFFSETS = range(-7, 1)

# Sunday sequences between the Sunday after Theophany and the Triodion,
# by number of Sundays available.
WINTER_SUNDAYS = {
    1: [32],
    2: [29, 32],
    3: [29, 32, 17],
    4: [29, 31, 32, 17],
    5: [29, 31, 32, 16, 17],
    6: [29, 32, 14, 15, 16, 17],
}

SYNOD_SUBTITLES = {
    7: ((15, 21), "a Sf. Părinţi de la Sinodul al IV-lea Ecumenic"),
    10: ((11, 17), "a Sf. Părinţi de la Sinodul al VII-lea Ecumenic"),
}

DAY_NAMES_RO = ["Luni", "Marți", "Miercuri", "Joi", "Vineri", "Sâmbătă", "Duminică"]

MOON_PHASES = ["new_moon", "first_quarter", "full_moon", "last_quarter"]

FEAST_LEVEL_GREAT = "great"
FEAST_LEVEL_MAJOR = "major"
FEAST_LEVEL_NORMAL = "normal"


def orthodox_easter(year: int) -> date:
    """Return Orthodox Easter (Gregorian date) using the Julian computus."""
    a = year % 4
    b = year % 7
    c = year % 19
    d = (19 * c + 15) % 30
    e = (2 * a + 4 * b - d + 34) % 7
    month = (d + e + 114) // 31
    day = (d + e + 114) % 31 + 1
    # Julian -> Gregorian difference for March-May of this year.
    shift = year // 100 - year // 400 - 2
    return date(year, month, day) + timedelta(days=shift)


@dataclass
class SundayInfo:
    """Liturgical information printed for a Sunday."""

    title: str
    subtitle: str | None = None
    apostle: str | None = None
    gospel: str | None = None
    tone: int | None = None
    eothinon: int | None = None

    @property
    def full_title(self) -> str:
        """Title including the subtitle."""
        return " ".join(p for p in (self.title, self.subtitle) if p)

    @property
    def readings(self) -> dict[str, str]:
        """Readings as a dict (apostle / gospel)."""
        result = {}
        if self.apostle:
            result["apostle"] = self.apostle
        if self.gospel:
            result["gospel"] = self.gospel
        return result


@dataclass
class OrthodoxCalendarDay:
    """All information for a single day."""

    date: date
    saints: str
    romanian_saints: list[str] = field(default_factory=list)
    red: bool = False
    notes: list[str] = field(default_factory=list)
    fasting: str | None = None
    fasting_period: str = PERIOD_ORDINARY
    no_weddings: bool = False
    sunday: SundayInfo | None = None
    moon_phase: str | None = None

    @property
    def day(self) -> int:
        return self.date.day

    @property
    def month(self) -> int:
        return self.date.month

    @property
    def year(self) -> int:
        return self.date.year

    @property
    def day_of_week(self) -> str:
        """Romanian weekday name."""
        return DAY_NAMES_RO[self.date.weekday()]

    @property
    def is_sunday(self) -> bool:
        return self.date.weekday() == 6

    @property
    def title(self) -> str:
        """Text to show for the day (saints, or the feast for Easter-like Sundays)."""
        if self.saints:
            return self.saints
        if self.sunday and self.sunday.full_title:
            return self.sunday.full_title
        return ""

    @property
    def feast_level(self) -> str:
        text = self.title
        if "(†)" in text:
            return FEAST_LEVEL_GREAT
        if "†" in text:
            return FEAST_LEVEL_MAJOR
        return FEAST_LEVEL_NORMAL

    @property
    def feast_day(self) -> bool:
        """Red-letter day (Sundays included) or a day with a marked feast."""
        return self.red or self.feast_level != FEAST_LEVEL_NORMAL

    @property
    def is_fasting(self) -> bool:
        """Whether any fasting rule applies (fish/oil days count as fasting)."""
        return self.fasting is not None and self.fasting != FREE

    @property
    def fasting_info(self) -> list[str]:
        """Fasting related notes (kept as a list for backwards compatibility)."""
        info = [self.fasting] if self.fasting else []
        if ALITURGICAL in self.notes:
            info.append(ALITURGICAL)
        return info

    @property
    def sunday_title(self) -> str | None:
        return (
            self.sunday.full_title if self.sunday and self.sunday.full_title else None
        )

    @property
    def sunday_readings(self) -> dict[str, str]:
        return self.sunday.readings if self.sunday else {}

    def to_dict(self) -> dict[str, Any]:
        """Convert to a plain dict."""
        return {
            "date": self.date.isoformat(),
            "day_of_week": self.day_of_week,
            "saints": self.title,
            "romanian_saints": self.romanian_saints,
            "feast_day": self.feast_day,
            "feast_level": self.feast_level,
            "red": self.red,
            "fasting": self.fasting,
            "fasting_period": self.fasting_period,
            "fasting_info": self.fasting_info,
            "no_weddings": self.no_weddings,
            "notes": self.notes,
            "moon_phase": self.moon_phase,
            "is_sunday": self.is_sunday,
            "sunday_title": self.sunday_title,
            "sunday_readings": self.sunday_readings,
            "tone": self.sunday.tone if self.sunday else None,
            "eothinon": self.sunday.eothinon if self.sunday else None,
        }


def _sunday_on_or_after(day: date) -> date:
    return day + timedelta(days=(6 - day.weekday()) % 7)


def _sunday_in(year: int, month: int, first: int, last: int) -> date | None:
    """The Sunday between two days of a month, if any."""
    sunday = _sunday_on_or_after(date(year, month, first))
    return sunday if sunday.day <= last and sunday.month == month else None


def _join_readings(prefix: str | None, base: str | None, label: str) -> str | None:
    parts = [p for p in (prefix, base) if p]
    return f"{label} {'; '.join(parts)}" if parts else None


class OrthodoxCalendar:
    """Compute Orthodox calendar days offline."""

    def __init__(
        self,
        data_dir: Path | str | None = None,
        time_zone: str | None = None,
        data: dict[str, dict[str, Any]] | None = None,
    ) -> None:
        if data is None:
            directory = Path(data_dir) if data_dir else DATA_DIR
            data = {
                name: self._load(directory / f"{name}.json")
                for name in ("menaion", "triodion", "sundays")
            }
        self._menaion: dict[str, dict[str, Any]] = data["menaion"]
        self._triodion: dict[int, dict[str, Any]] = {
            int(k): v for k, v in data["triodion"].items()
        }
        self._sundays: dict[str, dict[str, Any]] = data["sundays"]
        self._tz = ZoneInfo(time_zone) if time_zone else ZoneInfo("Europe/Bucharest")
        self.day = lru_cache(maxsize=1024)(self._compute_day)  # type: ignore[method-assign]

    @staticmethod
    def _load(path: Path) -> dict[str, Any]:
        with path.open(encoding="utf-8") as file:
            return json.load(file)

    # ------------------------------------------------------------------ helpers

    @staticmethod
    @lru_cache(maxsize=256)
    def easter(year: int) -> date:
        return orthodox_easter(year)

    @staticmethod
    @lru_cache(maxsize=256)
    def apostles_fast_start(year: int) -> date:
        """Start of the Apostles' fast (Monday after All Saints, or earlier if Easter is late)."""
        easter = orthodox_easter(year)
        start = easter + timedelta(days=57)
        if start >= date(year, 6, 28):
            start = easter + timedelta(days=51)
        return start

    def menaion_key(self, day: date) -> str:
        key = f"{day.month:02d}-{day.day:02d}"
        leap = day.year % 4 == 0 and (day.year % 100 != 0 or day.year % 400 == 0)
        if leap and f"{key}L" in self._menaion:
            return f"{key}L"
        return key

    def offset(self, day: date) -> int:
        return (day - self.easter(day.year)).days

    def period(self, day: date) -> str:
        """Fasting period of a day."""
        offset = self.offset(day)
        md = (day.month, day.day)
        if -69 <= offset <= -63:
            return PERIOD_FREE
        if -55 <= offset <= -49:
            return PERIOD_CHEESEFARE
        if -48 <= offset <= -1:
            return PERIOD_LENT
        if 0 <= offset <= 6:
            return PERIOD_FREE
        if 7 <= offset <= OFFSET_PENTECOST:
            return PERIOD_PENTECOSTARION
        if self.apostles_fast_start(day.year) <= day <= date(day.year, 6, 28):
            return PERIOD_APOSTLES
        if 50 <= offset <= 56:
            return PERIOD_FREE
        if md >= (12, 25) or md <= (1, 4):
            return PERIOD_FREE
        if (8, 1) <= md <= (8, 14):
            return PERIOD_DORMITION
        if (11, 15) <= md <= (11, 20):
            return PERIOD_NATIVITY_1
        if (11, 21) <= md <= (12, 20):
            return PERIOD_NATIVITY_2
        if (12, 21) <= md <= (12, 24):
            return PERIOD_NATIVITY_3
        return PERIOD_ORDINARY

    def base_fasting(self, day: date) -> str | None:
        """Fasting rule from the period and weekday only (no feast exceptions)."""
        period = self.period(day)
        weekday = day.weekday()
        wed_fri = weekday in (2, 4)
        weekend = weekday >= 5
        offset = self.offset(day)
        md = (day.month, day.day)

        if period == PERIOD_FREE:
            return FREE if wed_fri else None
        if period == PERIOD_CHEESEFARE:
            return DAIRY
        if period == PERIOD_PENTECOSTARION:
            return FISH if wed_fri else None
        if period == PERIOD_LENT:
            if offset in (-48, -47, -6, -5, -4):
                return BREAD_WATER
            if offset == OFFSET_PALM_SUNDAY:
                return FISH
            if offset in (-17, -8, -3, -1):
                return OIL
            if offset == -2:
                return POST_NEGRU
            return OIL if weekend else POST
        if period == PERIOD_APOSTLES or period == PERIOD_NATIVITY_2:
            if weekend:
                return FISH
            return OIL if weekday in (1, 3) else POST
        if period in (PERIOD_DORMITION, PERIOD_NATIVITY_1):
            return OIL if weekend else POST
        if period == PERIOD_NATIVITY_3:
            if weekend:
                return OIL
            if md == (12, 24) or self._is_royal_hours_friday(day, 12, 25):
                return WHEAT
            return POST
        # Ordinary time
        if md == (1, 5):
            return POST if weekend else POST_NEGRU
        if md in ((8, 29), (9, 14)):
            return OIL
        return POST if wed_fri else None

    @staticmethod
    def _is_royal_hours_friday(day: date, month: int, dom: int) -> bool:
        """Friday before a feast that falls on Sunday or Monday."""
        if day.weekday() != 4:
            return False
        feast = date(day.year, month, dom)
        return feast.weekday() in (6, 0) and 0 < (feast - day).days <= 3

    def fasting(self, day: date) -> str | None:
        """Final fasting rule, with feast exceptions applied."""
        base = self.base_fasting(day)
        if self.offset(day) in STRICT_OFFSETS or base == WHEAT:
            return base
        relax = self._menaion.get(self.menaion_key(day), {}).get("fast", {})
        group = (
            "wf" if day.weekday() in (2, 4) else "we" if day.weekday() >= 5 else "wd"
        )
        candidate = relax.get(group)
        if candidate is not None and FAST_LEVEL[candidate] > FAST_LEVEL[base]:
            return candidate
        return base

    # ------------------------------------------------------------------ notes

    def _fast_boundaries(self, year: int) -> dict[date, str]:
        """'Lăsatul secului' and 'Începutul Postului' notes for the fixed-start fasts."""
        result: dict[date, str] = {}
        for start, name in (
            (self.apostles_fast_start(year), FAST_PERIOD_NAMES[PERIOD_APOSTLES]),
            (date(year, 8, 1), FAST_PERIOD_NAMES[PERIOD_DORMITION]),
            (date(year, 11, 15), FAST_PERIOD_NAMES[PERIOD_NATIVITY_1]),
        ):
            last = start - timedelta(days=1)
            while last.weekday() in (2, 4):
                last -= timedelta(days=1)
            result[last] = f"Lăsatul secului pentru Postul {name}"
            result[last + timedelta(days=1)] = f"Începutul Postului {name}"
        return result

    def _rule_notes(self, day: date) -> list[str]:
        notes: list[str] = []
        md = (day.month, day.day)
        offset = self.offset(day)

        boundary = self._fast_boundaries(day.year).get(day)
        if boundary:
            notes.append(boundary)

        if day.weekday() == 5:
            saturdays = (
                ((1, 1), (1, 5), "Sâmbăta dinaintea Botezului Domnului"),
                ((1, 7), (1, 13), "Sâmbăta după Botezul Domnului"),
                ((9, 7), (9, 13), "Sâmbăta dinaintea Înălțării Sf. Cruci"),
                ((9, 15), (9, 21), "Sâmbăta după Înălțarea Sf. Cruci"),
                ((12, 18), (12, 24), "Sâmbăta dinaintea Nașterii Domnului"),
                ((12, 26), (12, 31), "Sâmbăta după Nașterea Domnului"),
            )
            for first, last, text in saturdays:
                if first <= md <= last:
                    notes.append(text)
            # Saturday before St. Michael and Gabriel (8 November).
            if (11, 1) <= md <= (11, 7):
                notes.append("Pomenirea morților - Moşii de toamnă")

        # Akathist vigil: Friday of the 5th week of Lent, unless the Akathist
        # Saturday is the Annunciation itself.
        easter = self.easter(day.year)
        akathist = -14 if easter - timedelta(days=15) == date(day.year, 3, 25) else -16
        if offset == akathist:
            notes.append("Denia Acatistului Bunei Vestiri")

        if self._is_royal_hours_friday(day, 12, 25) or self._is_royal_hours_friday(
            day, 1, 6
        ):
            notes.append(ALITURGICAL)
        return notes

    # ------------------------------------------------------------------ Sundays

    def _sunday_number(self, day: date) -> int | None:
        """Number of the Sunday 'after Pentecost' whose readings are used."""
        year = day.year
        easter = self.easter(year)
        offset = (day - easter).days

        before_exaltation = _sunday_in(year, 9, 7, 13)
        after_exaltation = _sunday_in(year, 9, 15, 21)
        after_theophany = _sunday_in(year, 1, 7, 13)
        before_nativity = _sunday_in(year, 12, 18, 24)

        if OFFSET_ALL_SAINTS <= offset and day < before_exaltation:
            return (offset - OFFSET_PENTECOST) // 7

        if after_exaltation < day < before_nativity:
            week = (day - after_exaltation).days // 7
            if week in (3, 4):
                # The parable of the sower (21st) is read on the Sunday of the
                # Fathers of the 7th Ecumenical Council (11-17 October).
                synod = 11 <= day.day <= 17 and day.month == 10
                other = day + timedelta(days=7 if week == 3 else -7)
                other_synod = 11 <= other.day <= 17 and other.month == 10
                if synod:
                    return 21
                if other_synod:
                    return 20
            if week <= 4:
                return 17 + week
            if week == 5:
                return 23
            if week in (6, 7):
                # The rich man and Lazarus is read on the Sunday between 30 Oct and 5 Nov.
                return 22 if (10, 30) <= (day.month, day.day) <= (11, 5) else 24
            if week in (8, 9):
                return 17 + week
            if week == 10:
                return 30
            if 4 <= day.day <= 10 and day.month == 12:
                return 27
            if 11 <= day.day <= 17 and day.month == 12:
                return 28
            # Extra Sunday at the start of December: the next Luke reading
            # (the blind man of Jericho).
            return 31

        triodion = easter - timedelta(days=70)
        if after_theophany < day < triodion:
            total = (triodion - after_theophany).days // 7 - 1
            index = (day - after_theophany).days // 7 - 1
            sequence = WINTER_SUNDAYS.get(total)
            if sequence:
                return sequence[index]
        return None

    def _sunday(self, day: date, key: str) -> SundayInfo | None:
        if day.weekday() != 6:
            return None
        year = day.year
        easter = self.easter(year)
        offset = (day - easter).days
        md = (day.month, day.day)
        entry: dict[str, Any] | None = None
        use_prefix = True

        tri = self._triodion.get(offset, {})
        if "sunday" in tri:
            entry = tri["sunday"]
        elif f"feast:{key[:5]}" in self._sundays:
            entry = self._sundays[f"feast:{key[:5]}"]
            use_prefix = False
        elif (1, 1) <= md <= (1, 5):
            entry = self._sundays["before_theophany"]
        elif (1, 7) <= md <= (1, 13):
            entry = self._sundays["after_theophany"]
        elif (9, 7) <= md <= (9, 13):
            entry = self._sundays["before_exaltation"]
        elif (9, 15) <= md <= (9, 21):
            entry = self._sundays["after_exaltation"]
        elif (12, 18) <= md <= (12, 24):
            entry = self._sundays["before_nativity"]
        elif (12, 26) <= md <= (12, 31):
            entry = self._sundays["after_nativity"]
        else:
            number = self._sunday_number(day)
            if number is not None:
                entry = self._sundays.get(str(number))

        if entry is None:
            return None

        subtitle = entry.get("subtitle")
        synod = SYNOD_SUBTITLES.get(day.month)
        if synod and synod[0][0] <= day.day <= synod[0][1] and subtitle:
            subtitle = f"({synod[1]}; {subtitle.strip('()')}; Rugăciunea lui Iisus)"

        prefix = (
            self._menaion.get(key, {}).get("sunday_prefix", {}) if use_prefix else {}
        )
        apostle = _join_readings(prefix.get("apostle"), entry.get("apostle"), "Ap.")
        gospel = _join_readings(prefix.get("gospel"), entry.get("gospel"), "Ev.")

        tone = eothinon = None
        if offset not in (OFFSET_PALM_SUNDAY, OFFSET_EASTER, OFFSET_PENTECOST):
            cycle_easter = easter if day >= easter else self.easter(year - 1)
            weeks = (day - (cycle_easter + timedelta(days=7))).days // 7
            tone = weeks % 8 + 1
            if offset in PENTECOSTARION_EOTHINA:
                eothinon = PENTECOSTARION_EOTHINA[offset]
            else:
                weeks = (
                    day - (cycle_easter + timedelta(days=OFFSET_ALL_SAINTS))
                ).days // 7
                eothinon = weeks % 11 + 1
        return SundayInfo(
            entry.get("title", ""), subtitle, apostle, gospel, tone, eothinon
        )

    # ------------------------------------------------------------------ moon

    @lru_cache(maxsize=64)
    def moon_phases(self, year: int) -> dict[date, str]:
        """Local dates of the principal moon phases of a year."""
        result: dict[date, str] = {}
        k_start = math.floor((year - 2000) * 12.3685) - 2
        for k in range(k_start, k_start + 16):
            for phase in range(4):
                moment = _moon_phase_utc(k + phase * 0.25, phase)
                local = moment.astimezone(self._tz).date()
                if local.year == year:
                    result[local] = MOON_PHASES[phase]
        return result

    # ------------------------------------------------------------------ day

    def _compute_day(self, day: date) -> OrthodoxCalendarDay:
        year = day.year
        easter = self.easter(year)
        offset = (day - easter).days
        key = self.menaion_key(day)
        fixed = self._menaion.get(key, {})
        tri = self._triodion.get(offset, {})

        fixed_saints = fixed.get("saints", "")
        romanian = list(fixed.get("romanian", []))
        red = bool(fixed.get("red"))

        # St. George moves to Bright Monday when it falls in Holy Week / on Easter.
        george_day = date(year, *ST_GEORGE_DATE)
        george = self._menaion.get("04-23", {})
        george_item = george.get("saints", "").split("; ")[0]
        george_moved = (george_day - easter).days in ST_GEORGE_MOVE_OFFSETS
        if george_moved and (day.month, day.day) == ST_GEORGE_DATE:
            fixed_saints = "; ".join(fixed_saints.split("; ")[1:])
            red = False

        if "replace" in tri:
            saints = tri["replace"]
            romanian = []
        else:
            parts = [tri.get("prefix")]
            if offset == OFFSET_BRIGHT_MONDAY and george_moved:
                parts.append(george_item)
            parts.append(fixed_saints)
            saints = "; ".join(p for p in parts if p)

        red = red or bool(tri.get("red")) or day.weekday() == 6

        notes = (
            list(fixed.get("notes", []))
            + list(tri.get("notes", []))
            + self._rule_notes(day)
        )

        period = self.period(day)
        fasting = self.fasting(day)
        no_weddings = (
            period in FASTING_PERIODS
            or (day.weekday() in (2, 4) and period != PERIOD_FREE)
            or bool(fixed.get("no_weddings"))
            or bool(tri.get("no_weddings"))
        )

        return OrthodoxCalendarDay(
            date=day,
            saints=saints,
            romanian_saints=romanian,
            red=red,
            notes=notes,
            fasting=fasting,
            fasting_period=period,
            no_weddings=no_weddings,
            sunday=self._sunday(day, key),
            moon_phase=self.moon_phases(year).get(day),
        )

    def clear_cache(self) -> None:
        """Forget cached days and moon phases."""
        self.day.cache_clear()  # type: ignore[attr-defined]
        OrthodoxCalendar.moon_phases.cache_clear()

    def next_day(
        self,
        start: date,
        predicate: Callable[[OrthodoxCalendarDay], bool],
        limit: int = 400,
    ) -> OrthodoxCalendarDay | None:
        """First day on or after start that matches the predicate."""
        for index in range(limit):
            info = self.day(start + timedelta(days=index))
            if predicate(info):
                return info
        return None

    def days(self, start: date, end: date) -> list[OrthodoxCalendarDay]:
        """All days from start to end (inclusive)."""
        result = []
        current = start
        while current <= end:
            result.append(self.day(current))
            current += timedelta(days=1)
        return result


def _moon_phase_utc(k: float, phase: int) -> datetime:
    """Moment of a moon phase (Meeus, Astronomical Algorithms, chapter 49)."""
    rad = math.radians
    t = k / 1236.85
    jde = (
        2451550.09766
        + 29.530588861 * k
        + 0.00015437 * t**2
        - 0.000000150 * t**3
        + 0.00000000073 * t**4
    )
    e = 1 - 0.002516 * t - 0.0000074 * t**2
    m = rad(2.5534 + 29.10535670 * k - 0.0000014 * t**2 - 0.00000011 * t**3)
    mp = rad(
        201.5643
        + 385.81693528 * k
        + 0.0107582 * t**2
        + 0.00001238 * t**3
        - 0.000000058 * t**4
    )
    f = rad(
        160.7108
        + 390.67050284 * k
        - 0.0016118 * t**2
        - 0.00000227 * t**3
        + 0.000000011 * t**4
    )
    om = rad(124.7746 - 1.56375588 * k + 0.0020672 * t**2 + 0.00000215 * t**3)

    if phase in (0, 2):
        if phase == 0:
            coeffs = [
                -0.40720,
                0.17241 * e,
                0.01608,
                0.01039,
                0.00739 * e,
                -0.00514 * e,
                0.00208 * e * e,
            ]
        else:
            coeffs = [
                -0.40614,
                0.17302 * e,
                0.01614,
                0.01043,
                0.00734 * e,
                -0.00515 * e,
                0.00209 * e * e,
            ]
        coeffs += [
            -0.00111,
            -0.00057,
            0.00056 * e,
            -0.00042,
            0.00042 * e,
            0.00038 * e,
            -0.00024 * e,
            -0.00017,
            -0.00007,
            0.00004,
            0.00004,
            0.00003,
            0.00003,
            -0.00003,
            0.00003,
            -0.00002,
            -0.00002,
            0.00002,
        ]
        args = [
            mp,
            m,
            2 * mp,
            2 * f,
            mp - m,
            mp + m,
            2 * m,
            mp - 2 * f,
            mp + 2 * f,
            2 * mp + m,
            3 * mp,
            m + 2 * f,
            m - 2 * f,
            2 * mp - m,
            om,
            mp + 2 * m,
            2 * mp - 2 * f,
            3 * m,
            mp + m - 2 * f,
            2 * mp + 2 * f,
            mp + m + 2 * f,
            mp - m + 2 * f,
            mp - m - 2 * f,
            3 * mp + m,
            4 * mp,
        ]
        jde += sum(c * math.sin(a) for c, a in zip(coeffs, args))
    else:
        coeffs = [
            -0.62801,
            0.17172 * e,
            -0.01183 * e,
            0.00862,
            0.00804,
            0.00454 * e,
            0.00204 * e * e,
            -0.00180,
            -0.00070,
            -0.00040,
            -0.00034 * e,
            0.00032 * e,
            0.00032 * e,
            -0.00028 * e * e,
            0.00027 * e,
            -0.00017,
            -0.00005,
            0.00004,
            -0.00004,
            0.00004,
            0.00003,
            0.00003,
            0.00002,
            0.00002,
            -0.00002,
        ]
        args = [
            mp,
            m,
            mp + m,
            2 * mp,
            2 * f,
            mp - m,
            2 * m,
            mp - 2 * f,
            mp + 2 * f,
            3 * mp,
            2 * mp - m,
            m + 2 * f,
            m - 2 * f,
            mp + 2 * m,
            2 * mp + m,
            om,
            mp - m - 2 * f,
            2 * mp + 2 * f,
            mp + m + 2 * f,
            mp - 2 * m,
            mp + m - 2 * f,
            3 * m,
            2 * mp - 2 * f,
            mp - m + 2 * f,
            3 * mp + m,
        ]
        jde += sum(c * math.sin(a) for c, a in zip(coeffs, args))
        w = (
            0.00306
            - 0.00038 * e * math.cos(m)
            + 0.00026 * math.cos(mp)
            - 0.00002 * math.cos(mp - m)
            + 0.00002 * math.cos(mp + m)
            + 0.00002 * math.cos(2 * f)
        )
        jde += w if phase == 1 else -w

    planetary = [
        (0.000325, 299.77 + 0.107408 * k - 0.009173 * t**2),
        (0.000165, 251.88 + 0.016321 * k),
        (0.000164, 251.83 + 26.651886 * k),
        (0.000126, 349.42 + 36.412478 * k),
        (0.000110, 84.66 + 18.206239 * k),
        (0.000062, 141.74 + 53.303771 * k),
        (0.000060, 207.14 + 2.453732 * k),
        (0.000056, 154.84 + 7.306860 * k),
        (0.000047, 34.52 + 27.261239 * k),
        (0.000042, 207.19 + 0.121824 * k),
        (0.000040, 291.34 + 1.844379 * k),
        (0.000037, 161.72 + 24.198154 * k),
        (0.000035, 239.56 + 25.513099 * k),
        (0.000023, 331.55 + 3.592518 * k),
    ]
    jde += sum(c * math.sin(rad(a)) for c, a in planetary)
    # Terrestrial time is about a minute ahead of UTC; close enough for a date.
    return datetime(2000, 1, 1, 12, tzinfo=timezone.utc) + timedelta(
        days=jde - 2451545.0, seconds=-69
    )
