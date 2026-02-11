"""Binary sensor platform for OverSight Android TV."""

from __future__ import annotations

from typing import TYPE_CHECKING

from homeassistant.components.binary_sensor import (
    BinarySensorDeviceClass,
    BinarySensorEntity,
    BinarySensorEntityDescription,
)

from .entity import OversightEntity

if TYPE_CHECKING:
    from homeassistant.core import HomeAssistant
    from homeassistant.helpers.entity_platform import AddEntitiesCallback

    from .data import OversightConfigEntry

ENTITY_DESCRIPTIONS = (
    BinarySensorEntityDescription(
        key="connectivity",
        device_class=BinarySensorDeviceClass.CONNECTIVITY,
    ),
)


async def async_setup_entry(
    hass: HomeAssistant,  # noqa: ARG001
    entry: OversightConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up OverSight binary sensors."""
    async_add_entities(
        OversightConnectivitySensor(
            coordinator=entry.runtime_data.coordinator,
            entity_description=entity_description,
        )
        for entity_description in ENTITY_DESCRIPTIONS
    )


class OversightConnectivitySensor(OversightEntity, BinarySensorEntity):
    """Connectivity sensor for an OverSight device."""

    @property
    def is_on(self) -> bool:
        """Return true if the device is reachable."""
        return self.coordinator.last_update_success
