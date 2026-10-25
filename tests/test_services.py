"""Tests for the OverSight actions and the notify entity."""

from __future__ import annotations

from typing import TYPE_CHECKING

import pytest
from homeassistant.const import ATTR_DEVICE_ID, ATTR_ENTITY_ID, CONF_HOST, CONF_PORT
from homeassistant.exceptions import HomeAssistantError
from homeassistant.helpers import device_registry as dr
from pytest_homeassistant_custom_component.common import MockConfigEntry

from custom_components.oversight_android_tv_notifications.const import DOMAIN

from .conftest import BASE_URL, INFO, LAYOUTS, PORT, envelope

if TYPE_CHECKING:
    from homeassistant.core import HomeAssistant
    from pytest_homeassistant_custom_component.test_util.aiohttp import (
        AiohttpClientMocker,
    )

NOTIFY_ENTITY = "notify.living_room_tv_notifications"
HOST_2 = "192.168.1.60"
BASE_URL_2 = f"http://{HOST_2}:{PORT}"


def _posts(aioclient_mock: AiohttpClientMocker) -> list[tuple[str, dict]]:
    """Return (url, body) for each POST made."""
    return [(str(u), d) for m, u, d, _ in aioclient_mock.mock_calls if m == "post"]


async def test_notify_send_message(
    hass: HomeAssistant,
    setup_integration: MockConfigEntry,
    aioclient_mock: AiohttpClientMocker,
) -> None:
    """notify.send_message sends the message and title."""
    aioclient_mock.post(f"{BASE_URL}/notify", json=envelope())
    await hass.services.async_call(
        "notify",
        "send_message",
        {ATTR_ENTITY_ID: NOTIFY_ENTITY, "message": "Hello", "title": "Hi"},
        blocking=True,
    )
    assert _posts(aioclient_mock) == [
        (f"{BASE_URL}/notify", {"message": "Hello", "title": "Hi"})
    ]


async def test_send_notification_camel_cases_fields(
    hass: HomeAssistant,
    setup_integration: MockConfigEntry,
    aioclient_mock: AiohttpClientMocker,
) -> None:
    """Action fields are sent with the API's camelCase names."""
    aioclient_mock.post(f"{BASE_URL}/notify", json=envelope())
    await hass.services.async_call(
        DOMAIN,
        "send_notification",
        {
            ATTR_ENTITY_ID: NOTIFY_ENTITY,
            "message": "Motion",
            "id": "door",
            "small_icon": "mdi:bell",
            "small_icon_color": "#FF5733",
            "duration": 5,
        },
        blocking=True,
    )
    assert _posts(aioclient_mock) == [
        (
            f"{BASE_URL}/notify",
            {
                "message": "Motion",
                "id": "door",
                "smallIcon": "mdi:bell",
                "smallIconColor": "#FF5733",
                "duration": 5,
            },
        )
    ]


async def test_device_target_reaches_every_device(
    hass: HomeAssistant,
    setup_integration: MockConfigEntry,
    aioclient_mock: AiohttpClientMocker,
    device_registry: dr.DeviceRegistry,
) -> None:
    """Targeting devices calls each targeted device, not just the first one."""
    aioclient_mock.get(
        f"{BASE_URL_2}/info", json=envelope({**INFO, "deviceId": "device-2"})
    )
    aioclient_mock.get(f"{BASE_URL_2}/", json=envelope(LAYOUTS))
    second = MockConfigEntry(
        domain=DOMAIN,
        unique_id="device-2",
        title="Bedroom TV",
        data={CONF_HOST: HOST_2, CONF_PORT: PORT},
    )
    second.add_to_hass(hass)
    assert await hass.config_entries.async_setup(second.entry_id)
    await hass.async_block_till_done()

    aioclient_mock.post(f"{BASE_URL}/screen_on", json=envelope())
    aioclient_mock.post(f"{BASE_URL_2}/screen_on", json=envelope())
    device_ids = [
        device.id
        for entry in (setup_integration, second)
        for device in dr.async_entries_for_config_entry(device_registry, entry.entry_id)
    ]
    assert len(device_ids) == 2
    await hass.services.async_call(
        DOMAIN, "screen_on", {ATTR_DEVICE_ID: device_ids}, blocking=True
    )

    assert sorted(url for url, _ in _posts(aioclient_mock)) == [
        f"{BASE_URL}/screen_on",
        f"{BASE_URL_2}/screen_on",
    ]


async def test_set_clock_appearance_keeps_other_fields(
    hass: HomeAssistant,
    setup_integration: MockConfigEntry,
    aioclient_mock: AiohttpClientMocker,
) -> None:
    """Fields not given keep their current values instead of resetting."""
    current = {
        "fontSize": 12,
        "fontWeight": "Normal",
        "color": "#FFFFFF",
        "displayShadow": True,
        "backgroundColor": "#000000",
    }
    aioclient_mock.get(f"{BASE_URL}/overlay_customization", json=envelope(current))
    aioclient_mock.post(f"{BASE_URL}/overlay_customization", json=envelope(current))

    await hass.services.async_call(
        DOMAIN,
        "set_clock_appearance",
        {ATTR_ENTITY_ID: NOTIFY_ENTITY, "font_size": 20, "font_weight": "bold"},
        blocking=True,
    )

    assert _posts(aioclient_mock) == [
        (
            f"{BASE_URL}/overlay_customization",
            {**current, "fontSize": 20, "fontWeight": "bold"},
        )
    ]


async def test_action_reports_device_error(
    hass: HomeAssistant,
    setup_integration: MockConfigEntry,
    aioclient_mock: AiohttpClientMocker,
) -> None:
    """A rejected action raises HomeAssistantError with the device's message."""
    aioclient_mock.post(
        f"{BASE_URL}/notify_fixed",
        status=400,
        json={
            "success": False,
            "message": "New fixed notification requires icon or text",
            "result": None,
        },
    )
    with pytest.raises(HomeAssistantError, match="requires icon or text"):
        await hass.services.async_call(
            DOMAIN,
            "send_fixed_notification",
            {ATTR_ENTITY_ID: NOTIFY_ENTITY, "id": "new"},
            blocking=True,
        )
