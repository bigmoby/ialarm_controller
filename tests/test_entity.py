"""Test the iAlarm device registration."""

from unittest.mock import AsyncMock

from custom_components.ialarm_controller.const import DOMAIN
from homeassistant.core import HomeAssistant
from homeassistant.helpers import device_registry as dr, entity_registry as er

MAC = "00:11:22:33:44:55"


async def test_device_has_network_mac_connection(
    hass: HomeAssistant,
    mock_config_entry,
    ialarm_api,
    device_registry: dr.DeviceRegistry,
    entity_registry: er.EntityRegistry,
) -> None:
    """Test the device is registered with its MAC as identifier and connection."""
    ialarm_api.return_value.get_mac = AsyncMock(return_value=MAC)
    mock_config_entry.add_to_hass(hass)
    assert await hass.config_entries.async_setup(mock_config_entry.entry_id)
    await hass.async_block_till_done()

    device = device_registry.async_get_device_by_connection(
        (dr.CONNECTION_NETWORK_MAC, MAC), mock_config_entry.entry_id
    )
    assert device is not None
    assert device == device_registry.async_get_device_by_identifier(
        (DOMAIN, MAC), mock_config_entry.entry_id
    )
    assert device.identifiers == {(DOMAIN, MAC)}
    assert device.connections == {(dr.CONNECTION_NETWORK_MAC, MAC)}
    assert device.manufacturer == "Antifurto365 - Meian"

    # Every entity of the entry is attached to that single device
    devices = dr.async_entries_for_config_entry(
        device_registry, mock_config_entry.entry_id
    )
    assert [d.id for d in devices] == [device.id]

    entities = er.async_entries_for_config_entry(
        entity_registry, mock_config_entry.entry_id
    )
    assert entities
    assert {entity.device_id for entity in entities} == {device.id}
