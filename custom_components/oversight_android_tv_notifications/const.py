"""Constants for the OverSight Android TV integration."""

from logging import Logger, getLogger

LOGGER: Logger = getLogger(__package__)

DOMAIN = "oversight_android_tv_notifications"

CONF_HOST = "host"
CONF_PORT = "port"
CONF_DEVICE_ID = "device_id"
CONF_DEVICE_NAME = "device_name"

DEFAULT_PORT = 5001
DEFAULT_SCAN_INTERVAL = 30
