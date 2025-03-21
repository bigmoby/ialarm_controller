"""Constants for the iAlarm integration."""

from typing import TypedDict

from homeassistant.components.alarm_control_panel import AlarmControlPanelState
from pyasyncialarm.const import ZoneStatusType
from pyasyncialarm.pyasyncialarm import IAlarm
import voluptuous as vol

DATA_COORDINATOR = "ialarm_controller"

DEFAULT_PORT = 18034
DEFAULT_HOST = "192.168.1.81"
DEFAULT_SEND_EVENTS = True

DOMAIN = "ialarm_controller"

NOTIFICATION_ID = "ialarm_notification"
NOTIFICATION_TITLE = "iAlarm notification"

IALARM_TO_HASS = {
    IAlarm.ARMED_AWAY: AlarmControlPanelState.ARMED_AWAY,
    IAlarm.ARMED_STAY: AlarmControlPanelState.ARMED_HOME,
    IAlarm.DISARMED: AlarmControlPanelState.DISARMED,
    IAlarm.TRIGGERED: AlarmControlPanelState.TRIGGERED,
}

SERVICE_GET_LOG = "get_log"
SERVICE_GET_LOG_MAX_ENTRIES = 25

GET_LOG_ACTION_SCHEMA = {vol.Required("max_entries"): vol.Coerce(int)}

ENTITY_SERVICES = {
    SERVICE_GET_LOG: GET_LOG_ACTION_SCHEMA,
}


class IAlarmStatusType(TypedDict):
    """Represents the status of the iAlarm.

    - ialarm_status: The current status of the alarm, can be a string or None.
    - zone_status_list: List of zone statuses, each element is of type ZoneStatusType.
    """

    ialarm_status: str | None
    zone_status_list: list[ZoneStatusType]
