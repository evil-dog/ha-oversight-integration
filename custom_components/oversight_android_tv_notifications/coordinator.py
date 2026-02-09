"""DataUpdateCoordinator for oversight_android_tv_notifications."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from homeassistant.exceptions import ConfigEntryAuthFailed
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .api import (
    OversightAndroidTvNotificationsApiClientAuthenticationError,
    OversightAndroidTvNotificationsApiClientError,
)

if TYPE_CHECKING:
    from .data import OversightAndroidTvNotificationsConfigEntry


# https://developers.home-assistant.io/docs/integration_fetching_data#coordinated-single-api-poll-for-data-for-all-entities
class OversightAndroidTvNotificationsDataUpdateCoordinator(DataUpdateCoordinator):
    """Class to manage fetching data from the API."""

    config_entry: OversightAndroidTvNotificationsConfigEntry

    async def _async_update_data(self) -> Any:
        """Update data via library."""
        try:
            return await self.config_entry.runtime_data.client.async_get_data()
        except OversightAndroidTvNotificationsApiClientAuthenticationError as exception:
            raise ConfigEntryAuthFailed(exception) from exception
        except OversightAndroidTvNotificationsApiClientError as exception:
            raise UpdateFailed(exception) from exception
