"""Constants for the iAlarm integration."""

from typing import TypedDict

from homeassistant.components.alarm_control_panel.const import AlarmControlPanelState
from pyasyncialarm.const import ZoneStatusType
from pyasyncialarm.pyasyncialarm import IAlarm

DATA_COORDINATOR = "ialarm_controller"

DEFAULT_PORT = 18034
DEFAULT_HOST = "192.168.1.81"
DEFAULT_SEND_EVENTS = True

# Max time to wait for the panel MAC address when setting up or configuring
CONNECT_TIMEOUT = 10

CONF_REQUIRE_CODE_TO_ARM = "require_code_to_arm"
CONF_REQUIRE_CODE_TO_DISARM = "require_code_to_disarm"
DEFAULT_REQUIRE_CODE_TO_ARM = True
DEFAULT_REQUIRE_CODE_TO_DISARM = True

DOMAIN = "ialarm_controller"

NOTIFICATION_ID = "ialarm_notification"
NOTIFICATION_TITLE = "iAlarm notification"

IALARM_TO_HASS = {
    IAlarm.ARMED_AWAY: AlarmControlPanelState.ARMED_AWAY,
    IAlarm.ARMED_STAY: AlarmControlPanelState.ARMED_HOME,
    IAlarm.DISARMED: AlarmControlPanelState.DISARMED,
    IAlarm.CANCEL: AlarmControlPanelState.DISARMED,
    IAlarm.TRIGGERED: AlarmControlPanelState.TRIGGERED,
}


SERVICE_GET_LOG = "get_log"
SERVICE_GET_LOG_MAX_ENTRIES = 25

# Clearing the zone alarm memory before arming
CLEAR_MEMORY_MAX_ATTEMPTS = 3
CLEAR_MEMORY_RETRY_DELAY = 1.0


class IAlarmStatusType(TypedDict):
    """Represents the status of the iAlarm.

    - ialarm_status: The current status of the alarm, can be a string or None.
    - zone_status_list: List of zone statuses, each element is of type ZoneStatusType.
    """

    ialarm_status: AlarmControlPanelState | None
    zone_status_list: list[ZoneStatusType]
