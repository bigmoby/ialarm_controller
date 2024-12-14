"""Test the Antifurto365 iAlarm config flow."""

from unittest.mock import patch

from custom_components.ialarm_controller.const import DOMAIN
from homeassistant import config_entries
from homeassistant.core import HomeAssistant
from homeassistant.data_entry_flow import FlowResultType

from .const import TEST_DATA, TEST_MAC


async def test_successful_config_flow(hass: HomeAssistant):
    """Test a successful config flow."""
    # Initialize a config flow
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )

    # Check that the config flow shows the user form as the first step
    assert result["type"] == FlowResultType.FORM
    assert result["errors"] is None
    assert result["step_id"] == "user"

    with (
        patch(
            "custom_components.ialarm_controller.config_flow._get_device_mac",
            return_value=TEST_MAC,
        ),
        patch(
            "custom_components.ialarm_controller.async_setup_entry",
            return_value=True,
        ) as mock_setup_entry,
    ):
        result2 = await hass.config_entries.flow.async_configure(
            result["flow_id"], user_input=TEST_DATA
        )
        await hass.async_block_till_done()

        assert len(mock_setup_entry.mock_calls) == 1
        assert result2["type"] == FlowResultType.CREATE_ENTRY
        assert result2["title"] == TEST_DATA["host"]
        assert result2["data"] == TEST_DATA


async def test_form_cannot_connect(hass: HomeAssistant) -> None:
    """Test we handle cannot connect error."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )

    with patch(
        "custom_components.ialarm_controller.config_flow._get_device_mac",
        side_effect=ConnectionError,
    ):
        result2 = await hass.config_entries.flow.async_configure(
            result["flow_id"], TEST_DATA
        )

    assert result2["type"] is FlowResultType.FORM
    assert result2["errors"] == {"base": "cannot_connect"}


async def test_form_exception(hass: HomeAssistant) -> None:
    """Test we handle unknown exception."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )

    with patch(
        "custom_components.ialarm_controller.config_flow._get_device_mac",
        side_effect=Exception,
    ):
        result2 = await hass.config_entries.flow.async_configure(
            result["flow_id"], TEST_DATA
        )

    assert result2["type"] is FlowResultType.FORM
    assert result2["errors"] == {"base": "unknown"}
