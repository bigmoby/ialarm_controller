"""Constants for the iAlarm integration."""

from typing import TypedDict

from homeassistant.const import (
    STATE_ALARM_ARMED_AWAY,
    STATE_ALARM_ARMED_HOME,
    STATE_ALARM_DISARMED,
    STATE_ALARM_TRIGGERED,
)
from pyasyncialarm.const import ZoneStatusType
from pyasyncialarm.pyasyncialarm import IAlarm

DATA_COORDINATOR = "ialarm_controller"

DEFAULT_PORT = 18034

DOMAIN = "ialarm_controller"

IALARM_TO_HASS = {
    IAlarm.ARMED_AWAY: STATE_ALARM_ARMED_AWAY,
    IAlarm.ARMED_STAY: STATE_ALARM_ARMED_HOME,
    IAlarm.DISARMED: STATE_ALARM_DISARMED,
    IAlarm.TRIGGERED: STATE_ALARM_TRIGGERED,
}


class IAlarmStatusType(TypedDict):
    """Represents the status of the iAlarm.

    - ialarm_status: The current status of the alarm, can be a string or None.
    - zone_status_list: List of zone statuses, each element is of type ZoneStatusType.
    """

    ialarm_status: str | None
    zone_status_list: list[ZoneStatusType]
