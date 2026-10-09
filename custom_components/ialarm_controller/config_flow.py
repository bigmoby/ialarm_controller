"""Config flow for Antifurto365 iAlarm integration."""

from __future__ import annotations

import logging
from typing import Any

from homeassistant.config_entries import (
    ConfigEntry,
    ConfigFlow,
    ConfigFlowResult,
    OptionsFlowWithReload,
)
from homeassistant.const import CONF_EVENT, CONF_HOST, CONF_PORT
from homeassistant.core import callback
import probatio as vol
from pyasyncialarm.pyasyncialarm import IAlarm

from .const import (
    CONF_REQUIRE_CODE_TO_ARM,
    CONF_REQUIRE_CODE_TO_DISARM,
    DEFAULT_HOST,
    DEFAULT_PORT,
    DEFAULT_REQUIRE_CODE_TO_ARM,
    DEFAULT_REQUIRE_CODE_TO_DISARM,
    DEFAULT_SEND_EVENTS,
    DOMAIN,
)

_LOGGER = logging.getLogger(__name__)

DATA_SCHEMA = vol.Schema(
    {
        vol.Required(CONF_HOST, default=DEFAULT_HOST): str,
        vol.Required(CONF_PORT, default=DEFAULT_PORT): int,
        vol.Required(CONF_EVENT, default=DEFAULT_SEND_EVENTS): bool,
        vol.Required(
            CONF_REQUIRE_CODE_TO_ARM, default=DEFAULT_REQUIRE_CODE_TO_ARM
        ): bool,
        vol.Required(
            CONF_REQUIRE_CODE_TO_DISARM, default=DEFAULT_REQUIRE_CODE_TO_DISARM
        ): bool,
    }
)


async def _get_device_mac(host: str, port: int) -> str:
    ialarm = IAlarm(host, port)
    return await ialarm.get_mac()


class IAlarmConfigFlow(ConfigFlow, domain=DOMAIN):  # type: ignore[call-arg,unused-ignore]
    """Handle a config flow for Antifurto365 iAlarm."""

    VERSION = 1

    @staticmethod
    @callback
    def async_get_options_flow(
        config_entry: ConfigEntry,
    ) -> IAlarmOptionsFlow:
        """Create the options flow."""
        return IAlarmOptionsFlow()

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Handle the initial step."""
        errors: dict[str, str] = {}

        if user_input is None:
            return self.async_show_form(step_id="user", data_schema=DATA_SCHEMA)

        host = user_input[CONF_HOST]
        port = user_input[CONF_PORT]

        try:
            # If we are able to get the MAC address, we are able to establish
            # a connection to the device.
            mac = await _get_device_mac(host, port)
        except TimeoutError, ConnectionError:
            errors["base"] = "cannot_connect"
        except Exception:
            _LOGGER.exception("Unexpected exception")
            errors["base"] = "unknown"

        if errors:
            return self.async_show_form(
                step_id="user", data_schema=DATA_SCHEMA, errors=errors
            )

        await self.async_set_unique_id(mac)
        self._abort_if_unique_id_configured()

        return self.async_create_entry(title=user_input[CONF_HOST], data=user_input)


class IAlarmOptionsFlow(OptionsFlowWithReload):
    """Handle options; the entry is reloaded automatically on change."""

    async def async_step_init(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Manage the options."""
        if user_input is not None:
            return self.async_create_entry(title="", data=user_input)

        options = {
            vol.Required(
                CONF_EVENT,
                default=self.config_entry.options.get(
                    CONF_EVENT,
                    self.config_entry.data.get(CONF_EVENT, DEFAULT_SEND_EVENTS),
                ),
            ): bool,
            vol.Required(
                CONF_REQUIRE_CODE_TO_ARM,
                default=self.config_entry.options.get(
                    CONF_REQUIRE_CODE_TO_ARM,
                    self.config_entry.data.get(
                        CONF_REQUIRE_CODE_TO_ARM, DEFAULT_REQUIRE_CODE_TO_ARM
                    ),
                ),
            ): bool,
            vol.Required(
                CONF_REQUIRE_CODE_TO_DISARM,
                default=self.config_entry.options.get(
                    CONF_REQUIRE_CODE_TO_DISARM,
                    self.config_entry.data.get(
                        CONF_REQUIRE_CODE_TO_DISARM, DEFAULT_REQUIRE_CODE_TO_DISARM
                    ),
                ),
            ): bool,
        }

        return self.async_show_form(
            step_id="init",
            data_schema=vol.Schema(options),
        )
