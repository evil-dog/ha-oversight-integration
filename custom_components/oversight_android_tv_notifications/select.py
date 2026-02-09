"""Select platform for OverSight Android TV."""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

from homeassistant.components.select import SelectEntity, SelectEntityDescription
from homeassistant.const import EntityCategory

from .entity import OversightEntity

if TYPE_CHECKING:
    from homeassistant.core import HomeAssistant
    from homeassistant.helpers.entity_platform import AddEntitiesCallback

    from .data import OversightConfigEntry

HOT_CORNER_OPTIONS = [
    "top_start",
    "top_end",
    "bottom_start",
    "bottom_end",
]

ENTITY_DESCRIPTIONS = (
    SelectEntityDescription(
        key="hot_corner",
        translation_key="hot_corner",
        options=HOT_CORNER_OPTIONS,
        entity_category=EntityCategory.CONFIG,
    ),
)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: OversightConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up OverSight select entities."""
    async_add_entities(
        OversightHotCornerSelect(
            coordinator=entry.runtime_data.coordinator,
            entity_description=description,
        )
        for description in ENTITY_DESCRIPTIONS
    )


class OversightHotCornerSelect(OversightEntity, SelectEntity):
    """Select entity for the hot corner position."""

    @property
    def current_option(self) -> str | None:
        """Return the current hot corner setting."""
        if self.coordinator.data is None:
            return None
        return self.coordinator.data.hot_corner

    async def async_select_option(self, option: str) -> None:
        """Change the hot corner setting."""
        await self.coordinator.client.async_set_overlay(hotCorner=option)
        await self.coordinator.async_request_refresh()
