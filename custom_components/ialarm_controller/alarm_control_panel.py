"""Interfaces with iAlarm control panels."""

from __future__ import annotations

import asyncio
import logging

from homeassistant.components import persistent_notification
from homeassistant.components.alarm_control_panel import (
    AlarmControlPanelEntity,
    AlarmControlPanelEntityFeature,
    CodeFormat,
)
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers import entity_platform
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from custom_components.ialarm_controller.entity import IAlarmEntity

from . import IAlarmConfigEntry
from .const import ENTITY_SERVICES, NOTIFICATION_ID, NOTIFICATION_TITLE
from .coordinator import IAlarmCoordinator

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(
    hass: HomeAssistant,
    config_entry: IAlarmConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up a iAlarm alarm control panel based on a config entry."""
    ialarm_coordinator = config_entry.runtime_data
    if not (unique_id := config_entry.unique_id):
        return
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
    _attr_code_arm_required = True
    _attr_code_format = CodeFormat.NUMBER

    def __init__(
        self, coordinator: IAlarmCoordinator, unique_id: str, name: str
    ) -> None:
        """Create the entity with a DataUpdateCoordinator."""
        super().__init__(coordinator, unique_id, name)
        if coordinator.data:
            self._attr_alarm_state = coordinator.data.get("ialarm_status")

    @callback
    def _handle_coordinator_update(self) -> None:
        """Handle updated data from the coordinator."""
        if self.coordinator.data:
            self._attr_alarm_state = self.coordinator.data.get("ialarm_status")
        super()._handle_coordinator_update()

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

        # Give the alarm panel time to process the disarm command and release the socket
        # before sending the cancel_alarm command. This prevents socket timeouts.
        await asyncio.sleep(2)

        await self.coordinator.ialarm_device.cancel_alarm()

        if self.coordinator.send_events:
            _LOGGER.debug("Event ialarm_disarm was triggered")
            event_data = {
                "device_id": self.entity_id,
                "type": "alarm_status",
                "alarm_status": "DISARMED",
            }
            self.hass.bus.async_fire(event_type="ialarm_disarm", event_data=event_data)

    async def async_alarm_arm_home(self, code: str | None = None) -> None:
        """Send arm home command."""
        # Require a code to be passed for arm operations
        if code is None or code == "":
            _LOGGER.error("Failed to arm home the alarm system. Please enter the code.")
            persistent_notification.create(
                self.hass,
                "Failed to arm home the alarm system.<br/>Please enter the code.",
                title=NOTIFICATION_TITLE,
                notification_id=NOTIFICATION_ID,
            )
            return
        await self.coordinator.ialarm_device.arm_stay()
        if self.coordinator.send_events:
            _LOGGER.debug("Event ialarm_arm_stay was triggered")
            self.hass.bus.async_fire(
                event_type="ialarm_arm_stay", event_data={"alarm_status": "ARMED HOME"}
            )

    async def async_alarm_arm_away(self, code: str | None = None) -> None:
        """Send arm away command."""
        # Require a code to be passed for arm operations
        if code is None or code == "":
            _LOGGER.error("Failed to arm away the alarm system. Please enter the code.")
            persistent_notification.create(
                self.hass,
                "Failed to arm away the alarm system.<br/>Please enter the code.",
                title=NOTIFICATION_TITLE,
                notification_id=NOTIFICATION_ID,
            )
            return
        await self.coordinator.ialarm_device.arm_away()
        if self.coordinator.send_events:
            _LOGGER.debug("Event ialarm_arm_away was triggered")
            self.hass.bus.async_fire(
                event_type="ialarm_arm_away", event_data={"alarm_status": "ARMED AWAY"}
            )
