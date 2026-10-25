"""Actions for the OverSight Android TV integration."""

from __future__ import annotations

from typing import TYPE_CHECKING

import voluptuous as vol
from homeassistant.components.notify import DOMAIN as NOTIFY_DOMAIN
from homeassistant.helpers import config_validation as cv
from homeassistant.helpers import service

from .const import DOMAIN

if TYPE_CHECKING:
    from homeassistant.core import HomeAssistant

SERVICE_SEND_NOTIFICATION = "send_notification"
SERVICE_SEND_FIXED_NOTIFICATION = "send_fixed_notification"
SERVICE_REMOVE_FIXED_NOTIFICATION = "remove_fixed_notification"
SERVICE_SCREEN_ON = "screen_on"
SERVICE_SET_CLOCK_APPEARANCE = "set_clock_appearance"

FONT_WEIGHTS = [
    "thin",
    "extralight",
    "light",
    "normal",
    "medium",
    "semibold",
    "bold",
    "extrabold",
    "black",
]

SEND_NOTIFICATION_SCHEMA = {
    vol.Required("message"): cv.string,
    vol.Optional("id"): cv.string,
    vol.Optional("title"): cv.string,
    vol.Optional("source"): cv.string,
    vol.Optional("image"): cv.string,
    vol.Optional("video"): cv.string,
    vol.Optional("small_icon"): cv.string,
    vol.Optional("small_icon_color"): cv.string,
    vol.Optional("large_icon"): cv.string,
    vol.Optional("corner"): cv.string,
    vol.Optional("duration"): vol.Coerce(int),
    vol.Optional("layout"): dict,
}

SEND_FIXED_NOTIFICATION_SCHEMA = {
    vol.Required("id"): cv.string,
    vol.Optional("visible"): cv.boolean,
    vol.Optional("icon"): cv.string,
    vol.Optional("text"): cv.string,
    vol.Optional("icon_color"): cv.string,
    vol.Optional("message_color"): cv.string,
    vol.Optional("background_color"): cv.string,
    vol.Optional("border_color"): cv.string,
    vol.Optional("shape"): cv.string,
    vol.Optional("size"): cv.string,
    vol.Optional("expiration"): cv.string,
    vol.Optional("show_duration"): vol.Coerce(int),
    vol.Optional("collapse_duration"): vol.Coerce(int),
    vol.Optional("repeat_expand"): cv.boolean,
}

REMOVE_FIXED_NOTIFICATION_SCHEMA = {
    vol.Required("id"): cv.string,
}

SET_CLOCK_APPEARANCE_SCHEMA = {
    vol.Optional("font_size"): vol.All(vol.Coerce(int), vol.Range(min=1)),
    vol.Optional("font_weight"): vol.In(FONT_WEIGHTS),
    vol.Optional("color"): cv.string,
    vol.Optional("display_shadow"): cv.boolean,
    vol.Optional("background_color"): cv.string,
}


def async_setup_services(hass: HomeAssistant) -> None:
    """
    Register the integration's actions.

    They are entity services on the notify entities: HA resolves entity, device
    and area targets to those entities and calls each one, so every targeted
    device is reached.
    """
    for name, schema, func in (
        (
            SERVICE_SEND_NOTIFICATION,
            SEND_NOTIFICATION_SCHEMA,
            "async_handle_send_notification",
        ),
        (
            SERVICE_SEND_FIXED_NOTIFICATION,
            SEND_FIXED_NOTIFICATION_SCHEMA,
            "async_handle_send_fixed_notification",
        ),
        (
            SERVICE_REMOVE_FIXED_NOTIFICATION,
            REMOVE_FIXED_NOTIFICATION_SCHEMA,
            "async_handle_remove_fixed_notification",
        ),
        (SERVICE_SCREEN_ON, {}, "async_handle_screen_on"),
        (
            SERVICE_SET_CLOCK_APPEARANCE,
            SET_CLOCK_APPEARANCE_SCHEMA,
            "async_handle_set_clock_appearance",
        ),
    ):
        service.async_register_platform_entity_service(
            hass,
            DOMAIN,
            name,
            entity_domain=NOTIFY_DOMAIN,
            schema=schema,
            func=func,
        )
