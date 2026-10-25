"""Tests for setting up the OverSight integration and its entities."""

from __future__ import annotations

from typing import TYPE_CHECKING

import pytest
from homeassistant.config_entries import ConfigEntryState
from homeassistant.const import ATTR_ENTITY_ID, STATE_OFF, STATE_ON
from homeassistant.exceptions import HomeAssistantError

from custom_components.oversight_android_tv_notifications.diagnostics import (
    async_get_config_entry_diagnostics,
)

from .conftest import BASE_URL, PORT, envelope, info_without_device_id

if TYPE_CHECKING:
    from homeassistant.core import HomeAssistant
    from pytest_homeassistant_custom_component.common import MockConfigEntry
    from pytest_homeassistant_custom_component.test_util.aiohttp import (
        AiohttpClientMocker,
    )


async def test_setup_and_unload(
    hass: HomeAssistant, setup_integration: MockConfigEntry
) -> None:
    """The entry loads, exposes the device state, and unloads."""
    assert setup_integration.state is ConfigEntryState.LOADED

    assert (
        hass.states.get("binary_sensor.living_room_tv_connectivity").state == STATE_ON
    )
    assert hass.states.get("number.living_room_tv_overlay_visibility").state == "20"
    # A stored 0 must not be replaced by the default of 100
    assert (
        hass.states.get("number.living_room_tv_fixed_notifications_visibility").state
        == "0"
    )
    assert hass.states.get("select.living_room_tv_hot_corner").state == "bottom_start"
    assert hass.states.get("switch.living_room_tv_pixel_shift").state == STATE_ON
    assert hass.states.get("text.living_room_tv_device_name").state == "Living Room TV"
    # Debug display is disabled by default
    assert hass.states.get("switch.living_room_tv_display_debug_info") is None

    layout = hass.states.get("select.living_room_tv_notification_layout")
    # No explicit layout name, so the layout list's selection applies
    assert layout.state == "Minimalist"
    assert layout.attributes["options"] == ["Default", "Minimalist", "Only Icon"]

    assert await hass.config_entries.async_unload(setup_integration.entry_id)
    assert setup_integration.state is ConfigEntryState.NOT_LOADED


async def test_setup_retries_when_unreachable(
    hass: HomeAssistant,
    config_entry: MockConfigEntry,
    aioclient_mock: AiohttpClientMocker,
) -> None:
    """An unreachable device puts the entry into setup retry."""
    aioclient_mock.get(f"{BASE_URL}/info", exc=TimeoutError())
    await hass.config_entries.async_setup(config_entry.entry_id)
    assert config_entry.state is ConfigEntryState.SETUP_RETRY


async def test_connectivity_off_when_unreachable(
    hass: HomeAssistant,
    setup_integration: MockConfigEntry,
    aioclient_mock: AiohttpClientMocker,
) -> None:
    """The connectivity sensor reports off, not unavailable, after a failed poll."""
    aioclient_mock.clear_requests()
    aioclient_mock.get(f"{BASE_URL}/info", exc=TimeoutError())
    await setup_integration.runtime_data.coordinator.async_refresh()
    await hass.async_block_till_done()

    assert (
        hass.states.get("binary_sensor.living_room_tv_connectivity").state == STATE_OFF
    )


async def test_setting_applies_response_immediately(
    hass: HomeAssistant,
    setup_integration: MockConfigEntry,
    aioclient_mock: AiohttpClientMocker,
) -> None:
    """Changing a setting uses the state the device returns, without a poll."""
    info = info_without_device_id()
    info["settings"]["pixelShift"] = False
    aioclient_mock.post(f"{BASE_URL}/set/settings", json=envelope(info))

    await hass.services.async_call(
        "switch",
        "turn_off",
        {ATTR_ENTITY_ID: "switch.living_room_tv_pixel_shift"},
        blocking=True,
    )

    assert [(m, str(u), d) for m, u, d, _ in aioclient_mock.mock_calls] == [
        ("post", f"{BASE_URL}/set/settings", {"pixelShift": False})
    ]
    assert hass.states.get("switch.living_room_tv_pixel_shift").state == STATE_OFF


async def test_select_layout(
    hass: HomeAssistant,
    setup_integration: MockConfigEntry,
    aioclient_mock: AiohttpClientMocker,
) -> None:
    """Selecting a layout sets it as the notification layout name."""
    info = info_without_device_id()
    info["notifications"]["notificationLayoutName"] = "Only Icon"
    aioclient_mock.post(f"{BASE_URL}/set/notifications", json=envelope(info))

    await hass.services.async_call(
        "select",
        "select_option",
        {
            ATTR_ENTITY_ID: "select.living_room_tv_notification_layout",
            "option": "Only Icon",
        },
        blocking=True,
    )

    assert aioclient_mock.mock_calls[-1][2] == {"notificationLayoutName": "Only Icon"}
    assert hass.states.get("select.living_room_tv_notification_layout").state == (
        "Only Icon"
    )


async def test_device_error_raises_homeassistant_error(
    hass: HomeAssistant,
    setup_integration: MockConfigEntry,
    aioclient_mock: AiohttpClientMocker,
) -> None:
    """A rejected setting is reported with the device's message."""
    aioclient_mock.post(
        f"{BASE_URL}/set/settings",
        status=400,
        json={
            "success": False,
            "message": "remotePort must be between",
            "result": None,
        },
    )
    with pytest.raises(HomeAssistantError, match="remotePort must be between"):
        await hass.services.async_call(
            "text",
            "set_value",
            {ATTR_ENTITY_ID: "text.living_room_tv_device_name", "value": "x"},
            blocking=True,
        )


async def test_restart_button(
    hass: HomeAssistant,
    setup_integration: MockConfigEntry,
    aioclient_mock: AiohttpClientMocker,
) -> None:
    """The restart button restarts the overlay service."""
    aioclient_mock.post(f"{BASE_URL}/restart_service", json=envelope())
    await hass.services.async_call(
        "button",
        "press",
        {ATTR_ENTITY_ID: "button.living_room_tv_restart_overlay_service"},
        blocking=True,
    )
    assert str(aioclient_mock.mock_calls[-1][1]) == f"{BASE_URL}/restart_service"


async def test_diagnostics_redacts_host(
    hass: HomeAssistant, setup_integration: MockConfigEntry
) -> None:
    """Diagnostics include the state but not the device address."""
    diagnostics = await async_get_config_entry_diagnostics(hass, setup_integration)
    assert diagnostics["entry"] == {"host": "**REDACTED**", "port": PORT}
    assert diagnostics["state"]["fixed_notifications_visibility"] == 0


@pytest.mark.parametrize(
    ("domain", "service", "data", "endpoint", "body"),
    [
        (
            "number",
            "set_value",
            {ATTR_ENTITY_ID: "number.living_room_tv_overlay_visibility", "value": 35},
            "set/overlay",
            {"overlayVisibility": 35},
        ),
        (
            "select",
            "select_option",
            {ATTR_ENTITY_ID: "select.living_room_tv_hot_corner", "option": "top_end"},
            "set/overlay",
            {"hotCorner": "top_end"},
        ),
        (
            "switch",
            "turn_on",
            {ATTR_ENTITY_ID: "switch.living_room_tv_display_notifications"},
            "set/notifications",
            {"displayNotifications": True},
        ),
    ],
)
async def test_setting_sends_api_field(
    hass: HomeAssistant,
    setup_integration: MockConfigEntry,
    aioclient_mock: AiohttpClientMocker,
    domain: str,
    service: str,
    data: dict,
    endpoint: str,
    body: dict,
) -> None:
    """Each setting entity posts its API field to the right endpoint."""
    aioclient_mock.post(
        f"{BASE_URL}/{endpoint}", json=envelope(info_without_device_id())
    )
    await hass.services.async_call(domain, service, data, blocking=True)
    assert [(str(u), d) for _, u, d, _ in aioclient_mock.mock_calls] == [
        (f"{BASE_URL}/{endpoint}", body)
    ]
