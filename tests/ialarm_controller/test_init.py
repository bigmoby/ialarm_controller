"""Test the Antifurto365 iAlarm init."""

from unittest.mock import Mock, patch
from uuid import uuid4

from custom_components.ialarm_controller import update_listener
from custom_components.ialarm_controller.const import DOMAIN
import pytest

from homeassistant.config_entries import ConfigEntryState
from homeassistant.const import CONF_EVENT, CONF_HOST, CONF_PORT
from homeassistant.core import HomeAssistant

from tests.common import MockConfigEntry

TEST_MAC = "00:00:54:12:34:56"


@pytest.fixture(name="ialarm_api")
def ialarm_api_fixture():
    """Set up IAlarm API fixture."""
    with patch("pyasyncialarm.pyasyncialarm.IAlarm") as mock_ialarm_api:
        yield mock_ialarm_api


@pytest.fixture(name="ialarm_coordinator")
def ialarm_coordinator_fixture():
    """Set up IAlarmCoordinator fixture."""
    with patch(
        "custom_components.ialarm_controller.IAlarmCoordinator"
    ) as mock_coordinator:
        yield mock_coordinator


@pytest.fixture(name="mock_config_entry")
def mock_config_fixture():
    """Return a fake config entry."""
    return MockConfigEntry(
        domain=DOMAIN,
        data={CONF_HOST: "192.168.10.20", CONF_PORT: 18034, CONF_EVENT: True},
        entry_id=str(uuid4()),
    )


async def test_setup_entry(
    hass: HomeAssistant, ialarm_api, ialarm_coordinator, mock_config_entry
) -> None:
    """Test setup entry."""
    ialarm_api.return_value.get_mac = Mock(return_value=TEST_MAC)
    ialarm_coordinator.return_value.async_config_entry_first_refresh = Mock(
        return_value=True
    )

    mock_config_entry.add_to_hass(hass)

    with patch(
        "homeassistant.config_entries.async_forward_entry_setups"
    ) as mock_forward:
        assert await hass.config_entries.async_setup(mock_config_entry.entry_id)
        await hass.async_block_till_done()

        ialarm_api.return_value.get_mac.assert_called_once()
        ialarm_coordinator.return_value.async_config_entry_first_refresh.assert_called_once()  # noqa: E501
        mock_forward.assert_called_once_with(
            mock_config_entry, ["alarm_control_panel", "sensor", "button"]
        )

    assert mock_config_entry.state is ConfigEntryState.LOADED


async def test_setup_not_ready(
    hass: HomeAssistant, ialarm_api, ialarm_coordinator, mock_config_entry
) -> None:
    """Test setup fails due to connection issues."""
    ialarm_api.return_value.get_mac = Mock(side_effect=ConnectionError)
    mock_config_entry.add_to_hass(hass)

    assert not await hass.config_entries.async_setup(mock_config_entry.entry_id)
    await hass.async_block_till_done()

    assert mock_config_entry.state is ConfigEntryState.SETUP_RETRY


async def test_unload_entry(
    hass: HomeAssistant, ialarm_api, ialarm_coordinator, mock_config_entry
) -> None:
    """Test unloading of entry."""
    ialarm_api.return_value.get_mac = Mock(return_value=TEST_MAC)
    ialarm_coordinator.return_value.async_shutdown = Mock()

    mock_config_entry.add_to_hass(hass)
    assert await hass.config_entries.async_setup(mock_config_entry.entry_id)
    await hass.async_block_till_done()

    assert mock_config_entry.state is ConfigEntryState.LOADED
    assert await hass.config_entries.async_unload(mock_config_entry.entry_id)
    await hass.async_block_till_done()

    ialarm_coordinator.return_value.async_shutdown.assert_called_once()
    assert mock_config_entry.state is ConfigEntryState.NOT_LOADED


async def test_update_listener(hass: HomeAssistant, mock_config_entry) -> None:
    """Test the update listener."""
    with patch("homeassistant.config_entries.async_reload") as mock_reload:
        await update_listener(hass, mock_config_entry)
        mock_reload.assert_called_once_with(mock_config_entry.entry_id)
