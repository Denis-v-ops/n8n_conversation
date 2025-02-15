"""The n8n Conversation integration."""
from __future__ import annotations
import logging

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.components import conversation
from homeassistant.exceptions import ConfigEntryNotReady

from .const import DOMAIN, CONF_WEBHOOK_URL, DEFAULT_WEBHOOK_URL
from .agent import N8NConversationAgent

_LOGGER = logging.getLogger(__name__)


# async def async_setup(hass: HomeAssistant, config: dict) -> bool:
#     """Set up the integration (nothing for YAML)."""
#     return True

async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up from a config entry."""
    # Optionally validate your webhook or handle errors
    webhook_url = entry.data.get(CONF_WEBHOOK_URL, DEFAULT_WEBHOOK_URL)
    if not webhook_url:
        raise ConfigEntryNotReady("Missing webhook URL")

    # Create and register your agent
    agent = N8NConversationAgent(hass, entry)
    conversation.async_set_agent(hass, entry, agent)
    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload the config entry."""
    # Unregister it
    conversation.async_unset_agent(hass, entry)
    return True
