"""Constants for ialarm_controller tests."""

from homeassistant.const import CONF_EVENT, CONF_HOST, CONF_PORT

TEST_DATA = {CONF_HOST: "1.1.1.1", CONF_PORT: 18034}
TEST_DATA_RESULT = {CONF_HOST: "1.1.1.1", CONF_PORT: 18034, CONF_EVENT: True}
TEST_MAC = "00:00:54:12:34:56"
