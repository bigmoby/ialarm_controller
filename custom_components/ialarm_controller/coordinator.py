"""Coordinator for the iAlarm integration."""

from __future__ import annotations

import logging

from homeassistant.components.alarm_control_panel import SCAN_INTERVAL
from homeassistant.core import HomeAssistant, ServiceResponse
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed
from pyasyncialarm.const import AlarmStatusType, LogEntryType, ZoneStatusType
from pyasyncialarm.pyasyncialarm import IAlarm

from .const import DOMAIN, IALARM_TO_HASS, SERVICE_GET_LOG_MAX_ENTRIES, IAlarmStatusType

_LOGGER = logging.getLogger(__name__)


class IAlarmCoordinator(DataUpdateCoordinator[IAlarmStatusType]):
    """Class to manage fetching iAlarm data."""

    def __init__(
        self, hass: HomeAssistant, device: IAlarm, mac: str, send_events: bool
    ) -> None:
        """Initialize global iAlarm data updater."""
        self.ialarm_device = device
        self.state: IAlarmStatusType | None = None
        self.host: str = device.host
        self.mac = mac
        self.send_events = send_events

        super().__init__(
            hass,
            _LOGGER,
            name=DOMAIN,
            update_interval=SCAN_INTERVAL,
        )

    async def async_cancel_alarm(self) -> None:
        """Cancel alarm alerts."""
        await self.ialarm_device.cancel_alarm()
        if self.send_events:
            self.hass.bus.async_fire(event_type="cancel_alarm")

    async def async_get_log(
        self, max_entries: int = SERVICE_GET_LOG_MAX_ENTRIES
    ) -> ServiceResponse:
        """Retrieve last n log entries."""

        _LOGGER.debug("Retrieve last %s log entries.", max_entries)

        items: list[LogEntryType] = await self.ialarm_device.get_last_log_entries(
            max_entries
        )

        if items:
            self.hass.bus.async_fire(event_type="ialarm_logs", event_data=items)
            return {
                "items": [
                    {
                        "time": item["time"],
                        "area": item["area"],
                        "event": item["event"],
                        "name": item["name"],
                    }
                    for item in items
                ],
            }
        return []

    async def _async_update_data(self) -> IAlarmStatusType:
        """Fetch data from iAlarm."""
        try:
            zone_status: list[
                ZoneStatusType
            ] = await self.ialarm_device.get_zone_status()
            internal_alarm_status: AlarmStatusType = (
                await self.ialarm_device.get_status(zone_status)
            )

            alarm_status_value = IALARM_TO_HASS.get(
                internal_alarm_status["status_value"]
            )

            if alarm_status_value == IAlarm.TRIGGERED and self.send_events:
                ialarm_alarmed_zones: list[ZoneStatusType] | None = (
                    internal_alarm_status["alarmed_zones"]
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
            self.async_set_updated_data(ialarm_status)
        except ConnectionError as error:
            raise UpdateFailed(error) from error
        return ialarm_status
