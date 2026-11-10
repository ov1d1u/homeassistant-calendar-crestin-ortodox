"""End-to-end tests inside Home Assistant.

Needs ``pytest-homeassistant-custom-component``; skipped when it is not installed.
"""

from __future__ import annotations

import pytest

pytest.importorskip("pytest_homeassistant_custom_component")

from homeassistant import config_entries  # noqa: E402
from homeassistant.core import HomeAssistant  # noqa: E402
from homeassistant.data_entry_flow import FlowResultType  # noqa: E402
from pytest_homeassistant_custom_component.common import MockConfigEntry  # noqa: E402

DOMAIN = "calendar_ortodox"
CONFIG = {"language": "ro", "include_fasting": True, "include_readings": True}


@pytest.fixture(autouse=True)
def auto_enable_custom_integrations(enable_custom_integrations):
    yield


async def _setup(hass: HomeAssistant) -> MockConfigEntry:
    await hass.config.async_set_time_zone("Europe/Bucharest")
    entry = MockConfigEntry(
        domain=DOMAIN, data=CONFIG, unique_id="calendar_ortodox_instance"
    )
    entry.add_to_hass(hass)
    assert await hass.config_entries.async_setup(entry.entry_id)
    await hass.async_block_till_done()
    return entry


async def test_config_flow_creates_entry(hass: HomeAssistant) -> None:
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )
    assert result["type"] is FlowResultType.FORM
    result = await hass.config_entries.flow.async_configure(result["flow_id"], CONFIG)
    assert result["type"] is FlowResultType.CREATE_ENTRY
    assert result["title"] == "Calendar Ortodox"


async def test_entities_on_easter(hass: HomeAssistant, freezer) -> None:
    freezer.move_to("2026-04-12 10:00:00+03:00")
    entry = await _setup(hass)

    saints = hass.states.get("sensor.sfantul_zilei")
    assert saints.state == "(†) Învierea Domnului (Sfintele Paști)"
    assert saints.attributes["feast_level"] == "great"
    assert saints.attributes["no_weddings"] is True
    assert saints.attributes["readings"]["gospel"] == "Ev. Ioan I, 1-17"

    next_feast = hass.states.get("sensor.urmatoarea_sarbatoare")
    assert next_feast.attributes["date"] == "2026-04-13"
    assert next_feast.attributes["days_until"] == 1

    assert hass.states.get("calendar.calendar_ortodox").state == "on"
    assert hass.states.get("calendar.calendar_ortodox_sarbatori").state == "on"

    await hass.services.async_call(DOMAIN, "refresh_calendar", blocking=True)

    assert await hass.config_entries.async_unload(entry.entry_id)
    await hass.async_block_till_done()
    assert not hass.services.has_service(DOMAIN, "refresh_calendar")


async def test_fasting_attributes(hass: HomeAssistant, freezer) -> None:
    freezer.move_to("2026-04-10 10:00:00+03:00")  # Good Friday
    await _setup(hass)
    state = hass.states.get("sensor.sfantul_zilei")
    assert state.attributes["fasting"] is True
    assert state.attributes["fasting_type"] == "Post negru"
    assert state.attributes["fasting_period"] == "great_lent"


async def test_calendar_events_across_new_year(hass: HomeAssistant, freezer) -> None:
    freezer.move_to("2026-12-30 10:00:00+02:00")
    await _setup(hass)
    response = await hass.services.async_call(
        "calendar",
        "get_events",
        {
            "start_date_time": "2026-12-31 00:00:00",
            "end_date_time": "2027-01-02 00:00:00",
        },
        target={"entity_id": "calendar.calendar_ortodox"},
        blocking=True,
        return_response=True,
    )
    events = response["calendar.calendar_ortodox"]["events"]
    assert [e["start"] for e in events] == ["2026-12-31", "2027-01-01"]
    assert events[0]["summary"].startswith("Odovania")
    assert events[1]["summary"].startswith("(†) Tăierea-împrejur")

    feast_response = await hass.services.async_call(
        "calendar",
        "get_events",
        {
            "start_date_time": "2026-12-31 00:00:00",
            "end_date_time": "2027-01-02 00:00:00",
        },
        target={"entity_id": "calendar.calendar_ortodox_sarbatori"},
        blocking=True,
        return_response=True,
    )
    feast_events = feast_response["calendar.calendar_ortodox_sarbatori"]["events"]
    assert [e["start"] for e in feast_events] == ["2027-01-01"]
    # Both calendars title a great feast the same way.
    assert feast_events[0]["summary"] == events[1]["summary"]


async def test_long_state_is_trimmed(hass: HomeAssistant, freezer) -> None:
    freezer.move_to("2026-08-16 10:00:00+03:00")
    await _setup(hass)
    state = hass.states.get("sensor.sfantul_zilei")
    assert len(state.state) <= 255
    assert state.attributes["saints"].startswith(state.state.rstrip("…"))
