"""Global fixtures for ialarm_controller integration."""

from homeassistant import loader
from homeassistant.core import HomeAssistant
import pytest

pytest_plugins = "pytest_homeassistant_custom_component"


@pytest.fixture(name="enable_custom_integrations", autouse=True)
def enable_custom_integrations(hass: HomeAssistant) -> None:
    """Enable custom integrations defined in the test dir."""
    hass.data.pop(loader.DATA_CUSTOM_COMPONENTS)
