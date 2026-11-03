"""The Calendar Ortodox integration (offline)."""

from __future__ import annotations

import logging
from datetime import date
from typing import Any

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import Platform
from homeassistant.core import HomeAssistant, ServiceCall, callback
from homeassistant.helpers.event import async_track_time_change
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator
from homeassistant.util import dt as dt_util

from .const import DOMAIN, SCAN_INTERVAL
from .engine import OrthodoxCalendar

_LOGGER = logging.getLogger(__name__)

PLATFORMS: list[Platform] = [Platform.CALENDAR, Platform.SENSOR]

SERVICE_REFRESH_CALENDAR = "refresh_calendar"


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up Calendar Ortodox from a config entry."""
    # Loading the bundled data reads files, so do it outside the event loop.
    calendar = await hass.async_add_executor_job(
        OrthodoxCalendar, None, hass.config.time_zone
    )

    coordinator = CalendarOrtodoxDataUpdateCoordinator(hass, calendar)
    await coordinator.async_config_entry_first_refresh()

    hass.data.setdefault(DOMAIN, {})
    hass.data[DOMAIN][entry.entry_id] = coordinator

    # Update states right after midnight, when the day changes.
    @callback
    def _midnight(_now: Any) -> None:
        hass.async_create_task(coordinator.async_refresh())

    entry.async_on_unload(
        async_track_time_change(hass, _midnight, hour=0, minute=0, second=5)
    )

    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)

    async def handle_refresh_calendar(call: ServiceCall) -> None:
        """Recompute the calendar (clears cached days)."""
        _LOGGER.debug("Manual calendar refresh requested")
        coordinator.calendar.clear_cache()
        await coordinator.async_refresh()

    if not hass.services.has_service(DOMAIN, SERVICE_REFRESH_CALENDAR):
        hass.services.async_register(
            DOMAIN, SERVICE_REFRESH_CALENDAR, handle_refresh_calendar
        )

    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a config entry."""
    if unload_ok := await hass.config_entries.async_unload_platforms(entry, PLATFORMS):
        hass.data[DOMAIN].pop(entry.entry_id)
        if not hass.data[DOMAIN]:
            hass.services.async_remove(DOMAIN, SERVICE_REFRESH_CALENDAR)
    return unload_ok


class CalendarOrtodoxDataUpdateCoordinator(DataUpdateCoordinator[dict[str, Any]]):
    """Keeps track of the current day; all data is computed locally."""

    def __init__(self, hass: HomeAssistant, calendar: OrthodoxCalendar) -> None:
        """Initialize the coordinator."""
        super().__init__(hass, _LOGGER, name=DOMAIN, update_interval=SCAN_INTERVAL)
        self.calendar = calendar

    @property
    def today(self) -> date:
        """Today's date in Home Assistant's time zone."""
        return dt_util.now().date()

    async def _async_update_data(self) -> dict[str, Any]:
        """Compute today's information."""
        today = self.today
        return {"today": today, "day": self.calendar.day(today)}
