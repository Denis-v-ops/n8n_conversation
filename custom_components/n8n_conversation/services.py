"""Service implementations for the n8n Conversation integration."""
import voluptuous as vol
import homeassistant.helpers.config_validation as cv
from homeassistant.core import HomeAssistant, ServiceCall, callback
from homeassistant.helpers.event import async_call_later
from .const import DOMAIN

SERVICE_SCHEMA = vol.Schema({
    vol.Required("timer_id"): cv.string,
    vol.Required("action"): vol.In(["set", "extend", "cancel"]),
    vol.Optional("delay", default=0): vol.Coerce(int),
    vol.Required("service"): cv.string,
    vol.Optional("target"): dict,
    vol.Optional("data", default={}): dict,
})

async def async_handle_schedule_action(call: ServiceCall) -> None:
    """Handle scheduling service call."""
    hass: HomeAssistant = call.hass
    # Ensure a data container exists for this domain.
    hass.data.setdefault(DOMAIN, {})
    timers = hass.data[DOMAIN].setdefault("timers", {})

    timer_id = call.data["timer_id"]
    action_type = call.data["action"]
    delay = call.data.get("delay", 0)
    service_str = call.data["service"]
    target = call.data.get("target")
    service_data = call.data.get("data", {})

    if action_type == "cancel":
        if timer_id in timers:
            timers[timer_id]()  # Cancel the timer.
            del timers[timer_id]
        hass.components.persistent_notification.async_create(
            f"Timer {timer_id} cancelled.", title="Schedule Action"
        )
    elif action_type in ["set", "extend"]:
        if action_type == "extend" and timer_id in timers:
            timers[timer_id]()  # Cancel the existing timer.
        timers[timer_id] = async_call_later(
            hass, delay, _schedule_callback(hass, timer_id, service_str, target, service_data)
        )
        hass.components.persistent_notification.async_create(
            f"Timer {timer_id} set for {delay} seconds.", title="Schedule Action"
        )
    else:
        hass.components.persistent_notification.async_create(
            f"Unknown action {action_type}.", title="Schedule Action"
        )

@callback
def _schedule_callback(hass: HomeAssistant, timer_id: str, service_str: str, target: dict, service_data: dict):
    """Return a callback that executes the scheduled service call."""
    @callback
    async def _callback(now):
        try:
            domain, svc = service_str.split(".")
            await hass.services.async_call(domain, svc, service_data, target=target)
        except Exception as err:
            hass.components.persistent_notification.async_create(
                f"Error executing scheduled service: {err}", title="Schedule Action"
            )
        # Clean up the timer.
        timers = hass.data[DOMAIN].get("timers", {})
        timers.pop(timer_id, None)
    return _callback
