"""Test the iAlarm init."""

from unittest.mock import AsyncMock

from homeassistant.config_entries import ConfigEntryState
from homeassistant.core import HomeAssistant


async def test_setup_unload_entry(
    hass: HomeAssistant,
    mock_config_entry,
    ialarm_api,
) -> None:
    """Test entry setup and unload."""
    ialarm_api.return_value.get_mac = AsyncMock(return_value="00:11:22:33:44:55")
    mock_config_entry.add_to_hass(hass)

    assert await hass.config_entries.async_setup(mock_config_entry.entry_id)
    await hass.async_block_till_done()

    assert mock_config_entry.state is ConfigEntryState.LOADED

    assert await hass.config_entries.async_unload(mock_config_entry.entry_id)
    await hass.async_block_till_done()

    assert mock_config_entry.state is ConfigEntryState.NOT_LOADED


async def test_setup_entry_exception(
    hass: HomeAssistant,
    mock_config_entry,
    ialarm_api,
) -> None:
    """Test ConfigEntryNotReady when API raises an exception."""
    ialarm_api.return_value.get_mac.side_effect = ConnectionError

    mock_config_entry.add_to_hass(hass)

    await hass.config_entries.async_setup(mock_config_entry.entry_id)
    await hass.async_block_till_done()

    assert mock_config_entry.state is ConfigEntryState.SETUP_RETRY
