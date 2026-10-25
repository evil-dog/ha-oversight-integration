"""DataUpdateCoordinator for OverSight Android TV."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import timedelta
from typing import TYPE_CHECKING, Any

from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .api import OversightApiClient, OversightApiClientError
from .const import DEFAULT_SCAN_INTERVAL, DOMAIN

if TYPE_CHECKING:
    from logging import Logger

    from homeassistant.core import HomeAssistant

    from .data import OversightConfigEntry


def _get(section: dict[str, Any], key: str, *, default: Any) -> Any:
    """Return section[key], using default only when it is missing or null."""
    value = section.get(key)
    return default if value is None else value


@dataclass
class OversightDeviceState:
    """Represent the current state of an OverSight device."""

    overlay_visibility: int = 0
    clock_overlay_visibility: int = 0
    hot_corner: str = "top_end"
    display_notifications: bool = True
    notification_duration: int = 8
    display_fixed_notifications: bool = True
    fixed_notifications_visibility: int = 100
    device_name: str = "OverSight Device"
    pixel_shift: bool = False
    remote_port: int = 5001
    device_id: str = ""

    @classmethod
    def from_api_response(cls, data: dict[str, Any]) -> OversightDeviceState:
        """Create state from API /info response."""
        overlay = data.get("overlay") or {}
        settings = data.get("settings") or {}
        notifications = data.get("notifications") or {}

        return cls(
            overlay_visibility=_get(overlay, "overlayVisibility", default=0),
            clock_overlay_visibility=_get(overlay, "clockOverlayVisibility", default=0),
            hot_corner=_get(overlay, "hotCorner", default="top_end"),
            display_notifications=_get(
                notifications, "displayNotifications", default=True
            ),
            notification_duration=_get(
                notifications, "notificationDuration", default=8
            ),
            display_fixed_notifications=_get(
                notifications, "displayFixedNotifications", default=True
            ),
            fixed_notifications_visibility=_get(
                notifications, "fixedNotificationsVisibility", default=100
            ),
            device_name=settings.get("deviceName") or "OverSight Device",
            pixel_shift=_get(settings, "pixelShift", default=False),
            remote_port=_get(settings, "remotePort", default=5001),
            device_id=_get(data, "deviceId", default=""),
        )


class OversightDataUpdateCoordinator(DataUpdateCoordinator[OversightDeviceState]):
    """Coordinator to poll OverSight device state."""

    config_entry: OversightConfigEntry

    def __init__(
        self,
        hass: HomeAssistant,
        logger: Logger,
        config_entry: OversightConfigEntry,
        client: OversightApiClient,
    ) -> None:
        """Initialize the coordinator."""
        super().__init__(
            hass,
            logger,
            config_entry=config_entry,
            name=f"{DOMAIN}_{config_entry.unique_id}",
            update_interval=timedelta(seconds=DEFAULT_SCAN_INTERVAL),
        )
        self.client = client

    async def _async_update_data(self) -> OversightDeviceState:
        """Fetch data from the OverSight device."""
        try:
            data = await self.client.async_get_info()
            return OversightDeviceState.from_api_response(data)
        except OversightApiClientError as exception:
            raise UpdateFailed(exception) from exception
