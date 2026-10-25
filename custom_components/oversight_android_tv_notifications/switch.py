"""Switch platform for OverSight Android TV."""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING, Any

from homeassistant.components.switch import SwitchEntity, SwitchEntityDescription
from homeassistant.const import EntityCategory

from .entity import OversightEntity

if TYPE_CHECKING:
    from homeassistant.core import HomeAssistant
    from homeassistant.helpers.entity_platform import AddConfigEntryEntitiesCallback

    from .data import OversightConfigEntry

PARALLEL_UPDATES = 1


@dataclass(frozen=True, kw_only=True)
class OversightSwitchDescription(SwitchEntityDescription):
    """Describe an OverSight switch entity."""

    state_key: str = ""
    api_method: str = ""
    api_param: str = ""


ENTITY_DESCRIPTIONS: tuple[OversightSwitchDescription, ...] = (
    OversightSwitchDescription(
        key="display_notifications",
        translation_key="display_notifications",
        entity_category=EntityCategory.CONFIG,
        state_key="display_notifications",
        api_method="async_set_notifications",
        api_param="displayNotifications",
    ),
    OversightSwitchDescription(
        key="display_fixed_notifications",
        translation_key="display_fixed_notifications",
        entity_category=EntityCategory.CONFIG,
        state_key="display_fixed_notifications",
        api_method="async_set_notifications",
        api_param="displayFixedNotifications",
    ),
    OversightSwitchDescription(
        key="pixel_shift",
        translation_key="pixel_shift",
        entity_category=EntityCategory.CONFIG,
        state_key="pixel_shift",
        api_method="async_set_settings",
        api_param="pixelShift",
    ),
    OversightSwitchDescription(
        key="display_debug",
        translation_key="display_debug",
        entity_category=EntityCategory.CONFIG,
        entity_registry_enabled_default=False,
        state_key="display_debug",
        api_method="async_set_settings",
        api_param="displayDebug",
    ),
)


async def async_setup_entry(
    hass: HomeAssistant,  # noqa: ARG001
    entry: OversightConfigEntry,
    async_add_entities: AddConfigEntryEntitiesCallback,
) -> None:
    """Set up OverSight switch entities."""
    async_add_entities(
        OversightSwitch(
            coordinator=entry.runtime_data.coordinator,
            entity_description=description,
        )
        for description in ENTITY_DESCRIPTIONS
    )


class OversightSwitch(OversightEntity, SwitchEntity):
    """Switch entity for an OverSight device setting."""

    entity_description: OversightSwitchDescription

    @property
    def is_on(self) -> bool | None:
        """Return true if the switch is on."""
        if self.coordinator.data is None:
            return None
        return getattr(self.coordinator.data, self.entity_description.state_key, None)

    async def async_turn_on(self, **kwargs: Any) -> None:  # noqa: ARG002
        """Turn on the switch."""
        await self._async_set(value=True)

    async def async_turn_off(self, **kwargs: Any) -> None:  # noqa: ARG002
        """Turn off the switch."""
        await self._async_set(value=False)

    async def _async_set(self, *, value: bool) -> None:
        """Send the new switch state to the device."""
        client = self.coordinator.client
        method = getattr(client, self.entity_description.api_method)
        await self._async_update_setting(
            method(**{self.entity_description.api_param: value})
        )
