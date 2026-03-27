"""Constants for ialarm_controller tests."""

from custom_components.ialarm_controller.const import (
    CONF_REQUIRE_CODE_TO_ARM,
    CONF_REQUIRE_CODE_TO_DISARM,
)
from homeassistant.const import CONF_EVENT, CONF_HOST, CONF_PORT

TEST_DATA = {
    CONF_HOST: "1.1.1.1",
    CONF_PORT: 18034,
    CONF_EVENT: True,
    CONF_REQUIRE_CODE_TO_ARM: True,
    CONF_REQUIRE_CODE_TO_DISARM: True,
}
TEST_MAC = "00:00:54:12:34:56"
