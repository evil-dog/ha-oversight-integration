"""DataUpdateCoordinator for OverSight Android TV."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import timedelta
from typing import TYPE_CHECKING, Any

from homeassistant.core import callback
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .api import OversightApiClient, OversightApiClientError
from .const import DEFAULT_DEVICE_NAME, DEFAULT_SCAN_INTERVAL, DOMAIN

if TYPE_CHECKING:
    from logging import Logger

    from homeassistant.core import HomeAssistant

    from .data import OversightConfigEntry

DEFAULT_LAYOUT = "Default"


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
    notification_layout: str = DEFAULT_LAYOUT
    display_fixed_notifications: bool = True
    fixed_notifications_visibility: int = 100
    device_name: str = DEFAULT_DEVICE_NAME
    pixel_shift: bool = False
    display_debug: bool = False
    layout_names: list[str] = field(default_factory=list)

    @classmethod
    def from_api_response(
        cls, info: dict[str, Any], layouts: dict[str, Any]
    ) -> OversightDeviceState:
        """Create state from the /info (or /set/*) result and the / layout list."""
        overlay = info.get("overlay") or {}
        settings = info.get("settings") or {}
        notifications = info.get("notifications") or {}

        layout_names = [
            layout["name"] for layout in layouts.get("list") or [] if layout.get("name")
        ]
        # Same precedence as the device: an explicit layout name, else the selected one
        notification_layout = (
            notifications.get("notificationLayoutName")
            or layouts.get("selected")
            or DEFAULT_LAYOUT
        )

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
            notification_layout=notification_layout,
            display_fixed_notifications=_get(
                notifications, "displayFixedNotifications", default=True
            ),
            fixed_notifications_visibility=_get(
                notifications, "fixedNotificationsVisibility", default=100
            ),
            device_name=settings.get("deviceName") or DEFAULT_DEVICE_NAME,
            pixel_shift=_get(settings, "pixelShift", default=False),
            display_debug=_get(settings, "displayDebug", default=False),
            layout_names=layout_names,
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
        self._layouts: dict[str, Any] = {}

    async def _async_update_data(self) -> OversightDeviceState:
        """Fetch data from the OverSight device."""
        try:
            info = await self.client.async_get_info()
            self._layouts = await self.client.async_get_layouts()
        except OversightApiClientError as exception:
            raise UpdateFailed(exception) from exception
        return OversightDeviceState.from_api_response(info, self._layouts)

    @callback
    def async_set_info(self, info: dict[str, Any]) -> None:
        """Apply the settings a /set/* call returns, without waiting for a poll."""
        self.async_set_updated_data(
            OversightDeviceState.from_api_response(info, self._layouts)
        )
