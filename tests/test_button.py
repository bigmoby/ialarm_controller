"""Test the iAlarm buttons."""

from unittest.mock import AsyncMock

from homeassistant.components.button import DOMAIN as BUTTON_DOMAIN, SERVICE_PRESS
from homeassistant.const import ATTR_ENTITY_ID
from homeassistant.core import HomeAssistant


async def test_button_cancel_alarm(
    hass: HomeAssistant,
    mock_config_entry,
    ialarm_api,
) -> None:
    """Test the cancel alarm button."""
    ialarm_api.return_value.get_mac = AsyncMock(return_value="00:11:22:33:44:55")
    ialarm_api.return_value.get_zone_status = AsyncMock(return_value=[])
    ialarm_api.return_value.get_status = AsyncMock(
        return_value={"status_value": 0, "alarmed_zones": []}
    )

    mock_config_entry.add_to_hass(hass)
    assert await hass.config_entries.async_setup(mock_config_entry.entry_id)
    await hass.async_block_till_done()

    entity_id = "button.mock_ialarm_config_entry_cancel_alarm_alerts"

    # We stub the coordinator's methods to see if the button reaches the API
    ialarm_api.return_value.cancel_alarm = AsyncMock()

    await hass.services.async_call(
        BUTTON_DOMAIN,
        SERVICE_PRESS,
        {ATTR_ENTITY_ID: entity_id},
        blocking=True,
    )

    ialarm_api.return_value.cancel_alarm.assert_awaited_once()


async def test_button_get_log(
    hass: HomeAssistant,
    mock_config_entry,
    ialarm_api,
) -> None:
    """Test the get log button."""
    ialarm_api.return_value.get_mac = AsyncMock(return_value="00:11:22:33:44:55")
    ialarm_api.return_value.get_zone_status = AsyncMock(return_value=[])
    ialarm_api.return_value.get_status = AsyncMock(
        return_value={"status_value": 0, "alarmed_zones": []}
    )

    mock_config_entry.add_to_hass(hass)
    assert await hass.config_entries.async_setup(mock_config_entry.entry_id)
    await hass.async_block_till_done()

    entity_id = "button.mock_ialarm_config_entry_log_alerts"

    ialarm_api.return_value.get_last_log_entries = AsyncMock(return_value=[])

    await hass.services.async_call(
        BUTTON_DOMAIN,
        SERVICE_PRESS,
        {ATTR_ENTITY_ID: entity_id},
        blocking=True,
    )

    ialarm_api.return_value.get_last_log_entries.assert_awaited_once()
