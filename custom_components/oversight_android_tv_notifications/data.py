"""Custom types for oversight_android_tv_notifications."""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from homeassistant.config_entries import ConfigEntry
    from homeassistant.loader import Integration

    from .api import OversightAndroidTvNotificationsApiClient
    from .coordinator import OversightAndroidTvNotificationsDataUpdateCoordinator


type OversightAndroidTvNotificationsConfigEntry = ConfigEntry[OversightAndroidTvNotificationsData]


@dataclass
class OversightAndroidTvNotificationsData:
    """Data for the Oversight Android TV Notifications integration."""

    client: OversightAndroidTvNotificationsApiClient
    coordinator: OversightAndroidTvNotificationsDataUpdateCoordinator
    integration: Integration
