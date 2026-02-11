"""DataUpdateCoordinator for OverSight Android TV."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import timedelta
from typing import TYPE_CHECKING, Any

from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .api import OversightApiClient, OversightApiClientError
from .const import DEFAULT_SCAN_INTERVAL

if TYPE_CHECKING:
    from logging import Logger

    from homeassistant.core import HomeAssistant


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
            overlay_visibility=overlay.get("overlayVisibility", 0) or 0,
            clock_overlay_visibility=overlay.get("clockOverlayVisibility", 0) or 0,
            hot_corner=overlay.get("hotCorner", "top_end") or "top_end",
            display_notifications=notifications.get("displayNotifications")
            if notifications.get("displayNotifications") is not None
            else True,
            notification_duration=notifications.get("notificationDuration", 8) or 8,
            display_fixed_notifications=notifications.get("displayFixedNotifications")
            if notifications.get("displayFixedNotifications") is not None
            else True,
            fixed_notifications_visibility=notifications.get(
                "fixedNotificationsVisibility", 100
            )
            or 100,
            device_name=settings.get("deviceName", "OverSight Device")
            or "OverSight Device",
            pixel_shift=settings.get("pixelShift", False) or False,
            remote_port=settings.get("remotePort", 5001) or 5001,
            device_id=data.get("deviceId", ""),
        )


class OversightDataUpdateCoordinator(DataUpdateCoordinator[OversightDeviceState]):
    """Coordinator to poll OverSight device state."""

    def __init__(
        self,
        hass: HomeAssistant,
        logger: Logger,
        name: str,
        client: OversightApiClient,
    ) -> None:
        """Initialize the coordinator."""
        super().__init__(
            hass,
            logger,
            name=name,
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
