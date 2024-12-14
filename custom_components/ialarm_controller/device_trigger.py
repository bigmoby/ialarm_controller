"""Defines the IAlarm trigger for managing iAlarm entities."""

import logging
from typing import Any

from homeassistant.components.device_automation import DEVICE_TRIGGER_BASE_SCHEMA
from homeassistant.components.homeassistant.triggers import event as event_trigger
from homeassistant.const import (
    CONF_DEVICE_ID,
    CONF_DOMAIN,
    CONF_EVENT,
    CONF_PLATFORM,
    CONF_TYPE,
)
from homeassistant.core import CALLBACK_TYPE, HomeAssistant
from homeassistant.helpers.trigger import TriggerActionType, TriggerInfo
from homeassistant.helpers.typing import ConfigType
import voluptuous as vol

from custom_components.ialarm_controller.const import DOMAIN

_LOGGER = logging.getLogger(__name__)

TRIGGER_TYPES = {"ialarm_disarm"}

TRIGGER_SCHEMA = DEVICE_TRIGGER_BASE_SCHEMA.extend(
    {
        vol.Required(CONF_TYPE): vol.In(TRIGGER_TYPES),
    }
)


async def async_get_triggers(
    hass: HomeAssistant, device_id: str
) -> list[dict[str, Any]]:
    """Return a list of triggers."""
    # device_registry = dr.async_get(hass)
    # device_entry = device_registry.async_get(device_id)

    triggers = []

    # Determine which triggers are supported by this device_id ...
    triggers.append(
        {
            CONF_PLATFORM: "device",
            CONF_DOMAIN: DOMAIN,
            CONF_DEVICE_ID: device_id,
            CONF_TYPE: "ialarm_disarm",
        }
    )

    return triggers


async def async_attach_trigger(
    hass: HomeAssistant,
    config: ConfigType,
    action: TriggerActionType,
    trigger_info: TriggerInfo,
) -> CALLBACK_TYPE:
    """Attach a trigger."""
    return await event_trigger.async_attach_trigger(
        hass,
        event_trigger.TRIGGER_SCHEMA(
            {
                event_trigger.CONF_PLATFORM: CONF_EVENT,
                event_trigger.CONF_EVENT_TYPE: "ialarm_disarm",
                event_trigger.CONF_EVENT_DATA: {
                    CONF_DEVICE_ID: config[CONF_DEVICE_ID],
                },
            }
        ),
        action,
        trigger_info,
        platform_type="device",
    )
