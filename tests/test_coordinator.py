"""Test the iAlarm coordinator."""

from unittest.mock import AsyncMock

from homeassistant.components.alarm_control_panel import AlarmControlPanelState
from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import UpdateFailed
from pyasyncialarm.const import StatusType
from pyasyncialarm.pyasyncialarm import IAlarm
import pytest


async def test_coordinator_update_data(
    hass: HomeAssistant,
    mock_config_entry,
    ialarm_api,
) -> None:
    """Test fetching data from the API."""
    ialarm_api.return_value.get_mac = AsyncMock(return_value="00:11:22:33:44:55")
    ialarm_api.return_value.get_zone_status = AsyncMock(
        return_value=[
            {"zone_id": 1, "name": "Main Door", "types": [StatusType.ZONE_ALARM]}
        ]
    )
    ialarm_api.return_value.get_status = AsyncMock(
        return_value={
            "status_value": IAlarm.TRIGGERED,
            "alarmed_zones": [{"zone_id": 1, "name": "Main Door"}],
        }
    )

    mock_config_entry.add_to_hass(hass)

    events = []
    hass.bus.async_listen("ialarm_triggered", events.append)

    await hass.config_entries.async_setup(mock_config_entry.entry_id)
    await hass.async_block_till_done()

    coordinator = mock_config_entry.runtime_data
    await coordinator.async_request_refresh()
    await hass.async_block_till_done()

    # The setup does a first refresh, and we just did a second one. Both fire an event.
    assert coordinator.data["ialarm_status"] == AlarmControlPanelState.TRIGGERED
    assert len(coordinator.data["zone_status_list"]) == 1

    # Check event bus for the trigger event
    assert len(events) > 0


async def test_coordinator_update_error(
    hass: HomeAssistant,
    mock_config_entry,
    ialarm_api,
) -> None:
    """Test UpdateFailed when ConnectionError occurs."""
    ialarm_api.return_value.get_mac = AsyncMock(return_value="00:11:22:33:44:55")
    mock_config_entry.add_to_hass(hass)

    await hass.config_entries.async_setup(mock_config_entry.entry_id)
    await hass.async_block_till_done()

    coordinator = mock_config_entry.runtime_data

    ialarm_api.return_value.get_zone_status.side_effect = ConnectionError
    with pytest.raises(UpdateFailed):
        await coordinator._async_update_data()


async def test_coordinator_cancel_alarm(
    hass: HomeAssistant,
    mock_config_entry,
    ialarm_api,
) -> None:
    """Test cancel alarm."""
    ialarm_api.return_value.get_mac = AsyncMock(return_value="00:11:22:33:44:55")
    mock_config_entry.add_to_hass(hass)
    await hass.config_entries.async_setup(mock_config_entry.entry_id)
    await hass.async_block_till_done()

    coordinator = mock_config_entry.runtime_data
    ialarm_api.return_value.cancel_alarm = AsyncMock()

    events = []
    hass.bus.async_listen("cancel_alarm", events.append)

    coordinator.send_events = True
    await coordinator.async_cancel_alarm()
    await hass.async_block_till_done()
    ialarm_api.return_value.cancel_alarm.assert_awaited_once()
    assert len(events) > 0


async def test_coordinator_get_log(
    hass: HomeAssistant,
    mock_config_entry,
    ialarm_api,
) -> None:
    """Test get log."""
    ialarm_api.return_value.get_mac = AsyncMock(return_value="00:11:22:33:44:55")
    mock_config_entry.add_to_hass(hass)
    await hass.config_entries.async_setup(mock_config_entry.entry_id)
    await hass.async_block_till_done()

    coordinator = mock_config_entry.runtime_data
    ialarm_api.return_value.get_last_log_entries = AsyncMock(
        return_value=[{"time": "12:00", "area": "0", "event": "arm", "name": "user"}]
    )

    response = await coordinator.async_get_log()
    assert response["items"][0]["time"] == "12:00"

    ialarm_api.return_value.get_last_log_entries = AsyncMock(return_value=[])
    response_empty = await coordinator.async_get_log()
    assert response_empty == {"items": []}
