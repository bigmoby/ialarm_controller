"""Interfaces with iAlarm control panels."""

from __future__ import annotations

import logging

from homeassistant.components import persistent_notification
from homeassistant.components.alarm_control_panel import AlarmControlPanelEntity
from homeassistant.components.alarm_control_panel.const import (
    AlarmControlPanelEntityFeature,
    AlarmControlPanelState,
    CodeFormat,
)
from homeassistant.core import HomeAssistant, ServiceResponse, callback
from homeassistant.helpers.entity_platform import AddConfigEntryEntitiesCallback

from .const import (
    CONF_REQUIRE_CODE_TO_ARM,
    CONF_REQUIRE_CODE_TO_DISARM,
    DEFAULT_REQUIRE_CODE_TO_ARM,
    DEFAULT_REQUIRE_CODE_TO_DISARM,
    NOTIFICATION_ID,
    NOTIFICATION_TITLE,
    SERVICE_GET_LOG_MAX_ENTRIES,
)
from .coordinator import IAlarmConfigEntry, IAlarmCoordinator
from .entity import IAlarmEntity

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(
    hass: HomeAssistant,
    config_entry: IAlarmConfigEntry,
    async_add_entities: AddConfigEntryEntitiesCallback,
) -> None:
    """Set up a iAlarm alarm control panel based on a config entry."""
    ialarm_coordinator = config_entry.runtime_data
    if not (unique_id := config_entry.unique_id):
        return
    async_add_entities(
        [IAlarmPanel(ialarm_coordinator, config_entry, unique_id, config_entry.title)],
        False,
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
    _attr_code_format: CodeFormat | None = CodeFormat.NUMBER

    def __init__(
        self,
        coordinator: IAlarmCoordinator,
        config_entry: IAlarmConfigEntry,
        unique_id: str,
        name: str,
    ) -> None:
        """Create the entity with a DataUpdateCoordinator."""
        super().__init__(coordinator, unique_id, name)

        self._require_code_to_arm = config_entry.options.get(
            CONF_REQUIRE_CODE_TO_ARM,
            config_entry.data.get(
                CONF_REQUIRE_CODE_TO_ARM, DEFAULT_REQUIRE_CODE_TO_ARM
            ),
        )
        self._require_code_to_disarm = config_entry.options.get(
            CONF_REQUIRE_CODE_TO_DISARM,
            config_entry.data.get(
                CONF_REQUIRE_CODE_TO_DISARM, DEFAULT_REQUIRE_CODE_TO_DISARM
            ),
        )

        self._attr_code_arm_required = self._require_code_to_arm

        if self._require_code_to_arm or self._require_code_to_disarm:
            self._attr_code_format = CodeFormat.NUMBER
        else:
            self._attr_code_format = None

        if coordinator.data:
            self._attr_alarm_state = coordinator.data.get("ialarm_status")

    @callback
    def _handle_coordinator_update(self) -> None:
        """Handle updated data from the coordinator."""
        if self.coordinator.data:
            self._attr_alarm_state = self.coordinator.data.get("ialarm_status")
        super()._handle_coordinator_update()

    async def async_get_log(
        self, max_entries: int = SERVICE_GET_LOG_MAX_ENTRIES
    ) -> ServiceResponse:
        """Retrieve the last n log entries (get_log service)."""
        return await self.coordinator.async_get_log(max_entries)

    async def async_alarm_disarm(self, code: str | None = None) -> None:
        """Send disarm command, then ensure any active alarm is cleared."""
        if self._require_code_to_disarm and (code is None or code == ""):
            _LOGGER.error(
                "Failed to disarm the alarm system. Please enter the disarm code."
            )
            persistent_notification.async_create(
                self.hass,
                "Failed to disarm the alarm system.<br/>Please enter the disarm code.",
                title=NOTIFICATION_TITLE,
                notification_id=NOTIFICATION_ID,
            )
            return

        cleared = await self.coordinator.async_disarm_and_cancel()

        if not cleared:
            _LOGGER.warning(
                "iAlarm: disarm sent but panel did not confirm a non-triggered "
                "state after all cancel attempts."
            )

        self.coordinator.async_set_alarm_status(AlarmControlPanelState.DISARMED)

        if self.coordinator.send_events:
            _LOGGER.debug("Event ialarm_disarm was triggered")
            self.hass.bus.async_fire(
                event_type="ialarm_disarm",
                event_data={
                    "device_id": self.entity_id,
                    "type": "alarm_status",
                    "alarm_status": "DISARMED",
                },
            )

    async def async_alarm_arm_home(self, code: str | None = None) -> None:
        """Send arm home command."""
        if self._require_code_to_arm and (code is None or code == ""):
            _LOGGER.error("Failed to arm home the alarm system. Please enter the code.")
            persistent_notification.async_create(
                self.hass,
                "Failed to arm home the alarm system.<br/>Please enter the code.",
                title=NOTIFICATION_TITLE,
                notification_id=NOTIFICATION_ID,
            )
            return
        await self.coordinator.async_arm_stay()
        self.coordinator.async_set_alarm_status(AlarmControlPanelState.ARMED_HOME)
        if self.coordinator.send_events:
            _LOGGER.debug("Event ialarm_arm_stay was triggered")
            self.hass.bus.async_fire(
                event_type="ialarm_arm_stay", event_data={"alarm_status": "ARMED HOME"}
            )

    async def async_alarm_arm_away(self, code: str | None = None) -> None:
        """Send arm away command."""
        if self._require_code_to_arm and (code is None or code == ""):
            _LOGGER.error("Failed to arm away the alarm system. Please enter the code.")
            persistent_notification.async_create(
                self.hass,
                "Failed to arm away the alarm system.<br/>Please enter the code.",
                title=NOTIFICATION_TITLE,
                notification_id=NOTIFICATION_ID,
            )
            return
        await self.coordinator.async_arm_away()
        self.coordinator.async_set_alarm_status(AlarmControlPanelState.ARMED_AWAY)
        if self.coordinator.send_events:
            _LOGGER.debug("Event ialarm_arm_away was triggered")
            self.hass.bus.async_fire(
                event_type="ialarm_arm_away", event_data={"alarm_status": "ARMED AWAY"}
            )
