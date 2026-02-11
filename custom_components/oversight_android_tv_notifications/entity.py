"""Base entity for the OverSight Android TV integration."""

from __future__ import annotations

from typing import TYPE_CHECKING

from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN
from .coordinator import OversightDataUpdateCoordinator

if TYPE_CHECKING:
    from homeassistant.helpers.entity import EntityDescription


class OversightEntity(CoordinatorEntity[OversightDataUpdateCoordinator]):
    """Base entity for OverSight devices."""

    _attr_has_entity_name = True

    def __init__(
        self,
        coordinator: OversightDataUpdateCoordinator,
        entity_description: EntityDescription,
    ) -> None:
        """Initialize the entity."""
        super().__init__(coordinator)
        self.entity_description = entity_description
        self._attr_unique_id = (
            f"{coordinator.config_entry.unique_id}_{entity_description.key}"
        )
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, coordinator.config_entry.unique_id)},
            name=coordinator.config_entry.title,
            manufacturer="OverSight",
            model="Android TV Overlay",
        )
