"""Test the iAlarm alarm control panel."""

from unittest.mock import AsyncMock

from homeassistant.components.alarm_control_panel import DOMAIN as ALARM_DOMAIN
from homeassistant.const import (
    ATTR_ENTITY_ID,
    SERVICE_ALARM_ARM_AWAY,
    SERVICE_ALARM_ARM_HOME,
    SERVICE_ALARM_DISARM,
)
from homeassistant.core import HomeAssistant


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
        {ATTR_ENTITY_ID: entity_id},
        blocking=True,
    )
    ialarm_api.return_value.arm_away.assert_awaited_once()

    # Test arm home
    ialarm_api.return_value.arm_stay = AsyncMock()
    await hass.services.async_call(
        ALARM_DOMAIN,
        SERVICE_ALARM_ARM_HOME,
        {ATTR_ENTITY_ID: entity_id},
        blocking=True,
    )
    ialarm_api.return_value.arm_stay.assert_awaited_once()

    # Test disarm without code
    ialarm_api.return_value.disarm = AsyncMock()
    ialarm_api.return_value.cancel_alarm = AsyncMock()
    await hass.services.async_call(
        ALARM_DOMAIN,
        SERVICE_ALARM_DISARM,
        {ATTR_ENTITY_ID: entity_id},
        blocking=True,
    )
    # Should not call disarm if no code is provided
    ialarm_api.return_value.disarm.assert_not_called()

    # Test disarm with empty code
    await hass.services.async_call(
        ALARM_DOMAIN,
        SERVICE_ALARM_DISARM,
        {ATTR_ENTITY_ID: entity_id, "code": ""},
        blocking=True,
    )
    ialarm_api.return_value.disarm.assert_not_called()

    # Test disarm with code
    await hass.services.async_call(
        ALARM_DOMAIN,
        SERVICE_ALARM_DISARM,
        {ATTR_ENTITY_ID: entity_id, "code": "1234"},
        blocking=True,
    )
    ialarm_api.return_value.disarm.assert_awaited_once()
    ialarm_api.return_value.cancel_alarm.assert_awaited_once()


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
