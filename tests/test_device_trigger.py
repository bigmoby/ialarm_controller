"""Test iAlarm device triggers."""

from custom_components.ialarm_controller.const import DOMAIN
from homeassistant.components.device_automation import DeviceAutomationType
from homeassistant.const import CONF_DEVICE_ID, CONF_DOMAIN, CONF_PLATFORM, CONF_TYPE
from homeassistant.core import HomeAssistant
from homeassistant.helpers import device_registry as dr
from homeassistant.setup import async_setup_component
from pytest_homeassistant_custom_component.common import (
    async_get_device_automations,
    async_mock_service,
)


async def test_get_triggers(
    hass: HomeAssistant,
    mock_config_entry,
    ialarm_api,
) -> None:
    """Test we get the expected triggers from a iAlarm device."""
    mock_config_entry.add_to_hass(hass)
    assert await hass.config_entries.async_setup(mock_config_entry.entry_id)
    await hass.async_block_till_done()

    device_registry = dr.async_get(hass)
    device = dr.async_entries_for_config_entry(
        device_registry, mock_config_entry.entry_id
    )[0]

    triggers = await async_get_device_automations(
        hass, DeviceAutomationType.TRIGGER, device.id
    )

    expected_types = {
        "disarmed",
        "armed_home",
        "armed_away",
        "triggered",
    }

    trigger_types = {
        trigger["type"] for trigger in triggers if trigger["domain"] == DOMAIN
    }
    assert expected_types == trigger_types


async def test_if_fires_on_event(
    hass: HomeAssistant,
    mock_config_entry,
    ialarm_api,
) -> None:
    """Test for iAlarm device triggers firing on events."""
    mock_config_entry.add_to_hass(hass)
    assert await hass.config_entries.async_setup(mock_config_entry.entry_id)
    await hass.async_block_till_done()

    device_registry = dr.async_get(hass)
    device = dr.async_entries_for_config_entry(
        device_registry, mock_config_entry.entry_id
    )[0]

    service_calls = async_mock_service(hass, "test", "automation")

    # Test all trigger types
    event_map = {
        "disarmed": "ialarm_disarm",
        "armed_home": "ialarm_arm_stay",
        "armed_away": "ialarm_arm_away",
        "triggered": "ialarm_triggered",
    }

    # Setup one automation for each trigger type
    automations = [
        {
            "trigger": {
                CONF_PLATFORM: "device",
                CONF_DOMAIN: DOMAIN,
                CONF_DEVICE_ID: device.id,
                CONF_TYPE: trigger_type,
            },
            "action": {
                "service": "test.automation",
                "data": {"message": f"fired {trigger_type}"},
            },
        }
        for trigger_type in event_map
    ]

    assert await async_setup_component(
        hass,
        "automation",
        {"automation": automations},
    )
    await hass.async_block_till_done()

    for trigger_type, event_type in event_map.items():
        # Fire the event
        hass.bus.async_fire(event_type, {"device_id": device.id})
        await hass.async_block_till_done()

        # Check if fired (it might be in any position in service_calls if they fire concurrently,
        # but here they are sequential)
        assert any(
            call.data["message"] == f"fired {trigger_type}" for call in service_calls
        )
