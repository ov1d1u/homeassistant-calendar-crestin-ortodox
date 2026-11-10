"""Calendar platform for Calendar Ortodox integration."""

from __future__ import annotations

from datetime import date, datetime, timedelta
import logging
from typing import Any

from homeassistant.components.calendar import CalendarEntity, CalendarEvent
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity
from homeassistant.util import dt as dt_util

from . import CalendarOrtodoxDataUpdateCoordinator
from .const import (
    ATTR_COMMENTS,
    ATTR_FASTING,
    ATTR_FASTING_DESCRIPTION,
    ATTR_FEAST_DAY,
    ATTR_FEAST_LEVEL,
    ATTR_NO_WEDDINGS,
    ATTR_NOTES,
    ATTR_READINGS,
    ATTR_SAINTS,
    CONF_INCLUDE_FASTING,
    CONF_INCLUDE_READINGS,
    CONF_LANGUAGE,
    DOMAIN,
    FASTING_TRANSLATIONS,
    FEAST_LEVEL_GREAT,
    FEAST_LEVEL_MAJOR,
    NEXT_FEAST_LOOKAHEAD_DAYS,
)
from .engine import OrthodoxCalendarDay

_LOGGER = logging.getLogger(__name__)

# Guard against very large ranges requested by API clients.
MAX_RANGE_DAYS = 3 * 366


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up Calendar Ortodox calendar platform."""
    coordinator: CalendarOrtodoxDataUpdateCoordinator = hass.data[DOMAIN][
        entry.entry_id
    ]
    async_add_entities(
        [
            OrthodoxCalendar(coordinator, entry),
            OrthodoxFeastDaysCalendar(coordinator, entry),
        ]
    )


def fasting_text(day_info: OrthodoxCalendarDay, language: str) -> str:
    """Fasting rules of a day as text."""
    items = day_info.fasting_info
    if language == "en":
        items = [FASTING_TRANSLATIONS.get(item, item) for item in items]
    return " | ".join(items)


class _BaseOrthodoxCalendar(
    CoordinatorEntity[CalendarOrtodoxDataUpdateCoordinator], CalendarEntity
):
    """Shared logic for both calendars."""

    _attr_has_entity_name = False

    def __init__(
        self, coordinator: CalendarOrtodoxDataUpdateCoordinator, entry: ConfigEntry
    ) -> None:
        super().__init__(coordinator)
        self._entry = entry

    def _option(self, key: str, default: Any) -> Any:
        return self._entry.options.get(key, self._entry.data.get(key, default))

    def _include(self, day_info: OrthodoxCalendarDay) -> bool:
        raise NotImplementedError

    def _summary(self, day_info: OrthodoxCalendarDay) -> str:
        if day_info.feast_level == FEAST_LEVEL_GREAT:
            return f"🌟 {day_info.title}"
        return day_info.title

    def _description(self, day_info: OrthodoxCalendarDay) -> str:
        include_fasting = self._option(CONF_INCLUDE_FASTING, True)
        include_readings = self._option(CONF_INCLUDE_READINGS, True)
        language = self._option(CONF_LANGUAGE, "ro")
        parts: list[str] = []

        if day_info.feast_level == FEAST_LEVEL_GREAT:
            parts.append("🌟 Praznic Mare")
        elif day_info.feast_level == FEAST_LEVEL_MAJOR:
            parts.append("✝️ Sărbătoare")

        if include_fasting and day_info.fasting_info:
            parts.append(f"Post: {fasting_text(day_info, language)}")
        if day_info.no_weddings:
            parts.append("Nu se fac nunți")

        notes = [n for n in day_info.notes if n not in day_info.fasting_info]
        if notes:
            parts.append("\n".join(notes))

        if day_info.sunday_title and day_info.sunday_title != day_info.title:
            parts.append(f"\n{day_info.sunday_title}")

        if include_readings and day_info.sunday_readings:
            readings = day_info.sunday_readings
            lines = [readings[key] for key in ("apostle", "gospel") if key in readings]
            if day_info.sunday and day_info.sunday.tone:
                tone = f"Glasul {day_info.sunday.tone}"
                if day_info.sunday.eothinon:
                    tone += f", voscresna {day_info.sunday.eothinon}"
                lines.append(tone)
            parts.append("\n" + "\n".join(lines))

        return "\n".join(parts) if parts else day_info.title

    def _create_event(self, day_info: OrthodoxCalendarDay) -> CalendarEvent:
        return CalendarEvent(
            start=day_info.date,
            end=day_info.date + timedelta(days=1),
            summary=self._summary(day_info),
            description=self._description(day_info),
        )

    async def async_get_events(
        self,
        hass: HomeAssistant,
        start_date: datetime,
        end_date: datetime,
    ) -> list[CalendarEvent]:
        """Return all events between two moments."""
        first = dt_util.as_local(start_date).date()
        last = dt_util.as_local(end_date - timedelta(microseconds=1)).date()
        if (last - first).days > MAX_RANGE_DAYS:
            last = first + timedelta(days=MAX_RANGE_DAYS)
        calendar = self.coordinator.calendar
        return [
            self._create_event(info)
            for info in calendar.days(first, last)
            if self._include(info)
        ]

    def _attributes(self, day_info: OrthodoxCalendarDay) -> dict[str, Any]:
        language = self._option(CONF_LANGUAGE, "ro")
        attrs: dict[str, Any] = {
            ATTR_SAINTS: day_info.title,
            ATTR_FEAST_DAY: day_info.feast_day,
            ATTR_FEAST_LEVEL: day_info.feast_level,
            ATTR_FASTING: day_info.is_fasting,
            ATTR_NO_WEDDINGS: day_info.no_weddings,
        }
        if day_info.fasting_info:
            attrs[ATTR_FASTING_DESCRIPTION] = fasting_text(day_info, language)
        if day_info.notes:
            attrs[ATTR_NOTES] = day_info.notes
        if day_info.sunday_readings:
            attrs[ATTR_READINGS] = day_info.sunday_readings
        if day_info.sunday_title:
            attrs[ATTR_COMMENTS] = day_info.sunday_title
        return attrs


class OrthodoxCalendar(_BaseOrthodoxCalendar):
    """Every day of the Orthodox calendar."""

    def __init__(
        self, coordinator: CalendarOrtodoxDataUpdateCoordinator, entry: ConfigEntry
    ) -> None:
        super().__init__(coordinator, entry)
        self._attr_name = "Calendar Ortodox"
        self._attr_unique_id = f"{entry.entry_id}_calendar"

    def _include(self, day_info: OrthodoxCalendarDay) -> bool:
        return True

    @property
    def _today(self) -> OrthodoxCalendarDay:
        return self.coordinator.calendar.day(self.coordinator.today)

    @property
    def event(self) -> CalendarEvent | None:
        """Today's event."""
        return self._create_event(self._today)

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        """Attributes for today."""
        return self._attributes(self._today)


class OrthodoxFeastDaysCalendar(_BaseOrthodoxCalendar):
    """Only feast days (sărbători)."""

    def __init__(
        self, coordinator: CalendarOrtodoxDataUpdateCoordinator, entry: ConfigEntry
    ) -> None:
        super().__init__(coordinator, entry)
        self._attr_name = "Calendar Ortodox - Sărbători"
        self._attr_unique_id = f"{entry.entry_id}_feast_days"

    def _include(self, day_info: OrthodoxCalendarDay) -> bool:
        return day_info.feast_level == FEAST_LEVEL_GREAT

    @property
    def _next_feast(self) -> OrthodoxCalendarDay | None:
        today: date = self.coordinator.today
        return self.coordinator.calendar.next_day(
            today, self._include, NEXT_FEAST_LOOKAHEAD_DAYS
        )

    @property
    def event(self) -> CalendarEvent | None:
        """The current or next feast day."""
        feast = self._next_feast
        return self._create_event(feast) if feast else None

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        """Attributes of the current or next feast day."""
        feast = self._next_feast
        if feast is None:
            return {}
        attrs = self._attributes(feast)
        attrs.pop(ATTR_FEAST_DAY, None)
        return attrs
