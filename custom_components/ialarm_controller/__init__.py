"""iAlarm integration."""

from __future__ import annotations

import asyncio
from typing import TypeAlias

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import (
    CONF_EVENT,
    CONF_HOST,
    CONF_PORT,
    EVENT_HOMEASSISTANT_STOP,
    Platform,
)
from homeassistant.core import Event, HomeAssistant
from homeassistant.exceptions import ConfigEntryNotReady
from pyasyncialarm.pyasyncialarm import IAlarm

from .const import DEFAULT_SEND_EVENTS
from .coordinator import IAlarmCoordinator

PLATFORMS = [Platform.ALARM_CONTROL_PANEL, Platform.SENSOR, Platform.BUTTON]

IAlarmConfigEntry: TypeAlias = ConfigEntry[IAlarmCoordinator]


async def async_setup_entry(
    hass: HomeAssistant, config_entry: IAlarmConfigEntry
) -> bool:
    """Set up iAlarm config."""
    host: str = config_entry.data[CONF_HOST]
    port: int = config_entry.data[CONF_PORT]

    # Read send_events from options, fallback to data for backwards compatibility
    send_events: bool = config_entry.options.get(
        CONF_EVENT, config_entry.data.get(CONF_EVENT, DEFAULT_SEND_EVENTS)
    )
    ialarm_device = IAlarm(host, port)

    try:
        async with asyncio.timeout(10):
            mac = await ialarm_device.get_mac()
    except (TimeoutError, ConnectionError) as ex:
        raise ConfigEntryNotReady from ex

    coordinator = IAlarmCoordinator(hass, ialarm_device, mac, send_events)

    await coordinator.async_config_entry_first_refresh()

    config_entry.runtime_data = coordinator

    async def _async_close_connection(event: Event) -> None:
        """Close connection on HA Stop."""
        await coordinator.async_shutdown()

    config_entry.async_on_unload(
        hass.bus.async_listen_once(EVENT_HOMEASSISTANT_STOP, _async_close_connection)
    )

    config_entry.async_on_unload(config_entry.add_update_listener(update_listener))

    await hass.config_entries.async_forward_entry_setups(config_entry, PLATFORMS)

    return True


async def async_unload_entry(
    hass: HomeAssistant, config_entry: IAlarmConfigEntry
) -> bool:
    """Unload iAlarm config."""
    return await hass.config_entries.async_unload_platforms(config_entry, PLATFORMS)


async def update_listener(hass: HomeAssistant, config_entry: IAlarmConfigEntry) -> None:
    """Handle options update."""
    await hass.config_entries.async_reload(config_entry.entry_id)
