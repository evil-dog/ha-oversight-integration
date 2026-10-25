"""Tests for the OverSight config flow."""

from __future__ import annotations

from ipaddress import ip_address
from typing import TYPE_CHECKING
from unittest.mock import patch

import pytest
from homeassistant.config_entries import SOURCE_USER, SOURCE_ZEROCONF
from homeassistant.const import CONF_HOST, CONF_PORT
from homeassistant.data_entry_flow import FlowResultType
from homeassistant.helpers.service_info.zeroconf import ZeroconfServiceInfo

from custom_components.oversight_android_tv_notifications.const import DOMAIN

from .conftest import BASE_URL, DEVICE_ID, HOST, INFO, PORT, TITLE, envelope

if TYPE_CHECKING:
    from collections.abc import Generator

    from homeassistant.core import HomeAssistant
    from pytest_homeassistant_custom_component.common import MockConfigEntry
    from pytest_homeassistant_custom_component.test_util.aiohttp import (
        AiohttpClientMocker,
    )

NEW_HOST = "192.168.1.77"


@pytest.fixture(autouse=True)
def mock_setup_entry() -> Generator[None]:
    """Skip setting up the entry a flow creates; only the flow is under test."""
    with patch(
        "custom_components.oversight_android_tv_notifications.async_setup_entry",
        return_value=True,
    ):
        yield


def _discovery(host: str = NEW_HOST, device_id: str = DEVICE_ID) -> ZeroconfServiceInfo:
    """Return zeroconf discovery info for the device."""
    return ZeroconfServiceInfo(
        ip_address=ip_address(host),
        ip_addresses=[ip_address(host)],
        hostname="tv.local.",
        name=f"{TITLE}._tvoverlay._tcp.local.",
        port=PORT,
        type="_tvoverlay._tcp.local.",
        properties={"deviceId": device_id, "deviceName": TITLE},
    )


async def test_user_flow(
    hass: HomeAssistant, aioclient_mock: AiohttpClientMocker
) -> None:
    """A reachable device creates an entry named after the device."""
    aioclient_mock.get(f"{BASE_URL}/info", json=envelope(INFO))
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": SOURCE_USER}
    )
    assert result["type"] is FlowResultType.FORM

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"], {CONF_HOST: HOST, CONF_PORT: PORT}
    )
    assert result["type"] is FlowResultType.CREATE_ENTRY
    assert result["title"] == TITLE
    assert result["data"] == {CONF_HOST: HOST, CONF_PORT: PORT}
    assert result["result"].unique_id == DEVICE_ID


async def test_user_flow_connection_error(
    hass: HomeAssistant, aioclient_mock: AiohttpClientMocker
) -> None:
    """An unreachable device shows the connection error."""
    aioclient_mock.get(f"{BASE_URL}/info", exc=TimeoutError())
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": SOURCE_USER}
    )
    result = await hass.config_entries.flow.async_configure(
        result["flow_id"], {CONF_HOST: HOST, CONF_PORT: PORT}
    )
    assert result["type"] is FlowResultType.FORM
    assert result["errors"] == {"base": "connection"}


async def test_user_flow_unknown_error(
    hass: HomeAssistant, aioclient_mock: AiohttpClientMocker
) -> None:
    """A device error response shows the unknown error."""
    aioclient_mock.get(f"{BASE_URL}/info", json=envelope(None, success=False))
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": SOURCE_USER}
    )
    result = await hass.config_entries.flow.async_configure(
        result["flow_id"], {CONF_HOST: HOST, CONF_PORT: PORT}
    )
    assert result["type"] is FlowResultType.FORM
    assert result["errors"] == {"base": "unknown"}


async def test_user_flow_missing_device_id(
    hass: HomeAssistant, aioclient_mock: AiohttpClientMocker
) -> None:
    """A device that reports an empty ID is rejected instead of colliding."""
    aioclient_mock.get(f"{BASE_URL}/info", json=envelope({**INFO, "deviceId": ""}))
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": SOURCE_USER}
    )
    result = await hass.config_entries.flow.async_configure(
        result["flow_id"], {CONF_HOST: HOST, CONF_PORT: PORT}
    )
    assert result["type"] is FlowResultType.FORM
    assert result["errors"] == {"base": "missing_device_id"}


async def test_user_flow_already_configured(
    hass: HomeAssistant,
    config_entry: MockConfigEntry,
    aioclient_mock: AiohttpClientMocker,
) -> None:
    """Adding the same device twice aborts."""
    aioclient_mock.get(f"{BASE_URL}/info", json=envelope(INFO))
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": SOURCE_USER}
    )
    result = await hass.config_entries.flow.async_configure(
        result["flow_id"], {CONF_HOST: HOST, CONF_PORT: PORT}
    )
    assert result["type"] is FlowResultType.ABORT
    assert result["reason"] == "already_configured"


async def test_zeroconf_flow(hass: HomeAssistant) -> None:
    """A discovered device is added after confirmation."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": SOURCE_ZEROCONF}, data=_discovery()
    )
    assert result["type"] is FlowResultType.FORM
    assert result["step_id"] == "zeroconf_confirm"

    result = await hass.config_entries.flow.async_configure(result["flow_id"], {})
    assert result["type"] is FlowResultType.CREATE_ENTRY
    assert result["title"] == TITLE
    assert result["data"] == {CONF_HOST: NEW_HOST, CONF_PORT: PORT}


async def test_zeroconf_updates_host(
    hass: HomeAssistant, config_entry: MockConfigEntry
) -> None:
    """Rediscovering a configured device at a new address updates the entry."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": SOURCE_ZEROCONF}, data=_discovery()
    )
    assert result["type"] is FlowResultType.ABORT
    assert result["reason"] == "already_configured"
    assert config_entry.data[CONF_HOST] == NEW_HOST


async def test_zeroconf_missing_device_id(
    hass: HomeAssistant, aioclient_mock: AiohttpClientMocker
) -> None:
    """Discovery aborts if neither TXT records nor /info give a device ID."""
    aioclient_mock.get(
        f"http://{NEW_HOST}:{PORT}/info", json=envelope({**INFO, "deviceId": ""})
    )
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": SOURCE_ZEROCONF}, data=_discovery(device_id="")
    )
    assert result["type"] is FlowResultType.ABORT
    assert result["reason"] == "missing_device_id"
