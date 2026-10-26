"""Binary sensor platform for OverSight Android TV."""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

from homeassistant.components.binary_sensor import (
    BinarySensorDeviceClass,
    BinarySensorEntity,
    BinarySensorEntityDescription,
)
from homeassistant.const import EntityCategory

from .entity import OversightEntity

if TYPE_CHECKING:
    from collections.abc import Callable

    from homeassistant.core import HomeAssistant
    from homeassistant.helpers.entity_platform import AddConfigEntryEntitiesCallback

    from .coordinator import OversightDeviceState
    from .data import OversightConfigEntry

PARALLEL_UPDATES = 0


@dataclass(frozen=True, kw_only=True)
class OversightStatusSensorDescription(BinarySensorEntityDescription):
    """Describe a binary sensor read from the device's status report."""

    value_fn: Callable[[OversightDeviceState], bool | None]


CONNECTIVITY_DESCRIPTION = BinarySensorEntityDescription(
    key="connectivity",
    device_class=BinarySensorDeviceClass.CONNECTIVITY,
)

STATUS_DESCRIPTIONS: tuple[OversightStatusSensorDescription, ...] = (
    OversightStatusSensorDescription(
        key="screen",
        translation_key="screen",
        value_fn=lambda state: state.screen_on,
    ),
    # Problem sensors: on means the overlay may not show or the service may be killed
    OversightStatusSensorDescription(
        key="overlay_permission",
        translation_key="overlay_permission",
        device_class=BinarySensorDeviceClass.PROBLEM,
        entity_category=EntityCategory.DIAGNOSTIC,
        value_fn=lambda state: _negate(state.overlay_permission_granted),
    ),
    OversightStatusSensorDescription(
        key="battery_optimization",
        translation_key="battery_optimization",
        device_class=BinarySensorDeviceClass.PROBLEM,
        entity_category=EntityCategory.DIAGNOSTIC,
        value_fn=lambda state: state.battery_optimization_skipped,
    ),
)


def _negate(value: bool | None) -> bool | None:  # noqa: FBT001
    """Invert a reported flag, keeping None when it isn't reported."""
    return None if value is None else not value


async def async_setup_entry(
    hass: HomeAssistant,  # noqa: ARG001
    entry: OversightConfigEntry,
    async_add_entities: AddConfigEntryEntitiesCallback,
) -> None:
    """Set up OverSight binary sensors."""
    coordinator = entry.runtime_data.coordinator
    entities: list[BinarySensorEntity] = [
        OversightConnectivitySensor(
            coordinator=coordinator,
            entity_description=CONNECTIVITY_DESCRIPTION,
        )
    ]
    entities.extend(
        OversightStatusSensor(coordinator=coordinator, entity_description=description)
        for description in STATUS_DESCRIPTIONS
    )
    async_add_entities(entities)


class OversightConnectivitySensor(OversightEntity, BinarySensorEntity):
    """Connectivity sensor for an OverSight device."""

    @property
    def available(self) -> bool:
        """Stay available so a failed poll reports off instead of unavailable."""
        return True

    @property
    def is_on(self) -> bool:
        """Return true if the device is reachable."""
        return self.coordinator.last_update_success


class OversightStatusSensor(OversightEntity, BinarySensorEntity):
    """Binary sensor for a value in the device's status report."""

    entity_description: OversightStatusSensorDescription

    @property
    def available(self) -> bool:
        """Return False while unreachable or when the app doesn't report it."""
        return (
            super().available
            and self.coordinator.data is not None
            and self.entity_description.value_fn(self.coordinator.data) is not None
        )

    @property
    def is_on(self) -> bool | None:
        """Return the reported value."""
        if self.coordinator.data is None:
            return None
        return self.entity_description.value_fn(self.coordinator.data)
