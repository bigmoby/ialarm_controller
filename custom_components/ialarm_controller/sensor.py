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

    _has_alarm = False
    _has_anomaly = False

    def _update_attr_name(self) -> None:
        if self._has_alarm and self._has_anomaly:
            self._attr_native_value = "triggered; anomaly detected"
        elif self._has_alarm:
            self._attr_native_value = "triggered"
        elif self._has_anomaly:
            self._attr_native_value = "anomaly detected"
        else:
            self._attr_native_value = "running"

    def _get_sensor_data_attributes(self) -> dict[str, str]:
        """Get iAlarm status data."""
        domain = self.coordinator.config_entry.domain
        ialarm_status_data = self.coordinator.data

        result: dict[str, str] = {}
        result["Integration"] = domain

        if not ialarm_status_data:
            self._update_attr_name()
            return result

        for zone in ialarm_status_data.get("zone_status_list", []):
            zone_id = zone.get("zone_id")
            zone_name = zone.get("name") or "N.A."
            zone_status_alert_type = zone.get("types")

            _LOGGER.debug(
                "Zone ID: %s, Name: %s, Status Types: %s",
                zone_id,
                zone_name,
                zone_status_alert_type,
            )

            if not (zone_id and zone_name):
                continue

            if zone_status_alert_type:
                zone_status_list_for_zone = [
                    status_type.name
                    for status_type in zone_status_alert_type
                    if isinstance(status_type, StatusType)
                ]
                if zone_status_list_for_zone:
                    result[f"Zone {zone_id} ({zone_name})"] = (
                        f"{', '.join(zone_status_list_for_zone)}"
                    )

                if "ZONE_ALARM" in zone_status_list_for_zone:
                    self._has_alarm = True
                if any(
                    status not in {"ZONE_NOT_USED", "ZONE_IN_USE", "ZONE_ALARM"}
                    for status in zone_status_list_for_zone
                ):
                    self._has_anomaly = True

        self._update_attr_name()
        return result

    def __init__(
        self, coordinator: IAlarmCoordinator, unique_id: str, name: str
    ) -> None:
        """Create the entity with a DataUpdateCoordinator."""
        super().__init__(coordinator, unique_id, name)
        self._attr_name = "Zone status"
        self._attr_icon = "mdi:hazard-lights"
        self._update_attr_name()
        self.entity_description = IAlarmZoneStatusSensorDescription
        self._attr_extra_state_attributes = self._get_sensor_data_attributes()

    @callback
    def _handle_coordinator_update(self) -> None:
        """Handle updated data from the coordinator."""
        self._attr_extra_state_attributes = self._get_sensor_data_attributes()
        self.async_write_ha_state()
