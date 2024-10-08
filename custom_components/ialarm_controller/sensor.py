"""Support for sensors."""

from __future__ import annotations

import logging
from typing import Any

from homeassistant.components.sensor import SensorEntity, SensorEntityDescription
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import EntityCategory
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DATA_COORDINATOR, DOMAIN, IAlarmStatusType
from .coordinator import IAlarmCoordinator
from pyasyncialarm.const import StatusType, ZoneStatusType

_LOGGER = logging.getLogger(__name__)

SENSOR_IALARM_ZONE_STATUS = SensorEntityDescription(
    key="ALARMS",
    translation_key="alarms",
    entity_category=EntityCategory.DIAGNOSTIC,
)


async def async_setup_entry(
    hass: HomeAssistant, entry: ConfigEntry, async_add_entities: AddEntitiesCallback
) -> None:
    """Set up iAlarm Zone Status sensors."""
    ialarm_coordinator: IAlarmCoordinator = hass.data[DOMAIN][entry.entry_id][
        DATA_COORDINATOR
    ]
    async_add_entities([IAlarmSensorEntity(ialarm_coordinator)], False)


class IAlarmSensorEntity(CoordinatorEntity[IAlarmCoordinator], SensorEntity):
    """IAlarm sensor device."""

    def __init__(self, coordinator: IAlarmCoordinator) -> None:
        """Create the entity with a DataUpdateCoordinator."""
        super().__init__(coordinator)
        self.entity_description = SENSOR_IALARM_ZONE_STATUS
        self._attr_unique_id = f"{coordinator.mac}-ialarm_zone_status"
        self._attr_extra_state_attributes: dict[str, Any] = {}
        self._attr_native_value = "ialarm_zone_status"
        self.name = "ialarm_zone_status"

    @callback
    def _handle_coordinator_update(self) -> None:
        """Handle updated data from the coordinator."""
        available = False

        ialarm_status_data: IAlarmStatusType = self.coordinator.data
        if ialarm_status_data:
            zone_list_infos: list[ZoneStatusType] = ialarm_status_data[
                "zone_status_list"
            ]

            for zone in zone_list_infos:
                zone_id = zone.get("zone_id")
                zone_name = zone.get("name")
                zone_status_type: list[StatusType] = zone.get("types")
                _LOGGER.debug(
                    "Zone ID: %s, Name: %s, Status Types: %s",
                    zone_id,
                    zone_name,
                    zone_status_type,
                )

                if zone_id is not None and zone_name is not None:
                    self._attr_extra_state_attributes[f"zone_{zone_id}_name"] = (
                        zone_name
                    )
                    zone_status_list = [
                        status_type.name
                        for status_type in zone_status_type
                        if isinstance(status_type, StatusType)
                    ]
                    self._attr_extra_state_attributes[f"zone_{zone_id}_status"] = (
                        ", ".join(zone_status_list)
                    )

        self._attr_available = available
        self.async_write_ha_state()
