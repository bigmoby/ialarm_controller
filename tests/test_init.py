"""Test the iAlarm init."""

from unittest.mock import AsyncMock, patch

from custom_components.ialarm_controller import update_listener
from homeassistant.config_entries import ConfigEntryState
from homeassistant.const import EVENT_HOMEASSISTANT_STOP
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


async def test_setup_entry_timeout(
    hass: HomeAssistant,
    mock_config_entry,
    ialarm_api,
) -> None:
    """Test ConfigEntryNotReady when API times out."""
    ialarm_api.return_value.get_mac.side_effect = TimeoutError

    mock_config_entry.add_to_hass(hass)

    await hass.config_entries.async_setup(mock_config_entry.entry_id)
    await hass.async_block_till_done()

    assert mock_config_entry.state is ConfigEntryState.SETUP_RETRY


async def test_on_hass_stop(
    hass: HomeAssistant,
    mock_config_entry,
    ialarm_api,
) -> None:
    """Test the shutdown callback when hass stops."""
    ialarm_api.return_value.get_mac = AsyncMock(return_value="00:11:22:33:44:55")
    mock_config_entry.add_to_hass(hass)

    assert await hass.config_entries.async_setup(mock_config_entry.entry_id)
    await hass.async_block_till_done()

    coordinator = mock_config_entry.runtime_data
    coordinator.async_shutdown = AsyncMock()

    hass.bus.async_fire(EVENT_HOMEASSISTANT_STOP)
    await hass.async_block_till_done()

    coordinator.async_shutdown.assert_awaited_once()


async def test_update_listener(
    hass: HomeAssistant,
    mock_config_entry,
    ialarm_api,
) -> None:
    """Test the update listener reloads the entry."""
    ialarm_api.return_value.get_mac = AsyncMock(return_value="00:11:22:33:44:55")
    mock_config_entry.add_to_hass(hass)

    assert await hass.config_entries.async_setup(mock_config_entry.entry_id)
    await hass.async_block_till_done()

    with patch(
        "homeassistant.config_entries.ConfigEntries.async_reload"
    ) as mock_reload:
        await update_listener(hass, mock_config_entry)
        await hass.async_block_till_done()
        mock_reload.assert_called_once_with(mock_config_entry.entry_id)
