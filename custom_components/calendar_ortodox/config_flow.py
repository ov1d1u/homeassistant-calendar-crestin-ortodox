"""Config flow for Calendar Ortodox integration."""

from __future__ import annotations

from typing import Any

import voluptuous as vol

from homeassistant import config_entries
from homeassistant.data_entry_flow import FlowResult

from .const import (
    CONF_INCLUDE_FASTING,
    CONF_INCLUDE_READINGS,
    CONF_LANGUAGE,
    DEFAULT_INCLUDE_FASTING,
    DEFAULT_INCLUDE_READINGS,
    DEFAULT_LANGUAGE,
    DOMAIN,
)

STEP_USER_DATA_SCHEMA = vol.Schema(
    {
        vol.Optional(CONF_LANGUAGE, default=DEFAULT_LANGUAGE): vol.In(["ro", "en"]),
        vol.Optional(CONF_INCLUDE_FASTING, default=DEFAULT_INCLUDE_FASTING): bool,
        vol.Optional(CONF_INCLUDE_READINGS, default=DEFAULT_INCLUDE_READINGS): bool,
    }
)


class ConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a config flow for Calendar Ortodox."""

    VERSION = 1

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Handle the initial step. Everything is computed locally, so nothing to validate."""
        if user_input is not None:
            await self.async_set_unique_id("calendar_ortodox_instance")
            self._abort_if_unique_id_configured()
            return self.async_create_entry(title="Calendar Ortodox", data=user_input)

        return self.async_show_form(step_id="user", data_schema=STEP_USER_DATA_SCHEMA)
