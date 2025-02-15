from __future__ import annotations
from typing import Any
import voluptuous as vol

from homeassistant.config_entries import ConfigFlow
from homeassistant.const import CONF_NAME
from homeassistant.data_entry_flow import FlowResult

from .const import DOMAIN, DEFAULT_NAME, CONF_WEBHOOK_URL, DEFAULT_WEBHOOK_URL


def configured_instances(hass) -> set[str]:
    """Return a set of configured instance names."""
    return {
        entry.data[CONF_NAME] for entry in hass.config_entries.async_entries(DOMAIN)
    }


class N8NConfigFlow(ConfigFlow, domain=DOMAIN):
    """Handle a config flow for N8N Conversation."""

    VERSION = 1

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Handle the initial step."""
        errors = {}

        if user_input is not None:
            if user_input[CONF_NAME] in configured_instances(self.hass):
                errors["base"] = "name_exists"

            if not errors:
                return self.async_create_entry(
                    title=user_input[CONF_NAME], data=user_input
                )

        default_data = {
            CONF_NAME: DEFAULT_NAME,
            CONF_WEBHOOK_URL: DEFAULT_WEBHOOK_URL,
        }
        return self.async_show_form(
            step_id="user",
            data_schema=vol.Schema(
                {
                    vol.Required(
                        CONF_NAME, default=default_data[CONF_NAME]
                    ): str,
                    vol.Required(
                        CONF_WEBHOOK_URL, default=default_data[CONF_WEBHOOK_URL]
                    ): str,
                }
            ),
            errors=errors,
        )
