"""Services for the iAlarm integration."""

from __future__ import annotations

from homeassistant.components.alarm_control_panel.const import (
    DOMAIN as ALARM_CONTROL_PANEL_DOMAIN,
)
from homeassistant.core import HomeAssistant, SupportsResponse, callback
from homeassistant.helpers import service
import probatio as vol

from .const import DOMAIN, SERVICE_GET_LOG


@callback
def async_setup_services(hass: HomeAssistant) -> None:
    """Register the iAlarm entity services."""
    service.async_register_platform_entity_service(
        hass,
        DOMAIN,
        SERVICE_GET_LOG,
        entity_domain=ALARM_CONTROL_PANEL_DOMAIN,
        schema={
            vol.Required("max_entries"): vol.All(
                vol.Coerce(int), vol.Range(min=1, max=100)
            ),
        },
        func="async_get_log",
        supports_response=SupportsResponse.OPTIONAL,
    )
