"""Interfaces with iAlarm control panels."""

from __future__ import annotations

import logging

from homeassistant.components.alarm_control_panel import (
    AlarmControlPanelEntity,
    AlarmControlPanelEntityFeature,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant, ServiceResponse
from homeassistant.helpers import entity_platform
from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DATA_COORDINATOR, DOMAIN, ENTITY_SERVICES, IAlarmStatusType
from .coordinator import IAlarmCoordinator

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(
    hass: HomeAssistant, entry: ConfigEntry, async_add_entities: AddEntitiesCallback
) -> None:
    """Set up a iAlarm alarm control panel based on a config entry."""
    ialarm_coordinator: IAlarmCoordinator = hass.data[DOMAIN][entry.entry_id][
        DATA_COORDINATOR
    ]
    async_add_entities([IAlarmPanel(ialarm_coordinator)], False)

    platform = entity_platform.async_get_current_platform()

    for service_name, service_schema in ENTITY_SERVICES.items():
        platform.async_register_entity_service(
            service_name, service_schema, f"async_{service_name}"
        )


class IAlarmPanel(CoordinatorEntity[IAlarmCoordinator], AlarmControlPanelEntity):
    """Representation of an iAlarm device."""

    _attr_has_entity_name = True
    _attr_name = None
    _attr_supported_features = (
        AlarmControlPanelEntityFeature.ARM_HOME
        | AlarmControlPanelEntityFeature.ARM_AWAY
    )
    _attr_code_arm_required = False

    def __init__(self, coordinator: IAlarmCoordinator) -> None:
        """Create the entity with a DataUpdateCoordinator."""
        super().__init__(coordinator)
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, coordinator.mac)},
            manufacturer="Antifurto365 - Meian",
            name="iAlarm",
        )
        self._attr_unique_id = f"{coordinator.mac}-ialarm_status"

    @property
    def state(self) -> str | None:
        """Return the state of the device."""
        ialarm_state: IAlarmStatusType | None = self.coordinator.state
        if ialarm_state is None:
            return None
        return ialarm_state["ialarm_status"]

    async def async_alarm_disarm(self, code: str | None = None) -> None:
        """Send disarm command."""
        # Require a code to be passed for disarm operations
        if code is None or code == "":
            raise ValueError("Please input the disarm code.")
        await self.coordinator.ialarm_device.disarm()

    async def async_alarm_arm_home(self, code: str | None = None) -> None:
        """Send arm home command."""
        await self.coordinator.ialarm_device.arm_stay()

    async def async_alarm_arm_away(self, code: str | None = None) -> None:
        """Send arm away command."""
        await self.coordinator.ialarm_device.arm_away()

    async def async_get_log(self, max_entries: int) -> ServiceResponse:
        """Retrieve last n log entries."""
        items = await self.coordinator.ialarm_device.get_last_log_entries(max_entries)
        if items:
            self.hass.bus.fire("ialarm_logs", items)
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
