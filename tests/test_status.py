"""Tests for the device status report and badge removal, on new and old apps."""

from __future__ import annotations

import copy
from typing import TYPE_CHECKING

import pytest
from homeassistant.const import ATTR_ENTITY_ID, STATE_OFF, STATE_ON, STATE_UNAVAILABLE
from homeassistant.exceptions import HomeAssistantError
from homeassistant.helpers import device_registry as dr

from custom_components.oversight_android_tv_notifications.const import DOMAIN
from custom_components.oversight_android_tv_notifications.coordinator import (
    format_app_version,
)

from .conftest import BASE_URL, INFO, LAYOUTS, envelope

if TYPE_CHECKING:
    from homeassistant.core import HomeAssistant
    from pytest_homeassistant_custom_component.common import MockConfigEntry
    from pytest_homeassistant_custom_component.test_util.aiohttp import (
        AiohttpClientMocker,
    )

NOTIFY_ENTITY = "notify.living_room_tv_notifications"


def _device(
    device_registry: dr.DeviceRegistry, entry: MockConfigEntry
) -> dr.DeviceEntry:
    """Return the single device of a config entry."""
    (device,) = dr.async_entries_for_config_entry(device_registry, entry.entry_id)
    return device


@pytest.fixture
async def setup_old_app(
    hass: HomeAssistant,
    config_entry: MockConfigEntry,
    aioclient_mock: AiohttpClientMocker,
) -> MockConfigEntry:
    """Set up against an app from before status and DELETE were added."""
    info = copy.deepcopy(INFO)
    info["status"] = None
    aioclient_mock.get(f"{BASE_URL}/info", json=envelope(info))
    aioclient_mock.get(f"{BASE_URL}/", json=envelope(LAYOUTS))
    assert await hass.config_entries.async_setup(config_entry.entry_id)
    await hass.async_block_till_done()
    aioclient_mock.mock_calls.clear()
    return config_entry


@pytest.mark.parametrize(
    ("version", "expected"),
    [(302, "0.3.2"), (10203, "1.2.3"), (1, "development build"), (None, None)],
)
def test_format_app_version(version: int | None, expected: str | None) -> None:
    """The versionCode is shown as major.minor.patch."""
    assert format_app_version(version) == expected


async def test_status_sensors(
    hass: HomeAssistant, setup_integration: MockConfigEntry
) -> None:
    """Screen state and the two problem sensors come from the status report."""
    assert hass.states.get("binary_sensor.living_room_tv_screen").state == STATE_ON
    # Permission granted: no problem
    assert (
        hass.states.get("binary_sensor.living_room_tv_overlay_permission").state
        == STATE_OFF
    )
    # Not exempt from battery optimization: problem
    assert (
        hass.states.get("binary_sensor.living_room_tv_battery_optimization").state
        == STATE_ON
    )


async def test_sw_version_tracks_app_updates(
    hass: HomeAssistant,
    setup_integration: MockConfigEntry,
    aioclient_mock: AiohttpClientMocker,
    device_registry: dr.DeviceRegistry,
) -> None:
    """The device page shows the app version and follows updates."""
    assert _device(device_registry, setup_integration).sw_version == "0.3.2"

    info = copy.deepcopy(INFO)
    info["status"]["version"] = 400
    aioclient_mock.clear_requests()
    aioclient_mock.get(f"{BASE_URL}/info", json=envelope(info))
    aioclient_mock.get(f"{BASE_URL}/", json=envelope(LAYOUTS))
    await setup_integration.runtime_data.coordinator.async_refresh()
    await hass.async_block_till_done()

    assert _device(device_registry, setup_integration).sw_version == "0.4.0"


async def test_remove_uses_delete(
    hass: HomeAssistant,
    setup_integration: MockConfigEntry,
    aioclient_mock: AiohttpClientMocker,
) -> None:
    """Apps that report status get a real delete, with the id URL-encoded."""
    aioclient_mock.delete(f"{BASE_URL}/notify_fixed/a%2Fb", json=envelope())
    await hass.services.async_call(
        DOMAIN,
        "remove_fixed_notification",
        {ATTR_ENTITY_ID: NOTIFY_ENTITY, "id": "a/b"},
        blocking=True,
    )
    assert [(m, str(u)) for m, u, _, _ in aioclient_mock.mock_calls] == [
        ("delete", f"{BASE_URL}/notify_fixed/a%2Fb")
    ]


async def test_remove_missing_badge_is_not_an_error(
    hass: HomeAssistant,
    setup_integration: MockConfigEntry,
    aioclient_mock: AiohttpClientMocker,
) -> None:
    """Removing a badge that is already gone succeeds."""
    aioclient_mock.delete(
        f"{BASE_URL}/notify_fixed/gone",
        status=404,
        json={
            "success": False,
            "message": "No fixed notification with id 'gone'",
            "result": None,
        },
    )
    await hass.services.async_call(
        DOMAIN,
        "remove_fixed_notification",
        {ATTR_ENTITY_ID: NOTIFY_ENTITY, "id": "gone"},
        blocking=True,
    )


async def test_remove_reports_other_errors(
    hass: HomeAssistant,
    setup_integration: MockConfigEntry,
    aioclient_mock: AiohttpClientMocker,
) -> None:
    """Errors other than not found are still reported."""
    aioclient_mock.delete(
        f"{BASE_URL}/notify_fixed/x",
        status=500,
        json={"success": False, "message": "Internal server error", "result": None},
    )
    with pytest.raises(HomeAssistantError, match="Internal server error"):
        await hass.services.async_call(
            DOMAIN,
            "remove_fixed_notification",
            {ATTR_ENTITY_ID: NOTIFY_ENTITY, "id": "x"},
            blocking=True,
        )


async def test_old_app_status_sensors_unavailable(
    hass: HomeAssistant,
    setup_old_app: MockConfigEntry,
    device_registry: dr.DeviceRegistry,
) -> None:
    """Without a status report the status sensors are unavailable."""
    for sensor in ("screen", "overlay_permission", "battery_optimization"):
        state = hass.states.get(f"binary_sensor.living_room_tv_{sensor}")
        assert state.state == STATE_UNAVAILABLE
    assert (
        hass.states.get("binary_sensor.living_room_tv_connectivity").state == STATE_ON
    )
    assert _device(device_registry, setup_old_app).sw_version is None


async def test_old_app_remove_falls_back_to_expiry(
    hass: HomeAssistant,
    setup_old_app: MockConfigEntry,
    aioclient_mock: AiohttpClientMocker,
) -> None:
    """Older apps have no delete, so the badge is hidden and expired instead."""
    aioclient_mock.post(f"{BASE_URL}/notify_fixed", json=envelope())
    await hass.services.async_call(
        DOMAIN,
        "remove_fixed_notification",
        {ATTR_ENTITY_ID: NOTIFY_ENTITY, "id": "weather"},
        blocking=True,
    )
    assert [(m, str(u), d) for m, u, d, _ in aioclient_mock.mock_calls] == [
        (
            "post",
            f"{BASE_URL}/notify_fixed",
            {"id": "weather", "visible": False, "expiration": "1s"},
        )
    ]
