"""Sensor platform for Calendar Ortodox integration."""

from __future__ import annotations

from datetime import timedelta
import logging
from typing import Any

from homeassistant.components.sensor import SensorEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from . import CalendarOrtodoxDataUpdateCoordinator
from .calendar import fasting_text
from .const import (
    ATTR_DAY_OF_WEEK,
    ATTR_EOTHINON,
    ATTR_FASTING,
    ATTR_FASTING_DESCRIPTION,
    ATTR_FASTING_PERIOD,
    ATTR_FASTING_TYPE,
    ATTR_FEAST_DAY,
    ATTR_FEAST_LEVEL,
    ATTR_LITURGICAL_INFO,
    ATTR_MOON_PHASE,
    ATTR_NO_WEDDINGS,
    ATTR_NOTES,
    ATTR_READINGS,
    ATTR_ROMANIAN_SAINTS,
    ATTR_SAINTS,
    ATTR_TONE,
    CONF_LANGUAGE,
    DOMAIN,
    NEXT_FEAST_LOOKAHEAD_DAYS,
)
from .engine import OrthodoxCalendarDay

_LOGGER = logging.getLogger(__name__)

# Home Assistant rejects states longer than 255 characters.
MAX_STATE_LENGTH = 255


def short_state(text: str) -> str:
    """Trim text to a valid state value."""
    if len(text) <= MAX_STATE_LENGTH:
        return text
    return text[: MAX_STATE_LENGTH - 1].rstrip() + "…"


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up Calendar Ortodox sensor platform."""
    coordinator: CalendarOrtodoxDataUpdateCoordinator = hass.data[DOMAIN][
        entry.entry_id
    ]
    async_add_entities(
        [
            TodaySaintsSensor(coordinator, entry),
            NextFeastDaySensor(coordinator, entry),
        ]
    )


class TodaySaintsSensor(
    CoordinatorEntity[CalendarOrtodoxDataUpdateCoordinator], SensorEntity
):
    """Today's saints, feasts and fasting rules."""

    _attr_icon = "mdi:calendar-star"

    def __init__(
        self, coordinator: CalendarOrtodoxDataUpdateCoordinator, entry: ConfigEntry
    ) -> None:
        """Initialize the sensor."""
        super().__init__(coordinator)
        self._entry = entry
        self._attr_name = "Sfântul Zilei"
        self._attr_unique_id = f"{entry.entry_id}_today_saints"

    @property
    def _day(self) -> OrthodoxCalendarDay:
        return self.coordinator.calendar.day(self.coordinator.today)

    @property
    def native_value(self) -> str | None:
        """Today's saints."""
        return short_state(self._day.title) or None

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        """Details for today."""
        day_info = self._day
        language = self._entry.data.get(CONF_LANGUAGE, "ro")
        attrs: dict[str, Any] = {
            ATTR_SAINTS: day_info.title,
            ATTR_DAY_OF_WEEK: day_info.day_of_week,
            ATTR_FEAST_DAY: day_info.feast_day,
            ATTR_FEAST_LEVEL: day_info.feast_level,
            ATTR_FASTING: day_info.is_fasting,
            ATTR_FASTING_TYPE: day_info.fasting,
            ATTR_FASTING_PERIOD: day_info.fasting_period,
            ATTR_NO_WEDDINGS: day_info.no_weddings,
        }
        if day_info.fasting_info:
            attrs[ATTR_FASTING_DESCRIPTION] = fasting_text(day_info, language)
        if day_info.romanian_saints:
            attrs[ATTR_ROMANIAN_SAINTS] = day_info.romanian_saints
        if day_info.notes:
            attrs[ATTR_NOTES] = day_info.notes
        if day_info.moon_phase:
            attrs[ATTR_MOON_PHASE] = day_info.moon_phase
        if day_info.sunday_title:
            attrs[ATTR_LITURGICAL_INFO] = day_info.sunday_title
        if day_info.sunday_readings:
            attrs[ATTR_READINGS] = day_info.sunday_readings
        if day_info.sunday and day_info.sunday.tone:
            attrs[ATTR_TONE] = day_info.sunday.tone
            attrs[ATTR_EOTHINON] = day_info.sunday.eothinon
        return attrs


class NextFeastDaySensor(
    CoordinatorEntity[CalendarOrtodoxDataUpdateCoordinator], SensorEntity
):
    """The next feast day after today."""

    _attr_icon = "mdi:calendar-star"

    def __init__(
        self, coordinator: CalendarOrtodoxDataUpdateCoordinator, entry: ConfigEntry
    ) -> None:
        """Initialize the sensor."""
        super().__init__(coordinator)
        self._attr_name = "Următoarea Sărbătoare"
        self._attr_unique_id = f"{entry.entry_id}_next_feast"

    @property
    def _next_feast(self) -> OrthodoxCalendarDay | None:
        tomorrow = self.coordinator.today + timedelta(days=1)
        return self.coordinator.calendar.next_day(
            tomorrow, lambda d: d.feast_day, NEXT_FEAST_LOOKAHEAD_DAYS
        )

    @property
    def native_value(self) -> str | None:
        """Name of the next feast."""
        feast = self._next_feast
        return short_state(feast.title) if feast else None

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        """Date and countdown."""
        feast = self._next_feast
        if feast is None:
            return {}
        return {
            ATTR_SAINTS: feast.title,
            "date": feast.date.isoformat(),
            "days_until": (feast.date - self.coordinator.today).days,
            ATTR_FEAST_LEVEL: feast.feast_level,
            ATTR_DAY_OF_WEEK: feast.day_of_week,
        }
