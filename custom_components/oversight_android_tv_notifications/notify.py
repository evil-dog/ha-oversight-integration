"""Notify platform for OverSight Android TV."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

import voluptuous as vol
from homeassistant.components.notify import NotifyEntity, NotifyEntityFeature
from homeassistant.helpers import config_validation as cv
from homeassistant.helpers import entity_platform
from homeassistant.helpers.entity import EntityDescription

from .entity import OversightEntity

if TYPE_CHECKING:
    from homeassistant.core import HomeAssistant
    from homeassistant.helpers.entity_platform import AddConfigEntryEntitiesCallback

    from .data import OversightConfigEntry

SERVICE_SEND_NOTIFICATION = "send_notification"
SERVICE_SEND_FIXED_NOTIFICATION = "send_fixed_notification"
SERVICE_REMOVE_FIXED_NOTIFICATION = "remove_fixed_notification"
SERVICE_SCREEN_ON = "screen_on"

SEND_NOTIFICATION_SCHEMA = {
    vol.Required("message"): cv.string,
    vol.Optional("title"): cv.string,
    vol.Optional("source"): cv.string,
    vol.Optional("image"): cv.string,
    vol.Optional("video"): cv.string,
    vol.Optional("small_icon"): cv.string,
    vol.Optional("small_icon_color"): cv.string,
    vol.Optional("large_icon"): cv.string,
    vol.Optional("corner"): cv.string,
    vol.Optional("duration"): vol.Coerce(int),
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


async def async_setup_entry(
    hass: HomeAssistant,  # noqa: ARG001
    entry: OversightConfigEntry,
    async_add_entities: AddConfigEntryEntitiesCallback,
) -> None:
    """Set up OverSight notify entity and the device actions."""
    async_add_entities(
        [
            OversightNotifyEntity(
                coordinator=entry.runtime_data.coordinator,
                entity_description=EntityDescription(
                    key="notify",
                    translation_key="notify",
                ),
            )
        ]
    )

    # Entity services: HA resolves entity, device and area targets to these
    # notify entities and calls each one, so every targeted device is reached.
    platform = entity_platform.async_get_current_platform()
    platform.async_register_entity_service(
        SERVICE_SEND_NOTIFICATION,
        SEND_NOTIFICATION_SCHEMA,
        "async_handle_send_notification",
    )
    platform.async_register_entity_service(
        SERVICE_SEND_FIXED_NOTIFICATION,
        SEND_FIXED_NOTIFICATION_SCHEMA,
        "async_handle_send_fixed_notification",
    )
    platform.async_register_entity_service(
        SERVICE_REMOVE_FIXED_NOTIFICATION,
        REMOVE_FIXED_NOTIFICATION_SCHEMA,
        "async_handle_remove_fixed_notification",
    )
    platform.async_register_entity_service(
        SERVICE_SCREEN_ON,
        {},
        "async_handle_screen_on",
    )


class OversightNotifyEntity(OversightEntity, NotifyEntity):
    """Notify entity for sending popup notifications to an OverSight device."""

    _attr_supported_features = NotifyEntityFeature.TITLE

    async def async_send_message(self, message: str, title: str | None = None) -> None:
        """Send a popup notification to the device."""
        data: dict[str, Any] = {"message": message}
        if title:
            data["title"] = title
        await self._async_api_call(
            self.coordinator.client.async_send_notification(data)
        )

    async def async_handle_send_notification(self, **kwargs: Any) -> None:
        """Handle the send_notification action."""
        await self._async_api_call(
            self.coordinator.client.async_send_notification(_to_api_payload(kwargs))
        )

    async def async_handle_send_fixed_notification(self, **kwargs: Any) -> None:
        """Handle the send_fixed_notification action."""
        await self._async_api_call(
            self.coordinator.client.async_send_fixed_notification(
                _to_api_payload(kwargs)
            )
        )

    async def async_handle_remove_fixed_notification(self, **kwargs: Any) -> None:
        """Handle the remove_fixed_notification action."""
        await self._async_api_call(
            self.coordinator.client.async_send_fixed_notification(
                {"id": kwargs["id"], "visible": False}
            )
        )

    async def async_handle_screen_on(self) -> None:
        """Handle the screen_on action."""
        await self._async_api_call(self.coordinator.client.async_screen_on())


def _to_api_payload(data: dict[str, Any]) -> dict[str, Any]:
    """Convert action data with snake_case keys to the camelCase API payload."""
    return {_to_camel_case(key): value for key, value in data.items()}


def _to_camel_case(snake_str: str) -> str:
    """Convert snake_case to camelCase."""
    parts = snake_str.split("_")
    return parts[0] + "".join(word.capitalize() for word in parts[1:])
