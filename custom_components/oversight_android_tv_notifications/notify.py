"""Notify platform for OverSight Android TV."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from homeassistant.components.notify import NotifyEntity

from .entity import OversightEntity

if TYPE_CHECKING:
    from homeassistant.core import HomeAssistant
    from homeassistant.helpers.entity_platform import AddEntitiesCallback

    from .data import OversightConfigEntry

from homeassistant.helpers.entity import EntityDescription


async def async_setup_entry(
    hass: HomeAssistant,  # noqa: ARG001
    entry: OversightConfigEntry,
    async_add_entities: AddEntitiesCallback,
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
    """Notify entity for sending popup notifications to an OverSight device."""

    async def async_send_message(
        self, message: str, title: str | None = None, **kwargs: Any
    ) -> None:
        """Send a popup notification to the device."""
        data: dict[str, Any] = {"message": message}
        if title:
            data["title"] = title

        # Pass through optional fields from the data dict
        extra = kwargs.get("data") or {}
        for field in (
            "source",
            "image",
            "video",
            "smallIcon",
            "largeIcon",
            "corner",
            "duration",
        ):
            if field in extra:
                data[field] = extra[field]

        await self.coordinator.client.async_send_notification(data)
