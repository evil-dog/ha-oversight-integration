"""Button platform for OverSight Android TV."""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING, Any

from homeassistant.components.button import (
    ButtonDeviceClass,
    ButtonEntity,
    ButtonEntityDescription,
)
from homeassistant.const import EntityCategory

from .entity import OversightEntity

if TYPE_CHECKING:
    from collections.abc import Awaitable, Callable

    from homeassistant.core import HomeAssistant
    from homeassistant.helpers.entity_platform import AddConfigEntryEntitiesCallback

    from .api import OversightApiClient
    from .data import OversightConfigEntry

PARALLEL_UPDATES = 1


@dataclass(frozen=True, kw_only=True)
class OversightButtonDescription(ButtonEntityDescription):
    """Describe an OverSight button entity."""

    press_fn: Callable[[OversightApiClient], Awaitable[dict[str, Any]]]


ENTITY_DESCRIPTIONS: tuple[OversightButtonDescription, ...] = (
    OversightButtonDescription(
        key="screen_on",
        translation_key="screen_on",
        press_fn=lambda client: client.async_screen_on(),
    ),
    OversightButtonDescription(
        key="restart_service",
        translation_key="restart_service",
        device_class=ButtonDeviceClass.RESTART,
        entity_category=EntityCategory.CONFIG,
        press_fn=lambda client: client.async_restart_service(),
    ),
)


async def async_setup_entry(
    hass: HomeAssistant,  # noqa: ARG001
    entry: OversightConfigEntry,
    async_add_entities: AddConfigEntryEntitiesCallback,
) -> None:
    """Set up OverSight button entities."""
    async_add_entities(
        OversightButton(
            coordinator=entry.runtime_data.coordinator,
            entity_description=description,
        )
        for description in ENTITY_DESCRIPTIONS
    )


class OversightButton(OversightEntity, ButtonEntity):
    """Button entity for an OverSight device command."""

    entity_description: OversightButtonDescription

    async def async_press(self) -> None:
        """Send the command to the device."""
        await self._async_api_call(
            self.entity_description.press_fn(self.coordinator.client)
        )
