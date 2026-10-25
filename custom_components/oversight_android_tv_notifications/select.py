"""Select platform for OverSight Android TV."""

from __future__ import annotations

from typing import TYPE_CHECKING

from homeassistant.components.select import SelectEntity, SelectEntityDescription
from homeassistant.const import EntityCategory

from .entity import OversightEntity

if TYPE_CHECKING:
    from homeassistant.core import HomeAssistant
    from homeassistant.helpers.entity_platform import AddConfigEntryEntitiesCallback

    from .data import OversightConfigEntry

PARALLEL_UPDATES = 1

HOT_CORNER_OPTIONS = [
    "top_start",
    "top_end",
    "bottom_start",
    "bottom_end",
]

HOT_CORNER_DESCRIPTION = SelectEntityDescription(
    key="hot_corner",
    translation_key="hot_corner",
    options=HOT_CORNER_OPTIONS,
    entity_category=EntityCategory.CONFIG,
)

NOTIFICATION_LAYOUT_DESCRIPTION = SelectEntityDescription(
    key="notification_layout",
    translation_key="notification_layout",
    entity_category=EntityCategory.CONFIG,
)


async def async_setup_entry(
    hass: HomeAssistant,  # noqa: ARG001
    entry: OversightConfigEntry,
    async_add_entities: AddConfigEntryEntitiesCallback,
) -> None:
    """Set up OverSight select entities."""
    coordinator = entry.runtime_data.coordinator
    async_add_entities(
        [
            OversightHotCornerSelect(
                coordinator=coordinator,
                entity_description=HOT_CORNER_DESCRIPTION,
            ),
            OversightNotificationLayoutSelect(
                coordinator=coordinator,
                entity_description=NOTIFICATION_LAYOUT_DESCRIPTION,
            ),
        ]
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
        await self._async_update_setting(
            self.coordinator.client.async_set_overlay(hotCorner=option)
        )


class OversightNotificationLayoutSelect(OversightEntity, SelectEntity):
    """Select entity for the popup notification layout."""

    @property
    def options(self) -> list[str]:
        """Return the layouts the device has, including custom ones."""
        if self.coordinator.data is None:
            return []
        options = list(self.coordinator.data.layout_names)
        # Keep the current value selectable even if the list didn't include it
        if self.coordinator.data.notification_layout not in options:
            options.append(self.coordinator.data.notification_layout)
        return options

    @property
    def current_option(self) -> str | None:
        """Return the current notification layout."""
        if self.coordinator.data is None:
            return None
        return self.coordinator.data.notification_layout

    async def async_select_option(self, option: str) -> None:
        """Change the notification layout."""
        await self._async_update_setting(
            self.coordinator.client.async_set_notifications(
                notificationLayoutName=option
            )
        )
