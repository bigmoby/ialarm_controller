"""Device triggers for iAlarm controller."""

import logging
from typing import Any

from homeassistant.components.device_automation import DEVICE_TRIGGER_BASE_SCHEMA
from homeassistant.components.homeassistant.triggers import event as event_trigger
from homeassistant.const import CONF_DEVICE_ID, CONF_DOMAIN, CONF_PLATFORM, CONF_TYPE
from homeassistant.core import CALLBACK_TYPE, HomeAssistant
from homeassistant.helpers.trigger import TriggerActionType, TriggerInfo
from homeassistant.helpers.typing import ConfigType
import voluptuous as vol

from .const import DOMAIN

_LOGGER = logging.getLogger(__name__)

TRIGGER_TYPES = {
    "disarmed",
    "armed_home",
    "armed_away",
    "triggered",
    "cancel",
}

EVENT_MAP = {
    "disarmed": "ialarm_disarm",
    "armed_home": "ialarm_arm_stay",
    "armed_away": "ialarm_arm_away",
    "triggered": "ialarm_triggered",
    "cancel": "cancel_alarm",
}

TRIGGER_SCHEMA = DEVICE_TRIGGER_BASE_SCHEMA.extend(
    {
        vol.Required(CONF_TYPE): vol.In(TRIGGER_TYPES),
    }
)


async def async_get_triggers(
    hass: HomeAssistant, device_id: str
) -> list[dict[str, Any]]:
    """List device triggers for iAlarm devices."""
    _LOGGER.debug("Getting triggers for device %s", device_id)
    return [
        {
            CONF_PLATFORM: "device",
            CONF_DEVICE_ID: device_id,
            CONF_DOMAIN: DOMAIN,
            CONF_TYPE: trigger_type,
        }
        for trigger_type in TRIGGER_TYPES
    ]


async def async_attach_trigger(
    hass: HomeAssistant,
    config: ConfigType,
    action: TriggerActionType,
    trigger_info: TriggerInfo,
) -> CALLBACK_TYPE:
    """Attach a trigger."""
    trigger_type = config[CONF_TYPE]
    event_type = EVENT_MAP[trigger_type]
    _LOGGER.debug("Attaching trigger %s for event %s", trigger_type, event_type)

    event_config = event_trigger.TRIGGER_SCHEMA(
        {
            event_trigger.CONF_PLATFORM: "event",
            event_trigger.CONF_EVENT_TYPE: event_type,
        }
    )

    return await event_trigger.async_attach_trigger(
        hass, event_config, action, trigger_info
    )
