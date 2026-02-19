"""Number platform for OverSight Android TV."""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

from homeassistant.components.number import (
    NumberEntity,
    NumberEntityDescription,
    NumberMode,
)
from homeassistant.const import PERCENTAGE, EntityCategory, UnitOfTime

from .entity import OversightEntity

if TYPE_CHECKING:
    from homeassistant.core import HomeAssistant
    from homeassistant.helpers.entity_platform import AddEntitiesCallback

    from .data import OversightConfigEntry


@dataclass(frozen=True, kw_only=True)
class OversightNumberDescription(NumberEntityDescription):
    """Describe an OverSight number entity."""

    state_key: str = ""
    api_method: str = ""
    api_param: str = ""


ENTITY_DESCRIPTIONS: tuple[OversightNumberDescription, ...] = (
    OversightNumberDescription(
        key="overlay_visibility",
        translation_key="overlay_visibility",
        native_min_value=0,
        native_max_value=95,
        native_step=5,
        native_unit_of_measurement=PERCENTAGE,
        mode=NumberMode.SLIDER,
        entity_category=EntityCategory.CONFIG,
        state_key="overlay_visibility",
        api_method="async_set_overlay",
        api_param="overlayVisibility",
    ),
    OversightNumberDescription(
        key="clock_overlay_visibility",
        translation_key="clock_overlay_visibility",
        native_min_value=0,
        native_max_value=100,
        native_step=5,
        native_unit_of_measurement=PERCENTAGE,
        mode=NumberMode.SLIDER,
        entity_category=EntityCategory.CONFIG,
        state_key="clock_overlay_visibility",
        api_method="async_set_overlay",
        api_param="clockOverlayVisibility",
    ),
    OversightNumberDescription(
        key="notification_duration",
        translation_key="notification_duration",
        native_min_value=3,
        native_max_value=30,
        native_step=1,
        native_unit_of_measurement=UnitOfTime.SECONDS,
        mode=NumberMode.SLIDER,
        entity_category=EntityCategory.CONFIG,
        state_key="notification_duration",
        api_method="async_set_notifications",
        api_param="notificationDuration",
    ),
    OversightNumberDescription(
        key="fixed_notifications_visibility",
        translation_key="fixed_notifications_visibility",
        native_min_value=0,
        native_max_value=100,
        native_step=5,
        native_unit_of_measurement=PERCENTAGE,
        mode=NumberMode.SLIDER,
        entity_category=EntityCategory.CONFIG,
        state_key="fixed_notifications_visibility",
        api_method="async_set_notifications",
        api_param="fixedNotificationsVisibility",
    ),
)


async def async_setup_entry(
    hass: HomeAssistant,  # noqa: ARG001
    entry: OversightConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up OverSight number entities."""
    async_add_entities(
        OversightNumber(
            coordinator=entry.runtime_data.coordinator,
            entity_description=description,
        )
        for description in ENTITY_DESCRIPTIONS
    )


class OversightNumber(OversightEntity, NumberEntity):
    """Number entity for an OverSight device setting."""

    entity_description: OversightNumberDescription

    @property
    def native_value(self) -> float | None:
        """Return the current value."""
        if self.coordinator.data is None:
            return None
        return getattr(self.coordinator.data, self.entity_description.state_key, None)

    async def async_set_native_value(self, value: float) -> None:
        """Set the value."""
        client = self.coordinator.client
        method = getattr(client, self.entity_description.api_method)
        await method(**{self.entity_description.api_param: int(value)})
        await self.coordinator.async_request_refresh()
