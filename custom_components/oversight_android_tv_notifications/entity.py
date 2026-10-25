"""Base entity for the OverSight Android TV integration."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from homeassistant.exceptions import HomeAssistantError
from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .api import OversightApiClientError
from .const import DOMAIN
from .coordinator import OversightDataUpdateCoordinator

if TYPE_CHECKING:
    from collections.abc import Awaitable

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

    async def _async_api_call[T](self, call: Awaitable[T]) -> T:
        """Await an API call, raising client errors as HomeAssistantError."""
        try:
            return await call
        except OversightApiClientError as exception:
            raise HomeAssistantError(str(exception)) from exception

    async def _async_update_setting(self, call: Awaitable[dict[str, Any]]) -> None:
        """Send a /set/* call and apply the device state it returns."""
        self.coordinator.async_set_info(await self._async_api_call(call))
