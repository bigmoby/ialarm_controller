"""Test the iAlarm sensor."""

from unittest.mock import AsyncMock

from custom_components.ialarm_controller.sensor import IAlarmSensorEntity
from homeassistant.core import HomeAssistant
from pyasyncialarm.const import StatusType


async def test_sensor_triggered_and_anomaly(
    hass: HomeAssistant,
    mock_config_entry,
    ialarm_api,
) -> None:
    """Test the sensor attributes and states."""
    ialarm_api.return_value.get_mac = AsyncMock(return_value="00:11:22:33:44:55")
    ialarm_api.return_value.get_zone_status = AsyncMock(
        return_value=[
            {"zone_id": 1, "name": "Zone 1", "types": [StatusType.ZONE_ALARM]},
            {"zone_id": 2, "name": "Zone 2", "types": [StatusType.ZONE_BYPASS]},
        ]
    )
    ialarm_api.return_value.get_status = AsyncMock(
        return_value={"status_value": 0, "alarmed_zones": []}
    )

    mock_config_entry.add_to_hass(hass)
    assert await hass.config_entries.async_setup(mock_config_entry.entry_id)
    await hass.async_block_till_done()

    entity_id = "sensor.mock_ialarm_config_entry_zone_status"
    state = hass.states.get(entity_id)

    assert state is not None
    assert state.state == "triggered; anomaly detected"
    assert "Zone 1 (Zone 1)" in state.attributes
    assert state.attributes["Zone 1 (Zone 1)"] == "ZONE_ALARM"


async def test_sensor_running(
    hass: HomeAssistant,
    mock_config_entry,
    ialarm_api,
) -> None:
    """Test the sensor when normal."""
    ialarm_api.return_value.get_mac = AsyncMock(return_value="00:11:22:33:44:55")
    ialarm_api.return_value.get_zone_status = AsyncMock(
        return_value=[
            {"zone_id": 1, "name": "Zone 1", "types": [StatusType.ZONE_IN_USE]},
        ]
    )
    ialarm_api.return_value.get_status = AsyncMock(
        return_value={"status_value": 0, "alarmed_zones": []}
    )

    mock_config_entry.add_to_hass(hass)
    assert await hass.config_entries.async_setup(mock_config_entry.entry_id)
    await hass.async_block_till_done()

    entity_id = "sensor.mock_ialarm_config_entry_zone_status"
    state = hass.states.get(entity_id)

    assert state is not None
    assert state.state == "running"


async def test_sensor_empty_or_broken_zones(
    hass: HomeAssistant,
    mock_config_entry,
    ialarm_api,
) -> None:
    """Test the sensor handles weird zone formats without crashing."""
    ialarm_api.return_value.get_mac = AsyncMock(return_value="00:11:22:33:44:55")
    ialarm_api.return_value.get_zone_status = AsyncMock(
        return_value=[
            {"zone_id": None, "name": "Broken Zone"},
            {"zone_id": 3, "name": None},
        ]
    )
    ialarm_api.return_value.get_status = AsyncMock(
        return_value={"status_value": 0, "alarmed_zones": []}
    )

    mock_config_entry.add_to_hass(hass)
    assert await hass.config_entries.async_setup(mock_config_entry.entry_id)
    await hass.async_block_till_done()

    entity_id = "sensor.mock_ialarm_config_entry_zone_status"
    state = hass.states.get(entity_id)

    assert state is not None
    assert state.state == "running"
    # Should not have created attrs for the broken zones
    assert "Integration" in state.attributes


async def test_sensor_only_alarm(
    hass: HomeAssistant,
    mock_config_entry,
    ialarm_api,
) -> None:
    """Test the sensor with only alarm."""
    ialarm_api.return_value.get_mac = AsyncMock(return_value="00:11:22:33:44:55")
    ialarm_api.return_value.get_zone_status = AsyncMock(
        return_value=[
            {"zone_id": 1, "name": "Zone 1", "types": [StatusType.ZONE_ALARM]},
        ]
    )
    mock_config_entry.add_to_hass(hass)
    assert await hass.config_entries.async_setup(mock_config_entry.entry_id)
    await hass.async_block_till_done()

    state = hass.states.get("sensor.mock_ialarm_config_entry_zone_status")
    assert state.state == "triggered"


async def test_sensor_only_anomaly(
    hass: HomeAssistant,
    mock_config_entry,
    ialarm_api,
) -> None:
    """Test the sensor with only anomaly."""
    ialarm_api.return_value.get_mac = AsyncMock(return_value="00:11:22:33:44:55")
    ialarm_api.return_value.get_zone_status = AsyncMock(
        return_value=[
            {"zone_id": 1, "name": "Zone 1", "types": [StatusType.ZONE_BYPASS]},
        ]
    )
    mock_config_entry.add_to_hass(hass)
    assert await hass.config_entries.async_setup(mock_config_entry.entry_id)
    await hass.async_block_till_done()

    state = hass.states.get("sensor.mock_ialarm_config_entry_zone_status")
    assert state.state == "anomaly detected"


async def test_sensor_no_coordinator_data(
    hass: HomeAssistant,
    mock_config_entry,
    ialarm_api,
) -> None:
    """Test the sensor when coordinator has no data."""
    ialarm_api.return_value.get_mac = AsyncMock(return_value="00:11:22:33:44:55")
    mock_config_entry.add_to_hass(hass)
    assert await hass.config_entries.async_setup(mock_config_entry.entry_id)
    await hass.async_block_till_done()

    coordinator = mock_config_entry.runtime_data
    coordinator.data = None

    sensor = IAlarmSensorEntity(
        coordinator, mock_config_entry.unique_id, mock_config_entry.title
    )
    attrs = sensor._get_sensor_data_attributes()
    assert attrs == {"Integration": "ialarm_controller"}


async def test_sensor_coordinator_update(
    hass: HomeAssistant,
    mock_config_entry,
    ialarm_api,
) -> None:
    """Test the sensor update handler."""
    ialarm_api.return_value.get_mac = AsyncMock(return_value="00:11:22:33:44:55")
    mock_config_entry.add_to_hass(hass)
    assert await hass.config_entries.async_setup(mock_config_entry.entry_id)
    await hass.async_block_till_done()

    entity_id = "sensor.mock_ialarm_config_entry_zone_status"
    coordinator = mock_config_entry.runtime_data

    # Update coordinator data and trigger update
    coordinator.data = {
        "ialarm_status": "armed_away",
        "zone_status_list": [
            {"zone_id": 1, "name": "Zone 1", "types": [StatusType.ZONE_ALARM]}
        ],
    }
    coordinator.async_set_updated_data(coordinator.data)
    await hass.async_block_till_done()

    state = hass.states.get(entity_id)
    assert state.state == "triggered"
    assert "Zone 1 (Zone 1)" in state.attributes
