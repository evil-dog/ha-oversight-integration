"""DataUpdateCoordinator for OverSight Android TV."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import timedelta
from typing import TYPE_CHECKING, Any

from homeassistant.core import callback
from homeassistant.helpers import device_registry as dr
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .api import OversightApiClient, OversightApiClientError
from .const import DEFAULT_DEVICE_NAME, DEFAULT_SCAN_INTERVAL, DOMAIN

if TYPE_CHECKING:
    from logging import Logger

    from homeassistant.core import HomeAssistant

    from .data import OversightConfigEntry

DEFAULT_LAYOUT = "Default"
# versionCode reported by local/debug builds instead of major*10000 + minor*100 + patch.
# Release v0.0.1 also maps to 1, but it predates status reporting so never sends it.
DEV_BUILD_VERSION = 1


def format_app_version(version: int | None) -> str | None:
    """Turn the app's versionCode (e.g. 302) into a version string ("0.3.2")."""
    if version is None:
        return None
    if version == DEV_BUILD_VERSION:
        return "development build"
    return f"{version // 10000}.{version // 100 % 100}.{version % 100}"


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
    # From the status block; None when the app is too old to report it
    app_version: int | None = None
    screen_on: bool | None = None
    overlay_permission_granted: bool | None = None
    # Only SKIPPED is a problem; BLOCKED means the device can't grant the
    # exemption on screen (e.g. Google TV), which the app treats as fine
    battery_optimization_skipped: bool | None = None

    @property
    def reports_status(self) -> bool:
        """
        Return whether the app reports status.

        Apps that do also support DELETE /notify_fixed/{id}; both arrived in
        the same release.
        """
        return self.app_version is not None

    @classmethod
    def from_api_response(
        cls, info: dict[str, Any], layouts: dict[str, Any]
    ) -> OversightDeviceState:
        """Create state from the /info (or /set/*) result and the / layout list."""
        overlay = info.get("overlay") or {}
        settings = info.get("settings") or {}
        notifications = info.get("notifications") or {}
        status = info.get("status") or {}

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
            app_version=status.get("version"),
            screen_on=status.get("isScreenOn"),
            overlay_permission_granted=_state_is(
                status.get("permissionState"), "GRANTED"
            ),
            battery_optimization_skipped=_state_is(
                status.get("batteryOptimizationState"), "SKIPPED"
            ),
        )


def _state_is(value: str | None, expected: str) -> bool | None:
    """Compare a reported enum value, keeping None when it isn't reported."""
    return None if value is None else value == expected


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
        state = OversightDeviceState.from_api_response(info, self._layouts)
        self._async_update_sw_version(state)
        return state

    @callback
    def async_set_info(self, info: dict[str, Any]) -> None:
        """Apply the settings a /set/* call returns, without waiting for a poll."""
        self.async_set_updated_data(
            OversightDeviceState.from_api_response(info, self._layouts)
        )

    @callback
    def _async_update_sw_version(self, state: OversightDeviceState) -> None:
        """Keep the device's software version current when the app is updated."""
        sw_version = format_app_version(state.app_version)
        if sw_version is None:
            return
        device_registry = dr.async_get(self.hass)
        for device in dr.async_entries_for_config_entry(
            device_registry, self.config_entry.entry_id
        ):
            if device.sw_version != sw_version:
                device_registry.async_update_device(device.id, sw_version=sw_version)
