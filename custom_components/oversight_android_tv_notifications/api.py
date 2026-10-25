"""API client for OverSight Android TV."""

from __future__ import annotations

import asyncio
import socket
from http import HTTPStatus
from typing import Any
from urllib.parse import quote

import aiohttp

REQUEST_TIMEOUT = 10
RETRIES = 2
RETRY_DELAY = 1


class OversightApiClientError(Exception):
    """Exception to indicate a general API error."""


class OversightApiClientCommunicationError(OversightApiClientError):
    """Exception to indicate a communication error."""


class OversightApiClientNotFoundError(OversightApiClientError):
    """Exception to indicate the requested item does not exist on the device."""


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
        # Not idempotent: retrying after a timeout could show the popup twice
        return await self._api_wrapper(
            "post", f"{self.base_url}/notify", data=data, retry=False
        )

    async def async_send_fixed_notification(
        self, data: dict[str, Any]
    ) -> dict[str, Any]:
        """Send a fixed notification (badge)."""
        return await self._api_wrapper(
            "post", f"{self.base_url}/notify_fixed", data=data
        )

    async def async_delete_fixed_notification(self, notification_id: str) -> None:
        """Delete a fixed notification (badge); needs an app that reports status."""
        await self._api_wrapper(
            "delete",
            f"{self.base_url}/notify_fixed/{quote(notification_id, safe='')}",
        )

    async def async_get_layouts(self) -> dict[str, Any]:
        """Get the notification layout list and the selected layout."""
        return await self._api_wrapper("get", f"{self.base_url}/")

    async def async_get_overlay_customization(self) -> dict[str, Any]:
        """Get the clock appearance settings."""
        return await self._api_wrapper("get", f"{self.base_url}/overlay_customization")

    async def async_set_overlay_customization(
        self, data: dict[str, Any]
    ) -> dict[str, Any]:
        """Replace the clock appearance settings; omitted fields reset to defaults."""
        return await self._api_wrapper(
            "post", f"{self.base_url}/overlay_customization", data=data
        )

    async def async_screen_on(self) -> dict[str, Any]:
        """Wake the device screen."""
        return await self._api_wrapper("post", f"{self.base_url}/screen_on")

    async def async_restart_service(self) -> dict[str, Any]:
        """Restart the overlay service."""
        return await self._api_wrapper(
            "post", f"{self.base_url}/restart_service", retry=False
        )

    async def _api_wrapper(
        self,
        method: str,
        url: str,
        data: dict | None = None,
        *,
        retry: bool = True,
    ) -> dict[str, Any]:
        """
        Wrap API calls with error handling.

        Connection errors and timeouts are retried when [retry] is set. Error
        responses from the device are raised immediately with its message.
        """
        last_exception: Exception | None = None
        for attempt in range(1 + RETRIES if retry else 1):
            if attempt:
                await asyncio.sleep(RETRY_DELAY)
            try:
                async with (
                    asyncio.timeout(REQUEST_TIMEOUT),
                    self._session.request(
                        method=method, url=url, json=data
                    ) as response,
                ):
                    status = response.status
                    resp_json = await _read_json(response)
            except (TimeoutError, aiohttp.ClientError, socket.gaierror) as exception:
                last_exception = exception
                continue

            if resp_json is None:
                msg = f"Invalid response from OverSight device (HTTP {status})"
                raise OversightApiClientError(msg)
            if status >= 400 or not resp_json.get("success", False):  # noqa: PLR2004
                msg = resp_json.get("message") or f"HTTP {status}"
                if status == HTTPStatus.NOT_FOUND:
                    raise OversightApiClientNotFoundError(msg)
                raise OversightApiClientError(msg)
            return resp_json.get("result") or {}

        msg = (
            "Error communicating with OverSight device at "
            f"{self._host}:{self._port} - {last_exception}"
        )
        raise OversightApiClientCommunicationError(msg) from last_exception


async def _read_json(response: aiohttp.ClientResponse) -> dict[str, Any] | None:
    """Return the response body as a JSON object, or None if it is not one."""
    try:
        body = await response.json(content_type=None)
    except ValueError:
        return None
    return body if isinstance(body, dict) else None
