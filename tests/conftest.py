"""Global fixtures for ialarm_controller integration."""

from unittest.mock import AsyncMock, patch
from uuid import uuid4

from custom_components.ialarm_controller.const import DOMAIN
from homeassistant import loader
from homeassistant.core import HomeAssistant
import pytest
from pytest_homeassistant_custom_component.common import MockConfigEntry

from tests.const import TEST_DATA

pytest_plugins = "pytest_homeassistant_custom_component"


@pytest.fixture(name="enable_custom_integrations", autouse=True)
def enable_custom_integrations(hass: HomeAssistant) -> None:  # noqa: PT004
    """Enable custom integrations defined in the test dir."""
    hass.data.pop(loader.DATA_CUSTOM_COMPONENTS)


@pytest.fixture(name="ialarm_api")
def ialarm_api_fixture():
    """Set up IAlarm API fixture."""
    with patch("custom_components.ialarm_controller.IAlarm") as mock_ialarm_api:
        mock_instance = mock_ialarm_api.return_value
        mock_instance.get_mac = AsyncMock(return_value="00:11:22:33:44:55")
        mock_instance.get_zone_status = AsyncMock(return_value=[])
        mock_instance.get_status = AsyncMock(
            return_value={"status_value": 0, "alarmed_zones": []}
        )
        mock_instance.get_last_log_entries = AsyncMock(return_value=[])
        mock_instance.arm_away = AsyncMock()
        mock_instance.arm_stay = AsyncMock()
        mock_instance.disarm = AsyncMock()
        mock_instance.cancel_alarm = AsyncMock()
        mock_instance.disarm_and_cancel = AsyncMock(return_value=True)
        mock_instance.shutdown = AsyncMock()
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
        title="Mock iAlarm config entry",
        domain=DOMAIN,
        data=TEST_DATA,
        unique_id=str(uuid4()),
        entry_id=str(uuid4()),
    )
