"""Support for sensors."""

from __future__ import annotations

import logging

from homeassistant.components.sensor import SensorEntity, SensorEntityDescription
from homeassistant.const import EntityCategory
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from pyasyncialarm.const import StatusType

from custom_components.ialarm_controller.entity import IAlarmEntity

from . import IAlarmConfigEntry
from .const import IAlarmStatusType
from .coordinator import IAlarmCoordinator

_LOGGER = logging.getLogger(__name__)

IAlarmZoneStatusSensorDescription = SensorEntityDescription(
    key="ALARMS",
    translation_key="alarms",
    entity_category=EntityCategory.DIAGNOSTIC,
)


async def async_setup_entry(
    hass: HomeAssistant,
    config_entry: IAlarmConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up iAlarm Zone Status sensors."""
    ialarm_coordinator = config_entry.runtime_data
    unique_id = config_entry.unique_id
    async_add_entities(
        [IAlarmSensorEntity(ialarm_coordinator, unique_id, config_entry.title)], True
    )


class IAlarmSensorEntity(IAlarmEntity, SensorEntity):
    """IAlarm sensor device."""

    @staticmethod
    def _get_sensor_data_attributes(
        ialarm_status_data: IAlarmStatusType,
    ) -> dict[str, str]:
        """Get iAlarm status data."""
        result: dict[str, str] = {}

        if not ialarm_status_data:
            return result

        for zone in ialarm_status_data.get("zone_status_list", []):
            zone_id = zone.get("zone_id")
            zone_name = zone.get("name")
            zone_status_type = zone.get("types")

            _LOGGER.debug(
                "Zone ID: %s, Name: %s, Status Types: %s",
                zone_id,
                zone_name,
                zone_status_type,
            )

            if not (zone_id and zone_name):
                continue

            result[f"zone_{zone_id}_name"] = zone_name

            if zone_status_type:
                zone_status_list = [
                    status_type.name
                    for status_type in zone_status_type
                    if isinstance(status_type, StatusType)
                ]
                if zone_status_list:
                    result[f"zone_{zone_id}_status"] = ", ".join(zone_status_list)

        return result

    def __init__(
        self, coordinator: IAlarmCoordinator, unique_id: str, name: str
    ) -> None:
        """Create the entity with a DataUpdateCoordinator."""
        super().__init__(coordinator, unique_id, name)
        self._attr_name = "iAlarm Zone status"
        self._attr_native_value = "[...see Attributes section]"
        self.entity_description = IAlarmZoneStatusSensorDescription
        self._attr_extra_state_attributes = self._get_sensor_data_attributes(
            self.coordinator.data
        )

    @callback
    def _handle_coordinator_update(self) -> None:
        """Handle updated data from the coordinator."""
        self._attr_extra_state_attributes = self._get_sensor_data_attributes(
            self.coordinator.data
        )
        self.async_write_ha_state()
