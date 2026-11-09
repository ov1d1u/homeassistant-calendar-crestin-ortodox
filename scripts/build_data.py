#!/usr/bin/env python3
"""Build the integration's bundled calendar data from noutati-ortodoxe.ro.

Development tool only. It reads the yearly calendar pages saved in
``tests/fixtures/site`` and writes three files used by the offline engine:

* ``data/menaion.json``  - per calendar date: saints, red-letter flag, notes,
  fasting exceptions, no-weddings flag and readings added on Sundays.
* ``data/triodion.json`` - per day offset from Easter: movable feasts, notes,
  red-letter flag, no-weddings flag and the Sunday title/readings.
* ``data/sundays.json``  - titles and readings for the Sundays that do not
  depend on Easter directly (after Pentecost, around the great feasts).

Everything the engine computes by rule (weekday fasting, special Saturdays,
fast boundaries, ...) is removed first, so only the irregular part is stored.

Usage:
    python scripts/build_data.py              # use saved pages
    python scripts/build_data.py --download   # fetch missing years first
"""
from __future__ import annotations

import argparse
import collections
import json
import re
import sys
import time
import urllib.request
from datetime import date
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from engine_loader import COMPONENT, FIXTURES, load_engine  # noqa: E402
from site_parser import parse_year  # noqa: E402

URL = "https://www.noutati-ortodoxe.ro/calendar-ortodox/?year={year}"
# The site generates these years from its current data set (the years before
# 2027 were edited by hand or use older data).
SOURCE_YEARS = list(range(2027, 2038))
# Older years: only used to fill gaps in Sunday readings (dates that never
# fall on a Sunday in the source years).
SECONDARY_YEARS = list(range(2021, 2027))

NAMED_SUNDAYS = {
    "Duminica dinaintea Botezului Domnului": "before_theophany",
    "Duminica după Botezul Domnului": "after_theophany",
    "Duminica dinaintea Înălțării Sf. Cruci": "before_exaltation",
    "Duminica după Înălțarea Sf. Cruci": "after_exaltation",
    "Duminica dinaintea Nașterii Domnului": "before_nativity",
    "Duminica după Nașterea Domnului": "after_nativity",
}

ROMAN = {"I": 1, "V": 5, "X": 10, "L": 50}


def roman_to_int(text: str) -> int:
    total = 0
    for i, char in enumerate(text):
        value = ROMAN[char]
        if i + 1 < len(text) and ROMAN[text[i + 1]] > value:
            total -= value
        else:
            total += value
    return total


def sunday_number(title: str) -> int | None:
    match = re.fullmatch(r"Duminica (?:a )?([IVXL]+)(?:-a)? după Rusalii", title)
    return roman_to_int(match.group(1)) if match else None


def strip_synod(subtitle: str | None) -> str | None:
    if subtitle and "Sinodul" in subtitle and "Rugăciunea lui Iisus" in subtitle:
        inner = subtitle.strip("()").split("; ")
        if inner[0].startswith("a Sf. Părin") and inner[-1] == "Rugăciunea lui Iisus":
            return "(" + "; ".join(inner[1:-1]) + ")"
    return subtitle


def strip_label(text: str | None, label: str) -> str | None:
    if text is None:
        return None
    prefix = label + " "
    return text.removeprefix(prefix)


def is_leap(year: int) -> bool:
    return year % 4 == 0 and (year % 100 != 0 or year % 400 == 0)


def menaion_key(day: date) -> str:
    key = f"{day.month:02d}-{day.day:02d}"
    return key + "L" if key == "02-28" and is_leap(day.year) else key


def mode(counter: collections.Counter):
    return counter.most_common(1)[0][0]


def download(years: list[int], directory: Path) -> None:
    directory.mkdir(parents=True, exist_ok=True)
    for year in years:
        path = directory / f"calendar_{year}.html"
        if path.exists():
            continue
        print(f"Downloading {year}...")
        request = urllib.request.Request(
            URL.format(year=year), headers={"User-Agent": "Mozilla/5.0"}
        )
        with urllib.request.urlopen(request, timeout=60) as response:
            path.write_bytes(response.read())
        time.sleep(1)


def load_observations(years: list[int], fixtures: Path) -> list:
    observations = []
    for year in years:
        path = fixtures / f"calendar_{year}.html"
        if not path.exists():
            continue
        for day, info in sorted(
            parse_year(path.read_text(encoding="utf-8"), year).items()
        ):
            observations.append((day, info))
    return observations


def build(
    years: list[int], fixtures: Path, secondary_years: list[int] = ()
) -> dict[str, dict]:
    engine = load_engine()
    cal = engine.OrthodoxCalendar(data={"menaion": {}, "triodion": {}, "sundays": {}})
    observations = load_observations(years, fixtures)
    secondary = load_observations(list(secondary_years), fixtures)

    def offset(day: date) -> int:
        return cal.offset(day)

    def george_moved(day: date) -> bool:
        return (day.month, day.day) == engine.ST_GEORGE_DATE and offset(
            day
        ) in engine.ST_GEORGE_MOVE_OFFSETS

    # ------------------------------------------------------------------ saints
    def movable_offsets(fixed: dict[str, str]) -> dict[int, tuple[str, str]]:
        found: dict[int, collections.Counter] = collections.defaultdict(
            collections.Counter
        )
        for day, info in observations:
            base = fixed[menaion_key(day)]
            text = info.saints
            if text == base:
                found[offset(day)][None] += 1
            elif text == "":
                found[offset(day)][("replace", "")] += 1
            elif base and text.endswith("; " + base):
                found[offset(day)][("prefix", text[: -len(base) - 2])] += 1
            else:
                found[offset(day)][("other", text)] += 1
        result = {}
        for off, counter in found.items():
            value, count = counter.most_common(1)[0]
            total = sum(counter.values())
            if value is None:
                continue
            if value[0] == "other":
                if count >= 0.8 * total:
                    result[off] = ("replace", value[1])
            elif count >= 0.5 * total:
                result[off] = value
        return result

    by_key: dict[str, collections.Counter] = collections.defaultdict(
        collections.Counter
    )
    for day, info in observations:
        by_key[menaion_key(day)][info.saints] += 1
    fixed = {key: mode(counter) for key, counter in by_key.items()}

    for _ in range(2):
        movable = movable_offsets(fixed)
        clean_counts: dict[str, collections.Counter] = collections.defaultdict(
            collections.Counter
        )
        for day, info in observations:
            off = offset(day)
            if off in movable or george_moved(day):
                continue
            clean_counts[menaion_key(day)][info.saints] += 1
        for key in fixed:
            if clean_counts.get(key):
                fixed[key] = mode(clean_counts[key])
    movable = movable_offsets(fixed)

    romanian: dict[str, collections.Counter] = collections.defaultdict(
        collections.Counter
    )
    for day, info in observations:
        if info.saints == fixed[menaion_key(day)] or info.saints.endswith(
            "; " + fixed[menaion_key(day)]
        ):
            romanian[menaion_key(day)][tuple(info.romanian)] += 1

    menaion: dict[str, dict] = {key: {"saints": fixed[key]} for key in sorted(fixed)}
    for key, counter in romanian.items():
        if mode(counter):
            menaion[key]["romanian"] = list(mode(counter))

    triodion: dict[int, dict] = collections.defaultdict(dict)
    for off, (kind, text) in movable.items():
        triodion[off][kind] = text

    # ------------------------------------------------------------------ red letter days
    date_red: dict[str, collections.Counter] = collections.defaultdict(
        collections.Counter
    )
    for day, info in observations:
        if day.weekday() != 6 and offset(day) not in movable and not george_moved(day):
            date_red[menaion_key(day)][info.is_red] += 1
    for key, counter in date_red.items():
        if mode(counter):
            menaion[key]["red"] = True
    offset_red: dict[int, collections.Counter] = collections.defaultdict(
        collections.Counter
    )
    for day, info in observations:
        if (
            day.weekday() == 6 and triodion.get(offset(day), {}).get("replace") != ""
        ) or menaion.get(menaion_key(day), {}).get("red"):
            continue
        offset_red[offset(day)][info.is_red] += 1
    for off, counter in offset_red.items():
        if -80 <= off <= 63 and counter[True] >= 0.8 * sum(counter.values()):
            triodion[off]["red"] = True

    # ------------------------------------------------------------------ notes
    key_years = collections.Counter(menaion_key(day) for day, _ in observations)
    off_years = collections.Counter(offset(day) for day, _ in observations)
    date_notes: dict[str, collections.Counter] = collections.defaultdict(
        collections.Counter
    )
    off_notes: dict[int, collections.Counter] = collections.defaultdict(
        collections.Counter
    )
    note_order: dict[str, int] = {}
    for day, info in observations:
        rule_notes = cal._rule_notes(day)
        for note in info.comments:
            if note in engine.FAST_LEVEL or note in rule_notes:
                continue
            note_order.setdefault(note, len(note_order))
            date_notes[menaion_key(day)][note] += 1
            off_notes[offset(day)][note] += 1
    for off, counter in off_notes.items():
        notes = [
            n
            for n, c in counter.items()
            if c >= 0.7 * off_years[off] and c >= 3 and -80 <= off <= 63
        ]
        if notes:
            triodion[off]["notes"] = sorted(notes, key=note_order.get)
    for key, counter in date_notes.items():
        notes = []
        for note, count in counter.items():
            # Ignore occurrences already explained by the Easter cycle.
            explained = sum(
                1
                for day, info in observations
                if menaion_key(day) == key
                and note in info.comments
                and note in triodion.get(offset(day), {}).get("notes", [])
            )
            if count - explained >= max(2, 0.7 * key_years[key]):
                notes.append(note)
        if notes:
            menaion[key]["notes"] = sorted(notes, key=note_order.get)

    # ------------------------------------------------------------------ fasting exceptions
    def find_relaxations(source) -> dict[str, dict[str, str]]:
        found: dict[str, dict[str, str]] = collections.defaultdict(dict)
        for day, info in source:
            observed = next((c for c in info.comments if c in engine.FAST_LEVEL), None)
            base = cal.base_fasting(day)
            if offset(day) in engine.STRICT_OFFSETS or base == engine.WHEAT:
                continue
            if (
                observed != base
                and engine.FAST_LEVEL[observed] > engine.FAST_LEVEL[base]
            ):
                group = (
                    "wf"
                    if day.weekday() in (2, 4)
                    else "we" if day.weekday() >= 5 else "wd"
                )
                current = found[menaion_key(day)].get(group)
                if (
                    current is None
                    or engine.FAST_LEVEL[observed] > engine.FAST_LEVEL[current]
                ):
                    found[menaion_key(day)][group] = observed
        return found

    # Older years are not used here: their fasting rules differ.
    relax = find_relaxations(observations)
    # A feast that relaxes the fast on some weekdays relaxes it on the others too:
    # fish on weekdays means oil and wine on Wednesday/Friday, and vice versa.
    for groups in relax.values():
        if (
            "wd" in groups
            and "wf" not in groups
            and groups["wd"] in (engine.OIL, engine.FISH)
        ):
            groups["wf"] = engine.OIL
        if (
            "wf" in groups
            and "wd" not in groups
            and groups["wf"] in (engine.OIL, engine.FISH)
        ):
            groups["wd"] = groups["wf"]
    for key, value in relax.items():
        if value:
            menaion[key]["fast"] = dict(sorted(value.items()))

    # ------------------------------------------------------------------ no weddings
    def wedding_rule(day: date) -> bool:
        period = cal.period(day)
        return period in engine.FASTING_PERIODS or (
            day.weekday() in (2, 4) and period != engine.PERIOD_FREE
        )

    off_nw: dict[int, collections.Counter] = collections.defaultdict(
        collections.Counter
    )
    for day, info in observations:
        if not wedding_rule(day):
            off_nw[offset(day)][info.no_weddings] += 1
    for off, counter in off_nw.items():
        if -80 <= off <= 63 and counter[True] >= 3 and counter[False] == 0:
            triodion[off]["no_weddings"] = True
    date_nw: dict[str, collections.Counter] = collections.defaultdict(
        collections.Counter
    )
    for day, info in observations:
        if not wedding_rule(day) and not triodion.get(offset(day), {}).get(
            "no_weddings"
        ):
            date_nw[menaion_key(day)][info.no_weddings] += 1
    for key, counter in date_nw.items():
        if counter[True] >= 3 and counter[False] == 0:
            menaion[key]["no_weddings"] = True

    # ------------------------------------------------------------------ Sundays
    def entry_of(sunday) -> tuple:
        return (
            sunday.title,
            sunday.subtitle,
            strip_label(sunday.apostle, "Ap."),
            strip_label(sunday.gospel, "Ev."),
        )

    tri_sundays: dict[int, collections.Counter] = collections.defaultdict(
        collections.Counter
    )
    other_sundays: dict[str, collections.Counter] = collections.defaultdict(
        collections.Counter
    )
    secondary_feasts: dict[str, collections.Counter] = collections.defaultdict(
        collections.Counter
    )
    for day, info in secondary:
        title = info.sunday.title if info.sunday else None
        if title is not None and (title == "" or title.startswith("(†) Duminica")):
            secondary_feasts[f"feast:{day.month:02d}-{day.day:02d}"][
                entry_of(info.sunday)
            ] += 1
    for day, info in observations:
        if info.sunday is None:
            continue
        off = offset(day)
        title = info.sunday.title
        if -70 <= off <= engine.OFFSET_ALL_SAINTS:
            tri_sundays[off][entry_of(info.sunday)] += 1
        elif title == "" or title.startswith("(†) Duminica"):
            other_sundays[f"feast:{day.month:02d}-{day.day:02d}"][
                entry_of(info.sunday)
            ] += 1
        elif title in NAMED_SUNDAYS:
            other_sundays[NAMED_SUNDAYS[title]][entry_of(info.sunday)] += 1
        elif (number := sunday_number(title)) is not None:
            t, sub, ap, ev = entry_of(info.sunday)
            other_sundays[str(number)][(t, strip_synod(sub), ap, ev)] += 1
        else:
            print(f"warning: unknown Sunday title {title!r} on {day}")

    def as_entry(value: tuple) -> dict:
        title, subtitle, apostle, gospel = value
        entry = {"title": title}
        if subtitle:
            entry["subtitle"] = subtitle
        if apostle:
            entry["apostle"] = apostle
        if gospel:
            entry["gospel"] = gospel
        return entry

    for off, counter in tri_sundays.items():
        triodion[off]["sunday"] = as_entry(mode(counter))
    sundays = {key: as_entry(mode(counter)) for key, counter in other_sundays.items()}
    for key, counter in secondary_feasts.items():
        sundays.setdefault(key, as_entry(mode(counter)))

    # Readings added when a Sunday falls on a fixed feast.
    partial = engine.OrthodoxCalendar(
        data={
            "menaion": menaion,
            "triodion": {str(k): v for k, v in triodion.items()},
            "sundays": sundays,
        }
    )

    def find_prefixes(source) -> dict[str, collections.Counter]:
        found: dict[str, collections.Counter] = collections.defaultdict(
            collections.Counter
        )
        for day, info in source:
            if info.sunday is None:
                continue
            prefix = sunday_prefix(day, info)
            if prefix:
                found[menaion_key(day)][prefix] += 1
        return found

    def sunday_prefix(day, info):
        computed = partial._sunday(day, menaion_key(day))
        if computed is None:
            return None
        found = []
        for observed, base, label in (
            (info.sunday.apostle, computed.apostle, "Ap."),
            (info.sunday.gospel, computed.gospel, "Ev."),
        ):
            observed = strip_label(observed, label)
            base = strip_label(base, label)
            if (
                observed
                and base
                and observed != base
                and observed.endswith("; " + base)
            ):
                found.append(observed[: -len(base) - 2])
            else:
                found.append(None)
        return tuple(found) if any(found) else None

    prefixes = find_prefixes(observations)
    for key, counter in find_prefixes(secondary).items():
        prefixes.setdefault(key, counter)
    for key, counter in prefixes.items():
        apostle, gospel = mode(counter)
        prefix = {}
        if apostle:
            prefix["apostle"] = apostle
        if gospel:
            prefix["gospel"] = gospel
        menaion[key]["sunday_prefix"] = prefix

    # Sundays 33 and 34 always fall in the Triodion and are stored there.
    missing = [n for n in range(2, 33) if str(n) not in sundays]
    if missing:
        print(f"warning: no data for Sundays after Pentecost {missing}")

    return {
        "menaion": menaion,
        "triodion": {str(k): triodion[k] for k in sorted(triodion)},
        "sundays": dict(
            sorted(
                sundays.items(), key=lambda kv: (not kv[0].isdigit(), kv[0].zfill(3))
            )
        ),
    }


def main() -> None:
    parser = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter
    )
    parser.add_argument(
        "--fixtures",
        type=Path,
        default=FIXTURES,
        help="directory with calendar_YYYY.html",
    )
    parser.add_argument(
        "--output", type=Path, default=COMPONENT / "data", help="output directory"
    )
    parser.add_argument(
        "--download", action="store_true", help="download missing source years first"
    )
    args = parser.parse_args()

    if args.download:
        download(SOURCE_YEARS, args.fixtures)

    data = build(SOURCE_YEARS, args.fixtures, SECONDARY_YEARS)
    args.output.mkdir(parents=True, exist_ok=True)
    for name, content in data.items():
        path = args.output / f"{name}.json"
        path.write_text(
            json.dumps(content, ensure_ascii=False, indent=1) + "\n", encoding="utf-8"
        )
        print(f"wrote {path} ({len(content)} entries)")


if __name__ == "__main__":
    main()
