"""The n8n Conversation integration."""
from __future__ import annotations
import logging

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.components import conversation
from homeassistant.exceptions import ConfigEntryNotReady

from .const import DOMAIN, CONF_WEBHOOK_URL, DEFAULT_WEBHOOK_URL
from .agent import N8NConversationAgent
from . import services  # Import our service implementation

_LOGGER = logging.getLogger(__name__)

async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up from a config entry."""
    webhook_url = entry.data.get(CONF_WEBHOOK_URL, DEFAULT_WEBHOOK_URL)
    if not webhook_url:
        raise ConfigEntryNotReady("Missing webhook URL")

    # Create and register your agent.
    agent = N8NConversationAgent(hass, entry)
    conversation.async_set_agent(hass, entry, agent)

    # Register custom service only once.
    hass.data.setdefault(DOMAIN, {})
    if not hass.data[DOMAIN].get("service_registered"):
        hass.services.async_register(
            DOMAIN,
            "schedule_action",
            services.async_handle_schedule_action,
            schema=services.SERVICE_SCHEMA,
        )
        hass.data[DOMAIN]["service_registered"] = True
        _LOGGER.debug("Custom service 'schedule_action' registered.")
    else:
        _LOGGER.debug("Custom service 'schedule_action' already registered.")

    return True

async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload the config entry."""
    conversation.async_unset_agent(hass, entry)
    return True
