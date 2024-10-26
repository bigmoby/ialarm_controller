"""Interfaces with iAlarm control panels."""

from __future__ import annotations

import logging

from homeassistant.components import persistent_notification
from homeassistant.components.alarm_control_panel import (
    AlarmControlPanelEntity,
    AlarmControlPanelEntityFeature,
)
from homeassistant.core import HomeAssistant
from homeassistant.helpers import entity_platform
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from custom_components.ialarm_controller.entity import IAlarmEntity

from . import IAlarmConfigEntry
from .const import (
    ENTITY_SERVICES,
    NOTIFICATION_ID,
    NOTIFICATION_TITLE,
    IAlarmStatusType,
)
from .coordinator import IAlarmCoordinator

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(
    hass: HomeAssistant,
    config_entry: IAlarmConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up a iAlarm alarm control panel based on a config entry."""
    ialarm_coordinator = config_entry.runtime_data
    unique_id = config_entry.unique_id
    async_add_entities(
        [IAlarmPanel(ialarm_coordinator, unique_id, config_entry.title)], False
    )

    platform = entity_platform.async_get_current_platform()

    for service_name, service_schema in ENTITY_SERVICES.items():
        platform.async_register_entity_service(
            service_name, service_schema, f"async_{service_name}"
        )


class IAlarmPanel(IAlarmEntity, AlarmControlPanelEntity):
    """Representation of an iAlarm device."""

    _attr_has_entity_name = True
    _attr_name = "iAlarm panel"
    _attr_supported_features = (
        AlarmControlPanelEntityFeature.ARM_HOME
        | AlarmControlPanelEntityFeature.ARM_AWAY
    )
    _attr_code_arm_required = False

    def __init__(
        self, coordinator: IAlarmCoordinator, unique_id: str, name: str
    ) -> None:
        """Create the entity with a DataUpdateCoordinator."""
        super().__init__(coordinator, unique_id, name)

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
            _LOGGER.error(
                "Failed to disarm the alarm system. Please enter the disarm code."
            )
            persistent_notification.create(
                self.hass,
                "Failed to disarm the alarm system.<br/>Please enter the disarm code.",
                title=NOTIFICATION_TITLE,
                notification_id=NOTIFICATION_ID,
            )
            return
        await self.coordinator.ialarm_device.disarm()
        await self.coordinator.ialarm_device.cancel_alarm()
        if self.coordinator.send_events:
            self.hass.bus.async_fire("ialarm_disarm", {"alarm_status": "DISARMED"})

    async def async_alarm_arm_home(self, code: str | None = None) -> None:
        """Send arm home command."""
        await self.coordinator.ialarm_device.arm_stay()
        if self.coordinator.send_events:
            self.hass.bus.async_fire("ialarm_arm_stay", {"alarm_status": "ARMED HOME"})

    async def async_alarm_arm_away(self, code: str | None = None) -> None:
        """Send arm away command."""
        await self.coordinator.ialarm_device.arm_away()
        if self.coordinator.send_events:
            self.hass.bus.async_fire("ialarm_arm_away", {"alarm_status": "ARMED AWAY"})
