"""Tests for the address-announcement webhook."""

from __future__ import annotations

import copy
from http import HTTPStatus
from typing import TYPE_CHECKING, Any
from unittest.mock import patch

import pytest
from homeassistant.components.webhook import async_generate_path
from homeassistant.config_entries import ConfigEntryState
from homeassistant.const import CONF_HOST, CONF_WEBHOOK_ID
from homeassistant.setup import async_setup_component

from .conftest import BASE_URL, DEVICE_ID, HOST, INFO, LAYOUTS, PORT, envelope

if TYPE_CHECKING:
    from collections.abc import Generator

    from homeassistant.core import HomeAssistant
    from pytest_homeassistant_custom_component.common import MockConfigEntry
    from pytest_homeassistant_custom_component.test_util.aiohttp import (
        AiohttpClientMocker,
    )
    from pytest_homeassistant_custom_component.typing import ClientSessionGenerator

HA_IP = "192.168.25.2"
NEW_HOST = "192.168.24.77"
NEW_URL = f"http://{NEW_HOST}:{PORT}"


def _info(*, webhook_configured: bool | None, device_id: str = DEVICE_ID) -> dict:
    """Return INFO as an app reporting webhookConfigured (or not, when None)."""
    info: dict[str, Any] = copy.deepcopy(INFO)
    info["deviceId"] = device_id
    if webhook_configured is not None:
        info["status"]["webhookConfigured"] = webhook_configured
    return info


def _mock_device(
    aioclient_mock: AiohttpClientMocker,
    *,
    webhook_configured: bool | None = False,
    url: str = BASE_URL,
) -> None:
    aioclient_mock.get(
        f"{url}/info", json=envelope(_info(webhook_configured=webhook_configured))
    )
    aioclient_mock.get(f"{url}/", json=envelope(LAYOUTS))
    aioclient_mock.post(f"{url}/set/webhook", json=envelope({}))


def _webhook_posts(aioclient_mock: AiohttpClientMocker) -> list[Any]:
    """Return the bodies of the /set/webhook calls made so far."""
    return [
        call[2] for call in aioclient_mock.mock_calls if call[1].path == "/set/webhook"
    ]


@pytest.fixture(autouse=True)
async def setup_http(hass: HomeAssistant) -> None:
    """Set up the HTTP server so webhooks have a URL and can be called."""
    await async_setup_component(hass, "http", {})


@pytest.fixture(autouse=True)
def mock_source_ip() -> Generator[None]:
    """Report Home Assistant's address on the device's network."""
    with patch(
        "custom_components.oversight_android_tv_notifications.webhook.async_get_source_ip",
        return_value=HA_IP,
    ):
        yield


async def _setup(hass: HomeAssistant, entry: MockConfigEntry) -> None:
    await hass.config_entries.async_setup(entry.entry_id)
    await hass.async_block_till_done()


async def test_setup_sends_webhook_url(
    hass: HomeAssistant,
    config_entry: MockConfigEntry,
    aioclient_mock: AiohttpClientMocker,
) -> None:
    """Setup creates a webhook ID and gives the device its direct URL."""
    _mock_device(aioclient_mock)
    await _setup(hass, config_entry)

    webhook_id = config_entry.data[CONF_WEBHOOK_ID]
    assert webhook_id.startswith("oversight_")
    port = hass.config.api.port
    assert _webhook_posts(aioclient_mock) == [
        {"url": f"http://{HA_IP}:{port}{async_generate_path(webhook_id)}"}
    ]


async def test_webhook_url_sent_once_then_when_missing(
    hass: HomeAssistant,
    config_entry: MockConfigEntry,
    aioclient_mock: AiohttpClientMocker,
) -> None:
    """The URL is sent once per setup, then only if the device loses it."""
    _mock_device(aioclient_mock, webhook_configured=True)
    await _setup(hass, config_entry)
    assert len(_webhook_posts(aioclient_mock)) == 1

    coordinator = config_entry.runtime_data.coordinator
    await coordinator.async_refresh()
    assert len(_webhook_posts(aioclient_mock)) == 1

    aioclient_mock.clear_requests()
    _mock_device(aioclient_mock, webhook_configured=False)
    await coordinator.async_refresh()
    assert len(_webhook_posts(aioclient_mock)) == 1


async def test_old_app_gets_no_webhook(
    hass: HomeAssistant,
    config_entry: MockConfigEntry,
    aioclient_mock: AiohttpClientMocker,
) -> None:
    """Apps that don't report webhookConfigured lack the endpoint; skip it."""
    _mock_device(aioclient_mock, webhook_configured=None)
    await _setup(hass, config_entry)
    assert config_entry.state is ConfigEntryState.LOADED
    assert _webhook_posts(aioclient_mock) == []


async def test_webhook_send_failure_does_not_fail_setup(
    hass: HomeAssistant,
    config_entry: MockConfigEntry,
    aioclient_mock: AiohttpClientMocker,
) -> None:
    """A device that rejects the URL still loads."""
    aioclient_mock.get(
        f"{BASE_URL}/info", json=envelope(_info(webhook_configured=False))
    )
    aioclient_mock.get(f"{BASE_URL}/", json=envelope(LAYOUTS))
    aioclient_mock.post(
        f"{BASE_URL}/set/webhook", json=envelope(None, success=False), status=400
    )
    await _setup(hass, config_entry)
    assert config_entry.state is ConfigEntryState.LOADED


async def _announce(
    hass: HomeAssistant,
    client_factory: ClientSessionGenerator,
    entry: MockConfigEntry,
    body: Any,
) -> int:
    client = await client_factory()
    resp = await client.post(
        async_generate_path(entry.data[CONF_WEBHOOK_ID]), json=body
    )
    await hass.async_block_till_done()
    return resp.status


async def test_announce_new_address_updates_entry(
    hass: HomeAssistant,
    config_entry: MockConfigEntry,
    aioclient_mock: AiohttpClientMocker,
    hass_client_no_auth: ClientSessionGenerator,
) -> None:
    """A verified new address updates the entry and reloads it."""
    _mock_device(aioclient_mock)
    _mock_device(aioclient_mock, url=NEW_URL)
    await _setup(hass, config_entry)

    status = await _announce(
        hass,
        hass_client_no_auth,
        config_entry,
        {"deviceId": DEVICE_ID, "host": NEW_HOST, "port": PORT},
    )
    assert status == HTTPStatus.OK
    assert config_entry.data[CONF_HOST] == NEW_HOST
    assert config_entry.state is ConfigEntryState.LOADED
    assert config_entry.runtime_data.coordinator.client.base_url == NEW_URL


async def test_announce_same_address_is_a_no_op(
    hass: HomeAssistant,
    config_entry: MockConfigEntry,
    aioclient_mock: AiohttpClientMocker,
    hass_client_no_auth: ClientSessionGenerator,
) -> None:
    """Announcing the current address changes nothing."""
    _mock_device(aioclient_mock)
    await _setup(hass, config_entry)
    calls = aioclient_mock.call_count

    status = await _announce(
        hass,
        hass_client_no_auth,
        config_entry,
        {"deviceId": DEVICE_ID, "host": HOST, "port": PORT},
    )
    assert status == HTTPStatus.OK
    assert aioclient_mock.call_count == calls


@pytest.mark.parametrize(
    "body",
    [
        {"deviceId": "device-2", "host": NEW_HOST, "port": PORT},
        {"deviceId": DEVICE_ID, "host": "not-an-ip", "port": PORT},
        {"deviceId": DEVICE_ID, "host": NEW_HOST, "port": 70000},
        ["not", "an", "object"],
    ],
)
async def test_announce_rejects_bad_payload(
    hass: HomeAssistant,
    config_entry: MockConfigEntry,
    aioclient_mock: AiohttpClientMocker,
    hass_client_no_auth: ClientSessionGenerator,
    body: Any,
) -> None:
    """Malformed announcements or another device's ID are rejected."""
    _mock_device(aioclient_mock)
    await _setup(hass, config_entry)

    status = await _announce(hass, hass_client_no_auth, config_entry, body)
    assert status == HTTPStatus.BAD_REQUEST
    assert config_entry.data[CONF_HOST] == HOST


async def test_announce_rejects_other_device_at_address(
    hass: HomeAssistant,
    config_entry: MockConfigEntry,
    aioclient_mock: AiohttpClientMocker,
    hass_client_no_auth: ClientSessionGenerator,
) -> None:
    """An address where another device answers is not adopted."""
    _mock_device(aioclient_mock)
    aioclient_mock.get(
        f"{NEW_URL}/info",
        json=envelope(_info(webhook_configured=False, device_id="device-2")),
    )
    await _setup(hass, config_entry)

    status = await _announce(
        hass,
        hass_client_no_auth,
        config_entry,
        {"deviceId": DEVICE_ID, "host": NEW_HOST, "port": PORT},
    )
    assert status == HTTPStatus.BAD_REQUEST
    assert config_entry.data[CONF_HOST] == HOST


async def test_announce_unreachable_address(
    hass: HomeAssistant,
    config_entry: MockConfigEntry,
    aioclient_mock: AiohttpClientMocker,
    hass_client_no_auth: ClientSessionGenerator,
) -> None:
    """An address that can't be verified yet asks the device to retry."""
    _mock_device(aioclient_mock)
    aioclient_mock.get(f"{NEW_URL}/info", exc=TimeoutError())
    await _setup(hass, config_entry)

    status = await _announce(
        hass,
        hass_client_no_auth,
        config_entry,
        {"deviceId": DEVICE_ID, "host": NEW_HOST, "port": PORT},
    )
    assert status == HTTPStatus.SERVICE_UNAVAILABLE
    assert config_entry.data[CONF_HOST] == HOST


async def test_announce_recovers_entry_that_failed_setup(
    hass: HomeAssistant,
    config_entry: MockConfigEntry,
    aioclient_mock: AiohttpClientMocker,
    hass_client_no_auth: ClientSessionGenerator,
) -> None:
    """A device that moved while Home Assistant was down can still announce."""
    aioclient_mock.get(f"{BASE_URL}/info", exc=TimeoutError())
    _mock_device(aioclient_mock, url=NEW_URL)
    await _setup(hass, config_entry)
    assert config_entry.state is ConfigEntryState.SETUP_RETRY

    status = await _announce(
        hass,
        hass_client_no_auth,
        config_entry,
        {"deviceId": DEVICE_ID, "host": NEW_HOST, "port": PORT},
    )
    assert status == HTTPStatus.OK
    assert config_entry.data[CONF_HOST] == NEW_HOST
    assert config_entry.state is ConfigEntryState.LOADED


async def test_unload_removes_webhook(
    hass: HomeAssistant,
    config_entry: MockConfigEntry,
    aioclient_mock: AiohttpClientMocker,
    hass_client_no_auth: ClientSessionGenerator,
) -> None:
    """After unloading, the webhook no longer handles announcements."""
    _mock_device(aioclient_mock)
    _mock_device(aioclient_mock, url=NEW_URL)
    await _setup(hass, config_entry)
    assert await hass.config_entries.async_unload(config_entry.entry_id)

    await _announce(
        hass,
        hass_client_no_auth,
        config_entry,
        {"deviceId": DEVICE_ID, "host": NEW_HOST, "port": PORT},
    )
    assert config_entry.data[CONF_HOST] == HOST
