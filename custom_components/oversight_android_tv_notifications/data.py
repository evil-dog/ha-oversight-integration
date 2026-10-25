"""Custom types for the OverSight Android TV integration."""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from homeassistant.config_entries import ConfigEntry

    from .coordinator import OversightDataUpdateCoordinator


type OversightConfigEntry = ConfigEntry[OversightData]


@dataclass
class OversightData:
    """Runtime data for the OverSight integration."""

    coordinator: OversightDataUpdateCoordinator
