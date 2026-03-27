"""Test the iAlarm alarm control panel."""

from unittest.mock import AsyncMock

from custom_components.ialarm_controller.alarm_control_panel import IAlarmPanel
from homeassistant.components.alarm_control_panel import DOMAIN as ALARM_DOMAIN
from homeassistant.const import (
    ATTR_ENTITY_ID,
    CONF_EVENT,
    SERVICE_ALARM_ARM_AWAY,
    SERVICE_ALARM_ARM_HOME,
    SERVICE_ALARM_DISARM,
)
from homeassistant.core import HomeAssistant, callback
from homeassistant.exceptions import ServiceValidationError
from homeassistant.helpers import entity_registry as er
import pytest


async def test_alarm_control_panel_actions(
    hass: HomeAssistant,
    mock_config_entry,
    ialarm_api,
) -> None:
    """Test the alarm control panel actions."""
    ialarm_api.return_value.get_mac = AsyncMock(return_value="00:11:22:33:44:55")
    ialarm_api.return_value.get_zone_status = AsyncMock(return_value=[])
    ialarm_api.return_value.get_status = AsyncMock(
        return_value={"status_value": 0, "alarmed_zones": []}
    )

    mock_config_entry.add_to_hass(hass)
    assert await hass.config_entries.async_setup(mock_config_entry.entry_id)
    await hass.async_block_till_done()

    entity_id = "alarm_control_panel.mock_ialarm_config_entry_ialarm_panel"

    state = hass.states.get(entity_id)
    assert state is not None

    # Test arm away
    ialarm_api.return_value.arm_away = AsyncMock()
    await hass.services.async_call(
        ALARM_DOMAIN,
        SERVICE_ALARM_ARM_AWAY,
        {ATTR_ENTITY_ID: entity_id, "code": "1234"},
        blocking=True,
    )
    ialarm_api.return_value.arm_away.assert_awaited_once()

    # Test arm away without code — should fail (HA ServiceValidationError)

    ialarm_api.return_value.arm_away.reset_mock()
    with pytest.raises(ServiceValidationError):
        await hass.services.async_call(
            ALARM_DOMAIN,
            SERVICE_ALARM_ARM_AWAY,
            {ATTR_ENTITY_ID: entity_id},
            blocking=True,
        )
    ialarm_api.return_value.arm_away.assert_not_called()

    # Test arm home
    ialarm_api.return_value.arm_stay = AsyncMock()
    await hass.services.async_call(
        ALARM_DOMAIN,
        SERVICE_ALARM_ARM_HOME,
        {ATTR_ENTITY_ID: entity_id, "code": "1234"},
        blocking=True,
    )
    ialarm_api.return_value.arm_stay.assert_awaited_once()

    # Test arm home without code — should fail (HA ServiceValidationError)
    ialarm_api.return_value.arm_stay.reset_mock()
    with pytest.raises(ServiceValidationError):
        await hass.services.async_call(
            ALARM_DOMAIN,
            SERVICE_ALARM_ARM_HOME,
            {ATTR_ENTITY_ID: entity_id},
            blocking=True,
        )
    ialarm_api.return_value.arm_stay.assert_not_called()

    # Test disarm without code (None) — should fail (not call API)
    ialarm_api.return_value.disarm = AsyncMock()
    ialarm_api.return_value.cancel_alarm = AsyncMock()
    await hass.services.async_call(
        ALARM_DOMAIN,
        SERVICE_ALARM_DISARM,
        {ATTR_ENTITY_ID: entity_id},
        blocking=True,
    )
    ialarm_api.return_value.disarm.assert_not_called()

    # Test disarm with empty code — should fail
    await hass.services.async_call(
        ALARM_DOMAIN,
        SERVICE_ALARM_DISARM,
        {ATTR_ENTITY_ID: entity_id, "code": ""},
        blocking=True,
    )
    ialarm_api.return_value.disarm.assert_not_called()

    # Test disarm with code — should succeed
    await hass.services.async_call(
        ALARM_DOMAIN,
        SERVICE_ALARM_DISARM,
        {ATTR_ENTITY_ID: entity_id, "code": "1234"},
        blocking=True,
    )
    ialarm_api.return_value.disarm.assert_awaited_once()
    ialarm_api.return_value.cancel_alarm.assert_awaited_once()

    # Test direct calls to verify internal validation and notifications (bypassing HA service schema)
    # This ensures 100% test coverage of our custom safety logic

    registry = er.async_get(hass)
    entry = registry.async_get(entity_id)
    assert entry is not None

    # Get the actual entity object from the platform
    # In tests, we can find it in hass.data
    # However, a simpler way is to find it via the coordinator
    ialarm_coordinator = mock_config_entry.runtime_data
    panel_entity = IAlarmPanel(
        ialarm_coordinator, mock_config_entry.unique_id, mock_config_entry.title
    )
    panel_entity.hass = hass

    # Test internal disarm validation
    ialarm_api.return_value.disarm.reset_mock()
    await panel_entity.async_alarm_disarm(None)
    ialarm_api.return_value.disarm.assert_not_called()

    await panel_entity.async_alarm_disarm("")
    ialarm_api.return_value.disarm.assert_not_called()

    # Test internal arm validation
    ialarm_api.return_value.arm_away.reset_mock()
    await panel_entity.async_alarm_arm_away(None)
    ialarm_api.return_value.arm_away.assert_not_called()

    ialarm_api.return_value.arm_stay.reset_mock()
    await panel_entity.async_alarm_arm_home(None)
    ialarm_api.return_value.arm_stay.assert_not_called()


async def test_alarm_control_panel_no_state(
    hass: HomeAssistant,
    mock_config_entry,
    ialarm_api,
) -> None:
    """Test the alarm control panel when state is none."""
    ialarm_api.return_value.get_mac = AsyncMock(return_value="00:11:22:33:44:55")
    ialarm_api.return_value.get_zone_status = AsyncMock(return_value=[])
    ialarm_api.return_value.get_status = AsyncMock(
        return_value={"status_value": 999, "alarmed_zones": []}  # Unmapped status
    )

    mock_config_entry.add_to_hass(hass)
    assert await hass.config_entries.async_setup(mock_config_entry.entry_id)
    await hass.async_block_till_done()

    entity_id = "alarm_control_panel.mock_ialarm_config_entry_ialarm_panel"
    state = hass.states.get(entity_id)
    assert state.state == "unknown"


async def test_alarm_control_panel_send_events(
    hass: HomeAssistant,
    mock_config_entry,
    ialarm_api,
) -> None:
    """Test the alarm control panel with send_events enabled."""
    mock_config_entry.add_to_hass(hass)

    hass.config_entries.async_update_entry(
        mock_config_entry, options={CONF_EVENT: True}
    )
    ialarm_api.return_value.disarm = AsyncMock()
    ialarm_api.return_value.cancel_alarm = AsyncMock()
    ialarm_api.return_value.arm_away = AsyncMock()
    ialarm_api.return_value.arm_stay = AsyncMock()

    assert await hass.config_entries.async_setup(mock_config_entry.entry_id)
    await hass.async_block_till_done()

    entity_id = "alarm_control_panel.mock_ialarm_config_entry_ialarm_panel"

    # Track events
    events = []

    @callback
    def listener(event):
        events.append(event)

    hass.bus.async_listen("ialarm_disarm", listener)
    hass.bus.async_listen("ialarm_arm_away", listener)
    hass.bus.async_listen("ialarm_arm_stay", listener)

    # Test disarm fires event
    await hass.services.async_call(
        ALARM_DOMAIN,
        SERVICE_ALARM_DISARM,
        {ATTR_ENTITY_ID: entity_id, "code": "1234"},
        blocking=True,
    )
    assert any(e.event_type == "ialarm_disarm" for e in events)

    # Test arm away fires event
    await hass.services.async_call(
        ALARM_DOMAIN,
        SERVICE_ALARM_ARM_AWAY,
        {ATTR_ENTITY_ID: entity_id, "code": "1234"},
        blocking=True,
    )
    assert any(e.event_type == "ialarm_arm_away" for e in events)

    # Test arm home fires event
    await hass.services.async_call(
        ALARM_DOMAIN,
        SERVICE_ALARM_ARM_HOME,
        {ATTR_ENTITY_ID: entity_id, "code": "1234"},
        blocking=True,
    )
    assert any(e.event_type == "ialarm_arm_stay" for e in events)


async def test_alarm_control_panel_state_property_none(
    hass: HomeAssistant,
    mock_config_entry,
    ialarm_api,
) -> None:
    """Test the alarm control panel state property returns None when coordinator state is None."""

    mock_config_entry.add_to_hass(hass)
    assert await hass.config_entries.async_setup(mock_config_entry.entry_id)
    await hass.async_block_till_done()

    coordinator = mock_config_entry.runtime_data
    coordinator.state = None
    panel = IAlarmPanel(
        coordinator, mock_config_entry.unique_id, mock_config_entry.title
    )
    assert panel.state is None
