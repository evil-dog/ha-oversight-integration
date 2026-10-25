"""Notify platform for OverSight Android TV."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from homeassistant.components.notify import NotifyEntity, NotifyEntityFeature
from homeassistant.exceptions import HomeAssistantError
from homeassistant.helpers.entity import EntityDescription

from .api import OversightApiClientError, OversightApiClientNotFoundError
from .entity import OversightEntity

if TYPE_CHECKING:
    from homeassistant.core import HomeAssistant
    from homeassistant.helpers.entity_platform import AddConfigEntryEntitiesCallback

    from .data import OversightConfigEntry

PARALLEL_UPDATES = 1


async def async_setup_entry(
    hass: HomeAssistant,  # noqa: ARG001
    entry: OversightConfigEntry,
    async_add_entities: AddConfigEntryEntitiesCallback,
) -> None:
    """Set up OverSight notify entity."""
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


class OversightNotifyEntity(OversightEntity, NotifyEntity):
    """
    Notify entity for sending popup notifications to an OverSight device.

    It is also the target of the integration's actions (see services.py).
    """

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
        client = self.coordinator.client
        if self.coordinator.data is not None and self.coordinator.data.reports_status:
            try:
                await client.async_delete_fixed_notification(kwargs["id"])
            except OversightApiClientNotFoundError:
                return  # Already gone
            except OversightApiClientError as exception:
                raise HomeAssistantError(str(exception)) from exception
            return
        # Older apps have no delete: hide the badge now and let a 1s expiration
        # make the device purge it, instead of keeping a hidden badge forever.
        await self._async_api_call(
            client.async_send_fixed_notification(
                {"id": kwargs["id"], "visible": False, "expiration": "1s"}
            )
        )

    async def async_handle_screen_on(self) -> None:
        """Handle the screen_on action."""
        await self._async_api_call(self.coordinator.client.async_screen_on())

    async def async_handle_set_clock_appearance(self, **kwargs: Any) -> None:
        """Handle the set_clock_appearance action."""
        client = self.coordinator.client
        # POST replaces every field, so merge onto the current values to keep
        # the ones not given here.
        current = await self._async_api_call(client.async_get_overlay_customization())
        await self._async_api_call(
            client.async_set_overlay_customization(
                {**current, **_to_api_payload(kwargs)}
            )
        )


def _to_api_payload(data: dict[str, Any]) -> dict[str, Any]:
    """Convert action data with snake_case keys to the camelCase API payload."""
    return {_to_camel_case(key): value for key, value in data.items()}


def _to_camel_case(snake_str: str) -> str:
    """Convert snake_case to camelCase."""
    parts = snake_str.split("_")
    return parts[0] + "".join(word.capitalize() for word in parts[1:])
