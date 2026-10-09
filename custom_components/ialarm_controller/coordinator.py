"""Coordinator for the iAlarm integration."""

from __future__ import annotations

import asyncio
import logging

from homeassistant.components.alarm_control_panel.const import AlarmControlPanelState
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant, ServiceResponse, callback
from homeassistant.helpers.entity_component import DEFAULT_SCAN_INTERVAL
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed
from homeassistant.util.json import JsonValueType
from pyasyncialarm.const import (
    AlarmStatusType,
    LogEntryType,
    StatusType,
    ZoneStatusType,
)
from pyasyncialarm.pyasyncialarm import IAlarm

from .const import (
    CLEAR_MEMORY_MAX_ATTEMPTS,
    CLEAR_MEMORY_RETRY_DELAY,
    DOMAIN,
    IALARM_TO_HASS,
    SERVICE_GET_LOG_MAX_ENTRIES,
    IAlarmStatusType,
)

_LOGGER = logging.getLogger(__name__)

type IAlarmConfigEntry = ConfigEntry[IAlarmCoordinator]


class IAlarmCoordinator(DataUpdateCoordinator[IAlarmStatusType]):
    """Class to manage fetching iAlarm data."""

    config_entry: IAlarmConfigEntry

    def __init__(
        self,
        hass: HomeAssistant,
        config_entry: IAlarmConfigEntry,
        device: IAlarm,
        mac: str,
        send_events: bool,
    ) -> None:
        """Initialize global iAlarm data updater."""
        self.ialarm_device = device
        self.state: IAlarmStatusType | None = None
        self.host: str = device.host
        self.mac = mac
        self.send_events = send_events
        self._io_lock: asyncio.Lock = asyncio.Lock()

        super().__init__(
            hass,
            _LOGGER,
            config_entry=config_entry,
            name=DOMAIN,
            update_interval=DEFAULT_SCAN_INTERVAL,
        )

    async def async_shutdown(self) -> None:
        """Shut down the coordinator and close the alarm device connection."""
        async with self._io_lock:
            await self.ialarm_device.shutdown()
        await super().async_shutdown()

    async def async_cancel_alarm(self) -> None:
        """Cancel alarm alerts."""
        async with self._io_lock:
            await self.ialarm_device.cancel_alarm()
        if self.send_events:
            self.hass.bus.async_fire(event_type="cancel_alarm")

    async def async_get_log(
        self, max_entries: int = SERVICE_GET_LOG_MAX_ENTRIES
    ) -> ServiceResponse:
        """Retrieve last n log entries."""
        _LOGGER.debug("Retrieve last %s log entries.", max_entries)

        async with self._io_lock:
            items: list[LogEntryType] = await self.ialarm_device.get_last_log_entries(
                max_entries
            )

        if not items:
            return {"items": []}

        log_entries: list[JsonValueType] = [
            {
                "time": item["time"],
                "area": item["area"],
                "event": item["event"],
                "name": item["name"],
            }
            for item in items
            if item is not None
        ]
        self.hass.bus.async_fire(
            event_type="ialarm_logs", event_data={"items": log_entries}
        )
        return {"items": log_entries}

    async def _async_get_alarmed_zone_ids(self) -> list[int]:
        """Return the in-use zones that still have the ZONE_ALARM flag set."""
        zones = await self.ialarm_device.get_zone_status()
        return [
            zone["zone_id"]
            for zone in zones
            if StatusType.ZONE_ALARM in zone["types"]
            and StatusType.ZONE_IN_USE in zone["types"]
        ]

    async def _async_clear_alarm_memory(self) -> None:
        """Clear the zone alarm memory left by a disarm not sent from HA.

        Disarming from a key fob or keypad does not send the CLEAR command, so
        the panel keeps the ZONE_ALARM flag on the zones that were violated.
        Arming with that memory still set reports the panel as triggered right
        away. Must be called with the I/O lock held.
        """
        alarmed = await self._async_get_alarmed_zone_ids()
        for attempt in range(1, CLEAR_MEMORY_MAX_ATTEMPTS + 1):
            if not alarmed:
                return
            _LOGGER.debug(
                "iAlarm: clearing alarm memory of zones %s before arming "
                "(attempt %d/%d)",
                alarmed,
                attempt,
                CLEAR_MEMORY_MAX_ATTEMPTS,
            )
            await self.ialarm_device.cancel_alarm()
            await asyncio.sleep(CLEAR_MEMORY_RETRY_DELAY)
            alarmed = await self._async_get_alarmed_zone_ids()

        if alarmed:
            _LOGGER.warning(
                "iAlarm: alarm memory of zones %s still set after %d clear "
                "attempts, arming anyway",
                alarmed,
                CLEAR_MEMORY_MAX_ATTEMPTS,
            )

    async def async_arm_stay(self) -> None:
        """Send arm stay/home command."""
        async with self._io_lock:
            await self._async_clear_alarm_memory()
            await self.ialarm_device.arm_stay()

    async def async_arm_away(self) -> None:
        """Send arm away command."""
        async with self._io_lock:
            await self._async_clear_alarm_memory()
            await self.ialarm_device.arm_away()

    async def async_disarm_and_cancel(self) -> bool:
        """Send disarm and cancel alarm command, confirming state clearance."""
        async with self._io_lock:
            return await self.ialarm_device.disarm_and_cancel()

    @callback
    def async_set_alarm_status(self, status: AlarmControlPanelState) -> None:
        """Force an immediate status update without waiting for polling."""
        zone_status = self.data["zone_status_list"] if self.data else []
        new_data: IAlarmStatusType = IAlarmStatusType(
            ialarm_status=status,
            zone_status_list=zone_status,
        )
        self.state = new_data
        self.async_set_updated_data(new_data)

    async def _async_update_data(self) -> IAlarmStatusType:
        """Fetch data from iAlarm."""
        try:
            async with self._io_lock:
                zone_status: list[
                    ZoneStatusType
                ] = await self.ialarm_device.get_zone_status()
                internal_alarm_status: AlarmStatusType = (
                    await self.ialarm_device.get_status(zone_status)
                )

            alarm_status_value = IALARM_TO_HASS.get(
                internal_alarm_status["status_value"]
            )

            _LOGGER.debug(
                "iAlarm raw status [%s], mapped to [%s]",
                internal_alarm_status["status_value"],
                alarm_status_value,
            )

            if (
                alarm_status_value == AlarmControlPanelState.TRIGGERED
                and self.send_events
            ):
                ialarm_alarmed_zones: list[ZoneStatusType] | None = (
                    internal_alarm_status["alarmed_zones"]
                )

                _LOGGER.debug(
                    "iAlarm in TRIGGERED status with allarmed zones [%s]",
                    ialarm_alarmed_zones,
                )

                self.hass.bus.async_fire(
                    event_type="ialarm_triggered",
                    event_data={
                        "alarm_status": "TRIGGERED",
                        "alarmed_zones": ialarm_alarmed_zones,
                    },
                )

            ialarm_status: IAlarmStatusType = IAlarmStatusType(
                ialarm_status=alarm_status_value, zone_status_list=zone_status
            )

            self.state = ialarm_status
        except ConnectionError as error:
            raise UpdateFailed(error) from error
        return ialarm_status
