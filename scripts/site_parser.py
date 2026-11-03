"""Parser for the yearly calendar page of noutati-ortodoxe.ro.

Development tool only: used to build the bundled data files and to check
the offline engine against the site. It is not shipped with the integration.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from datetime import date
from pathlib import Path

from bs4 import BeautifulSoup, NavigableString

NO_WEDDINGS = "Nu se fac nunți"

_WS = re.compile(r"\s+")


def clean(text: str) -> str:
    """Collapse whitespace and tidy separators."""
    text = _WS.sub(" ", text.replace("\xa0", " ")).strip()
    text = re.sub(r"\s+([;,.])", r"\1", text)
    text = re.sub(r";(?=\S)", "; ", text)
    return text.strip(" ;")


def split_groups(text: str) -> list[str]:
    """Split '(A) (B)(C)' into ['A', 'B', 'C'], honouring nested parentheses."""
    groups: list[str] = []
    depth = 0
    buf = ""
    for char in text:
        if char == "(":
            if depth > 0:
                buf += char
            depth += 1
        elif char == ")":
            depth -= 1
            if depth > 0:
                buf += char
            elif depth == 0:
                groups.append(clean(buf))
                buf = ""
        elif depth > 0:
            buf += char
    if not groups and text.strip():
        groups.append(clean(text))
    return [g for g in groups if g]


@dataclass
class SiteSunday:
    """The extra row printed under a Sunday (or Easter-cycle feast)."""

    title: str
    subtitle: str | None
    apostle: str | None
    gospel: str | None
    tone: int | None
    eothinon: int | None


@dataclass
class SiteDay:
    """One parsed day."""

    date: date
    weekday: str
    classes: list[str]
    saints: str
    romanian: list[str] = field(default_factory=list)
    comments: list[str] = field(default_factory=list)
    no_weddings: bool = False
    moon: str | None = None
    sunday: SiteSunday | None = None

    @property
    def is_red(self) -> bool:
        """Whether the site marks the day as a holiday (red row)."""
        return "sarbatoare" in self.classes


def _parse_sunday_row(row) -> SiteSunday:
    cell = row.find("td")
    title_el = cell.find("span", class_="title")
    sub_el = cell.find("span", class_="subtitle")
    title = clean(title_el.get_text(" ")) if title_el else ""
    subtitle = clean(sub_el.get_text(" ")) if sub_el else None
    rest_parts = []
    for node in cell.children:
        if node in (title_el, sub_el):
            continue
        rest_parts.append(
            node if isinstance(node, NavigableString) else node.get_text(" ")
        )
    rest = clean("".join(rest_parts)).lstrip("; ").strip()
    tone = eothinon = None
    match = re.search(r";?\s*glas (\d+)(?:,\s*voscr\.\s*(\d+))?\s*$", rest)
    if match:
        tone = int(match.group(1))
        eothinon = int(match.group(2)) if match.group(2) else None
        rest = rest[: match.start()].strip(" ;")
    apostle = gospel = None
    match = re.match(r"^(Ap\..*?)(?:;\s*(Ev\..*))?$", rest)
    if match:
        apostle = clean(match.group(1))
        gospel = clean(match.group(2)) if match.group(2) else None
    elif rest.startswith("Ev."):
        gospel = clean(rest)
    return SiteSunday(title, subtitle, apostle, gospel, tone, eothinon)


def parse_year(html: str, year: int) -> dict[date, SiteDay]:
    """Parse a full year page."""
    soup = BeautifulSoup(html, "lxml")
    days: dict[date, SiteDay] = {}
    for month, div in enumerate(soup.find_all("div", class_="calendar"), start=1):
        for row in div.find_all("tr"):
            day_cell = row.find("td", class_="ziua")
            if day_cell is None:
                continue
            cells = row.find_all("td", recursive=False)
            content = cells[2] if len(cells) >= 3 else None
            if content is None:
                continue
            day = int(day_cell.get_text(strip=True))
            weekday = row.find("td", class_="sapt").get_text(strip=True)
            classes = [c.strip() for c in row.get("class", []) if c.strip()]

            link = content.find("a", class_="sinaxar")
            if link is not None:
                saints = clean(link.get_text(" "))
                rom = [
                    clean(s.get_text(" ")) for s in link.find_all("span", class_="rom")
                ]
            else:
                parts = []
                for node in content.children:
                    if isinstance(node, NavigableString):
                        parts.append(str(node))
                    elif node.name == "span" and set(node.get("class", [])) & {
                        "comentariu",
                        "next",
                    }:
                        continue
                    else:
                        parts.append(node.get_text(" "))
                saints = clean("".join(parts))
                rom = [
                    clean(s.get_text(" "))
                    for s in content.find_all("span", class_="rom")
                ]

            comments: list[str] = []
            no_weddings = False
            for span in content.find_all("span", class_="comentariu"):
                for group in split_groups(span.get_text(" ")):
                    if group.endswith(NO_WEDDINGS):
                        no_weddings = True
                        group = group[: -len(NO_WEDDINGS)].strip(" .")
                    if group:
                        comments.append(group)

            moon = None
            for img in content.find_all("img"):
                match = re.search(r"luna-(\d)\.png", img.get("src", ""))
                if match:
                    moon = int(match.group(1))

            sunday = None
            nxt = row.find_next_sibling("tr")
            if nxt is not None and "duminica" in [
                c.strip() for c in nxt.get("class", [])
            ]:
                sunday = _parse_sunday_row(nxt)

            current = date(year, month, day)
            days[current] = SiteDay(
                date=current,
                weekday=weekday,
                classes=classes,
                saints=saints,
                romanian=rom,
                comments=comments,
                no_weddings=no_weddings,
                moon=moon,
                sunday=sunday,
            )
    return days


def load_fixtures(directory: Path) -> dict[int, dict[date, SiteDay]]:
    """Load every calendar_YYYY.html file in a directory."""
    result = {}
    for path in sorted(directory.glob("calendar_*.html")):
        year = int(path.stem.split("_")[1])
        result[year] = parse_year(path.read_text(encoding="utf-8"), year)
    return result
