"""Fixtures for the OverSight Android TV tests."""

from __future__ import annotations

import copy
from typing import TYPE_CHECKING, Any

import pytest
from homeassistant.const import CONF_HOST, CONF_PORT
from pytest_homeassistant_custom_component.common import MockConfigEntry

from custom_components.oversight_android_tv_notifications import api
from custom_components.oversight_android_tv_notifications.const import DOMAIN

if TYPE_CHECKING:
    from homeassistant.core import HomeAssistant
    from pytest_homeassistant_custom_component.test_util.aiohttp import (
        AiohttpClientMocker,
    )

HOST = "192.168.1.50"
PORT = 5001
BASE_URL = f"http://{HOST}:{PORT}"
DEVICE_ID = "device-1"
TITLE = "Living Room TV"

INFO: dict[str, Any] = {
    "deviceId": DEVICE_ID,
    "overlay": {
        "overlayVisibility": 20,
        "clockOverlayVisibility": 100,
        "hotCorner": "bottom_start",
    },
    "settings": {
        "deviceName": TITLE,
        "remotePort": PORT,
        "displayDebug": None,
        "pixelShift": True,
    },
    "notifications": {
        "displayNotifications": True,
        "notificationLayoutName": None,
        "notificationDuration": 8,
        "displayFixedNotifications": True,
        # 0 is a valid value and must not fall back to the default of 100
        "fixedNotificationsVisibility": 0,
    },
    "status": None,
}

LAYOUTS: dict[str, Any] = {
    "list": [{"name": "Default"}, {"name": "Minimalist"}, {"name": "Only Icon"}],
    "selected": "Minimalist",
}


def envelope(result: Any = None, *, success: bool = True) -> dict[str, Any]:
    """Wrap a result in the device's API response envelope."""
    return {"success": success, "message": "OK", "result": result}


def info_without_device_id() -> dict[str, Any]:
    """Return INFO the way /set/* returns it: the same fields minus deviceId."""
    info = copy.deepcopy(INFO)
    del info["deviceId"]
    return info


@pytest.fixture(autouse=True)
def auto_enable_custom_integrations(
    enable_custom_integrations: None,
) -> None:
    """Enable loading the integration from custom_components."""
    return


@pytest.fixture(autouse=True)
def no_retry_delay(monkeypatch: pytest.MonkeyPatch) -> None:
    """Do not sleep between API retries."""
    monkeypatch.setattr(api, "RETRY_DELAY", 0)


@pytest.fixture
def mock_device(aioclient_mock: AiohttpClientMocker) -> AiohttpClientMocker:
    """Mock a reachable OverSight device."""
    aioclient_mock.get(f"{BASE_URL}/info", json=envelope(INFO))
    aioclient_mock.get(f"{BASE_URL}/", json=envelope(LAYOUTS))
    return aioclient_mock


@pytest.fixture
def config_entry(hass: HomeAssistant) -> MockConfigEntry:
    """Return a config entry for the mocked device."""
    entry = MockConfigEntry(
        domain=DOMAIN,
        unique_id=DEVICE_ID,
        title=TITLE,
        data={CONF_HOST: HOST, CONF_PORT: PORT},
    )
    entry.add_to_hass(hass)
    return entry


@pytest.fixture
async def setup_integration(
    hass: HomeAssistant,
    config_entry: MockConfigEntry,
    mock_device: AiohttpClientMocker,
) -> MockConfigEntry:
    """Set up the integration with the mocked device."""
    assert await hass.config_entries.async_setup(config_entry.entry_id)
    await hass.async_block_till_done()
    mock_device.mock_calls.clear()
    return config_entry
