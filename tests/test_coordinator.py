"""Test the iAlarm coordinator."""

import asyncio
from unittest.mock import AsyncMock, patch

from homeassistant.components.alarm_control_panel import AlarmControlPanelState
from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import UpdateFailed
from pyasyncialarm.const import StatusType
from pyasyncialarm.pyasyncialarm import IAlarm
import pytest
from pytest_homeassistant_custom_component.common import async_capture_events


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

    events = async_capture_events(hass, "ialarm_logs")
    response = await coordinator.async_get_log()
    await hass.async_block_till_done()
    assert response["items"][0]["time"] == "12:00"
    assert len(events) == 1
    assert events[0].data == response

    ialarm_api.return_value.get_last_log_entries = AsyncMock(return_value=[])
    response_empty = await coordinator.async_get_log()
    assert response_empty == {"items": []}


async def test_coordinator_arm_commands(
    hass: HomeAssistant,
    mock_config_entry,
    ialarm_api,
) -> None:
    """Test coordinator arm and disarm methods."""
    ialarm_api.return_value.get_mac = AsyncMock(return_value="00:11:22:33:44:55")
    mock_config_entry.add_to_hass(hass)
    await hass.config_entries.async_setup(mock_config_entry.entry_id)
    await hass.async_block_till_done()

    coordinator = mock_config_entry.runtime_data
    ialarm_api.return_value.arm_stay = AsyncMock()
    ialarm_api.return_value.arm_away = AsyncMock()
    ialarm_api.return_value.disarm_and_cancel = AsyncMock(return_value=True)

    await coordinator.async_arm_stay()
    ialarm_api.return_value.arm_stay.assert_awaited_once()

    await coordinator.async_arm_away()
    ialarm_api.return_value.arm_away.assert_awaited_once()

    result = await coordinator.async_disarm_and_cancel()
    ialarm_api.return_value.disarm_and_cancel.assert_awaited_once()
    assert result is True


async def test_coordinator_io_lock_serialization(
    hass: HomeAssistant,
    mock_config_entry,
    ialarm_api,
) -> None:
    """Test that concurrent operations are serialized by _io_lock."""
    ialarm_api.return_value.get_mac = AsyncMock(return_value="00:11:22:33:44:55")
    mock_config_entry.add_to_hass(hass)
    await hass.config_entries.async_setup(mock_config_entry.entry_id)
    await hass.async_block_till_done()

    coordinator = mock_config_entry.runtime_data

    execution_order: list[str] = []

    async def slow_arm() -> None:
        execution_order.append("slow_arm_start")
        await asyncio.sleep(0.05)
        execution_order.append("slow_arm_end")

    async def fast_cancel() -> None:
        execution_order.append("fast_cancel_start")
        execution_order.append("fast_cancel_end")

    ialarm_api.return_value.arm_away = AsyncMock(side_effect=slow_arm)
    ialarm_api.return_value.cancel_alarm = AsyncMock(side_effect=fast_cancel)

    # Launch both concurrently
    await asyncio.gather(
        coordinator.async_arm_away(),
        coordinator.async_cancel_alarm(),
    )

    # slow_arm must complete before fast_cancel starts
    assert execution_order == [
        "slow_arm_start",
        "slow_arm_end",
        "fast_cancel_start",
        "fast_cancel_end",
    ]


async def test_coordinator_async_set_alarm_status(
    hass: HomeAssistant,
    mock_config_entry,
    ialarm_api,
) -> None:
    """Test forcing alarm status update optimistically without polling."""
    ialarm_api.return_value.get_mac = AsyncMock(return_value="00:11:22:33:44:55")
    mock_config_entry.add_to_hass(hass)
    await hass.config_entries.async_setup(mock_config_entry.entry_id)
    await hass.async_block_till_done()

    coordinator = mock_config_entry.runtime_data
    coordinator.async_set_alarm_status(AlarmControlPanelState.ARMED_AWAY)
    assert coordinator.data["ialarm_status"] == AlarmControlPanelState.ARMED_AWAY

    coordinator.async_set_alarm_status(AlarmControlPanelState.DISARMED)
    assert coordinator.data["ialarm_status"] == AlarmControlPanelState.DISARMED


ALARMED_ZONE = {
    "zone_id": 1,
    "name": "Main Door",
    "types": [StatusType.ZONE_IN_USE, StatusType.ZONE_ALARM],
}
CLEAN_ZONE = {"zone_id": 1, "name": "Main Door", "types": [StatusType.ZONE_IN_USE]}


@pytest.mark.parametrize("arm_method", ["arm_stay", "arm_away"])
async def test_arm_clears_alarm_memory_first(
    hass: HomeAssistant,
    mock_config_entry,
    ialarm_api,
    arm_method: str,
) -> None:
    """Test arming clears the zone alarm memory left by a key fob disarm."""
    mock_config_entry.add_to_hass(hass)
    await hass.config_entries.async_setup(mock_config_entry.entry_id)
    await hass.async_block_till_done()

    coordinator = mock_config_entry.runtime_data
    device = ialarm_api.return_value
    calls: list[str] = []
    device.get_zone_status = AsyncMock(side_effect=[[ALARMED_ZONE], [CLEAN_ZONE]])
    device.cancel_alarm = AsyncMock(side_effect=lambda: calls.append("clear"))
    setattr(device, arm_method, AsyncMock(side_effect=lambda: calls.append("arm")))

    with patch(
        "custom_components.ialarm_controller.coordinator.CLEAR_MEMORY_RETRY_DELAY", 0
    ):
        await getattr(coordinator, f"async_{arm_method}")()

    assert calls == ["clear", "arm"]


async def test_arm_without_alarm_memory_does_not_clear(
    hass: HomeAssistant,
    mock_config_entry,
    ialarm_api,
) -> None:
    """Test arming sends no clear command when no zone has alarm memory."""
    mock_config_entry.add_to_hass(hass)
    await hass.config_entries.async_setup(mock_config_entry.entry_id)
    await hass.async_block_till_done()

    coordinator = mock_config_entry.runtime_data
    device = ialarm_api.return_value
    device.get_zone_status = AsyncMock(return_value=[CLEAN_ZONE])
    device.cancel_alarm = AsyncMock()
    device.arm_away = AsyncMock()

    await coordinator.async_arm_away()

    device.cancel_alarm.assert_not_awaited()
    device.arm_away.assert_awaited_once()


async def test_arm_when_alarm_memory_cannot_be_cleared(
    hass: HomeAssistant,
    mock_config_entry,
    ialarm_api,
    caplog: pytest.LogCaptureFixture,
) -> None:
    """Test arming still proceeds, with a warning, if the memory stays set."""
    mock_config_entry.add_to_hass(hass)
    await hass.config_entries.async_setup(mock_config_entry.entry_id)
    await hass.async_block_till_done()

    coordinator = mock_config_entry.runtime_data
    device = ialarm_api.return_value
    device.get_zone_status = AsyncMock(return_value=[ALARMED_ZONE])
    device.cancel_alarm = AsyncMock()
    device.arm_stay = AsyncMock()

    with patch(
        "custom_components.ialarm_controller.coordinator.CLEAR_MEMORY_RETRY_DELAY", 0
    ):
        await coordinator.async_arm_stay()

    assert device.cancel_alarm.await_count == 3
    device.arm_stay.assert_awaited_once()
    assert "still set after 3 clear attempts" in caplog.text
