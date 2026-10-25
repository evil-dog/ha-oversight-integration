"""Tests for the OverSight API client."""

from __future__ import annotations

from typing import TYPE_CHECKING

import pytest
from homeassistant.helpers.aiohttp_client import async_get_clientsession

from custom_components.oversight_android_tv_notifications.api import (
    OversightApiClient,
    OversightApiClientCommunicationError,
    OversightApiClientError,
)

from .conftest import BASE_URL, HOST, PORT, envelope

if TYPE_CHECKING:
    from homeassistant.core import HomeAssistant
    from pytest_homeassistant_custom_component.test_util.aiohttp import (
        AiohttpClientMocker,
    )


@pytest.fixture
async def client(
    hass: HomeAssistant,
    aioclient_mock: AiohttpClientMocker,
) -> OversightApiClient:
    """Return a client bound to the mocked session."""
    return OversightApiClient(HOST, PORT, async_get_clientsession(hass))


async def test_result_returned(
    client: OversightApiClient, aioclient_mock: AiohttpClientMocker
) -> None:
    """The result object of a successful response is returned."""
    aioclient_mock.get(f"{BASE_URL}/info", json=envelope({"deviceId": "x"}))
    assert await client.async_get_info() == {"deviceId": "x"}


async def test_null_result_is_empty_dict(
    client: OversightApiClient, aioclient_mock: AiohttpClientMocker
) -> None:
    """A successful response with "result": null returns {}."""
    aioclient_mock.post(f"{BASE_URL}/screen_on", json=envelope(None))
    assert await client.async_screen_on() == {}


async def test_device_error_message_raised_without_retry(
    client: OversightApiClient, aioclient_mock: AiohttpClientMocker
) -> None:
    """A 400 surfaces the device's message and is not retried."""
    aioclient_mock.post(
        f"{BASE_URL}/notify_fixed",
        status=400,
        json={
            "success": False,
            "message": "New fixed notification requires icon or text",
            "result": None,
        },
    )
    with pytest.raises(OversightApiClientError, match="requires icon or text") as err:
        await client.async_send_fixed_notification({"id": "a"})
    assert not isinstance(err.value, OversightApiClientCommunicationError)
    assert aioclient_mock.call_count == 1


async def test_non_json_error_response(
    client: OversightApiClient, aioclient_mock: AiohttpClientMocker
) -> None:
    """A response without a JSON object reports the HTTP status."""
    aioclient_mock.get(f"{BASE_URL}/info", status=404, text="")
    with pytest.raises(OversightApiClientError, match="HTTP 404"):
        await client.async_get_info()


async def test_timeout_retried(
    client: OversightApiClient, aioclient_mock: AiohttpClientMocker
) -> None:
    """Idempotent requests are retried, then raise a communication error."""
    aioclient_mock.get(f"{BASE_URL}/info", exc=TimeoutError())
    with pytest.raises(OversightApiClientCommunicationError):
        await client.async_get_info()
    assert aioclient_mock.call_count == 3


async def test_notify_not_retried(
    client: OversightApiClient, aioclient_mock: AiohttpClientMocker
) -> None:
    """A popup is never resent, so a timeout cannot show it twice."""
    aioclient_mock.post(f"{BASE_URL}/notify", exc=TimeoutError())
    with pytest.raises(OversightApiClientCommunicationError):
        await client.async_send_notification({"message": "hi"})
    assert aioclient_mock.call_count == 1
