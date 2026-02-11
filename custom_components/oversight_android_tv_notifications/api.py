"""API client for OverSight Android TV."""

from __future__ import annotations

import asyncio
import socket
from typing import Any

import aiohttp
import async_timeout


class OversightApiClientError(Exception):
    """Exception to indicate a general API error."""


class OversightApiClientCommunicationError(OversightApiClientError):
    """Exception to indicate a communication error."""


class OversightApiClient:
    """API client for OverSight Android TV devices."""

    def __init__(
        self,
        host: str,
        port: int,
        session: aiohttp.ClientSession,
    ) -> None:
        """Initialize the API client."""
        self._host = host
        self._port = port
        self._session = session

    @property
    def base_url(self) -> str:
        """Return the base URL for the device."""
        return f"http://{self._host}:{self._port}"

    async def async_get_info(self) -> dict[str, Any]:
        """Get device info and current state."""
        return await self._api_wrapper("get", f"{self.base_url}/info")

    async def async_set_overlay(self, **kwargs: Any) -> dict[str, Any]:
        """Update overlay settings."""
        return await self._api_wrapper(
            "post", f"{self.base_url}/set/overlay", data=kwargs
        )

    async def async_set_notifications(self, **kwargs: Any) -> dict[str, Any]:
        """Update notification settings."""
        return await self._api_wrapper(
            "post", f"{self.base_url}/set/notifications", data=kwargs
        )

    async def async_set_settings(self, **kwargs: Any) -> dict[str, Any]:
        """Update general settings."""
        return await self._api_wrapper(
            "post", f"{self.base_url}/set/settings", data=kwargs
        )

    async def async_send_notification(self, data: dict[str, Any]) -> dict[str, Any]:
        """Send a popup notification."""
        return await self._api_wrapper("post", f"{self.base_url}/notify", data=data)

    async def async_send_fixed_notification(
        self, data: dict[str, Any]
    ) -> dict[str, Any]:
        """Send a fixed notification (badge)."""
        return await self._api_wrapper(
            "post", f"{self.base_url}/notify_fixed", data=data
        )

    async def async_get_fixed_notifications(self) -> dict[str, Any]:
        """Get active fixed notifications."""
        return await self._api_wrapper("get", f"{self.base_url}/fixed_notifications")

    async def async_screen_on(self) -> dict[str, Any]:
        """Wake the device screen."""
        return await self._api_wrapper("post", f"{self.base_url}/screen_on")

    async def async_restart_service(self) -> dict[str, Any]:
        """Restart the overlay service."""
        return await self._api_wrapper("post", f"{self.base_url}/restart_service")

    async def _api_wrapper(
        self,
        method: str,
        url: str,
        data: dict | None = None,
        retries: int = 2,
    ) -> dict[str, Any]:
        """Wrap API calls with error handling and retry on connection errors."""
        last_exception: Exception | None = None
        for attempt in range(1 + retries):
            try:
                async with async_timeout.timeout(10):
                    response = await self._session.request(
                        method=method,
                        url=url,
                        json=data,
                    )
                    response.raise_for_status()
                    resp_json = await response.json()
            except (TimeoutError, aiohttp.ClientError, socket.gaierror) as exception:
                last_exception = exception
                if attempt < retries:
                    await asyncio.sleep(1)
                    continue
            except Exception as exception:
                msg = (
                    "Unexpected error communicating with OverSight device - "
                    f"{exception}"
                )
                raise OversightApiClientError(msg) from exception
            else:
                if not resp_json.get("success", False):
                    msg = resp_json.get("message", "Unknown API error")
                    raise OversightApiClientError(msg)

                return resp_json.get("result", {})

        msg = (
            "Error communicating with OverSight device at "
            f"{self._host}:{self._port} - {last_exception}"
        )
        raise OversightApiClientCommunicationError(msg) from last_exception
