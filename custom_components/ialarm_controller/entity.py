"""Defines the IAlarmEntity class for managing iAlarm entities.

The IAlarmEntity class is a representation of an entity in the iAlarm
system that interacts with the Home Assistant framework. It extends
the CoordinatorEntity to facilitate coordination of updates for the
iAlarm system and includes device information such as manufacturer
and unique identifiers.

Classes:
- IAlarmEntity: Represents an entity in the iAlarm system.
"""

from homeassistant.helpers.device_registry import CONNECTION_NETWORK_MAC, DeviceInfo
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from custom_components.ialarm_controller.const import DOMAIN
from custom_components.ialarm_controller.coordinator import IAlarmCoordinator


class IAlarmEntity(CoordinatorEntity[IAlarmCoordinator]):
    """Represents an entity in the iAlarm system."""

    _attr_has_entity_name = True

    def __init__(
        self, coordinator: IAlarmCoordinator, unique_id: str, name: str
    ) -> None:
        """Initialize the entity."""
        super().__init__(coordinator)

        self._attr_unique_id = unique_id
        self._attr_device_info = DeviceInfo(
            manufacturer="Antifurto365 - Meian",
            name=name,
        )
        if coordinator.mac:
            self._attr_device_info["connections"] = {
                (CONNECTION_NETWORK_MAC, coordinator.mac)
            }
            self._attr_device_info["identifiers"] = {(DOMAIN, coordinator.mac)}
