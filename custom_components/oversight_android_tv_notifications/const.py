"""Constants for the OverSight Android TV integration."""

from logging import Logger, getLogger

LOGGER: Logger = getLogger(__package__)

DOMAIN = "oversight_android_tv_notifications"

DEFAULT_PORT = 5001
DEFAULT_SCAN_INTERVAL = 30
DEFAULT_DEVICE_NAME = "OverSight Device"
