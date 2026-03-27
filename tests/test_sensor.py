"""Test the iAlarm sensor."""

from unittest.mock import AsyncMock

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
