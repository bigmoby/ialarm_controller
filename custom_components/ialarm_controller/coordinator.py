"""Coordinator for the iAlarm integration."""

from __future__ import annotations

import logging

from homeassistant.components.alarm_control_panel import SCAN_INTERVAL
from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed
from pyasyncialarm.const import ZoneStatusType
from pyasyncialarm.pyasyncialarm import IAlarm

from .const import DOMAIN, IALARM_TO_HASS, IAlarmStatusType

_LOGGER = logging.getLogger(__name__)


class IAlarmCoordinator(DataUpdateCoordinator[IAlarmStatusType]):
    """Class to manage fetching iAlarm data."""

    def __init__(self, hass: HomeAssistant, device: IAlarm, mac: str) -> None:
        """Initialize global iAlarm data updater."""
        self.ialarm_device = device
        self.state: IAlarmStatusType | None = None
        self.host: str = device.host
        self.mac = mac

        super().__init__(
            hass,
            _LOGGER,
            name=DOMAIN,
            update_interval=SCAN_INTERVAL,
        )

    async def _async_update_data(self) -> IAlarmStatusType:
        """Fetch data from iAlarm."""
        try:
            status = await self.ialarm_device.get_status()
            zone_status: list[ZoneStatusType] = (
                await self.ialarm_device.get_zone_status()
            )
            ialarm_status: IAlarmStatusType = IAlarmStatusType(
                ialarm_status=IALARM_TO_HASS.get(status), zone_status_list=zone_status
            )
            self.state = ialarm_status
            self.async_set_updated_data(ialarm_status)
        except ConnectionError as error:
            raise UpdateFailed(error) from error
        return ialarm_status
