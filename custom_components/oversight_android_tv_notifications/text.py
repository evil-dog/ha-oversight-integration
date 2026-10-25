"""Text platform for OverSight Android TV."""

from __future__ import annotations

from typing import TYPE_CHECKING

from homeassistant.components.text import TextEntity, TextEntityDescription
from homeassistant.const import EntityCategory

from .entity import OversightEntity

if TYPE_CHECKING:
    from homeassistant.core import HomeAssistant
    from homeassistant.helpers.entity_platform import AddConfigEntryEntitiesCallback

    from .data import OversightConfigEntry

PARALLEL_UPDATES = 1

DEVICE_NAME_DESCRIPTION = TextEntityDescription(
    key="device_name",
    translation_key="device_name",
    entity_category=EntityCategory.CONFIG,
    native_min=1,
    # The name is advertised as the mDNS service name, which is limited to 63 bytes
    native_max=63,
)


async def async_setup_entry(
    hass: HomeAssistant,  # noqa: ARG001
    entry: OversightConfigEntry,
    async_add_entities: AddConfigEntryEntitiesCallback,
) -> None:
    """Set up OverSight text entities."""
    async_add_entities(
        [
            OversightDeviceNameText(
                coordinator=entry.runtime_data.coordinator,
                entity_description=DEVICE_NAME_DESCRIPTION,
            )
        ]
    )


class OversightDeviceNameText(OversightEntity, TextEntity):
    """Text entity for the name the device advertises on the network."""

    @property
    def native_value(self) -> str | None:
        """Return the current device name."""
        if self.coordinator.data is None:
            return None
        return self.coordinator.data.device_name

    async def async_set_value(self, value: str) -> None:
        """Change the device name."""
        await self._async_update_setting(
            self.coordinator.client.async_set_settings(deviceName=value.strip())
        )
