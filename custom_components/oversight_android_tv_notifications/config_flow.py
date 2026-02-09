"""Config flow for OverSight Android TV."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

import voluptuous as vol
from homeassistant import config_entries
from homeassistant.helpers import selector
from homeassistant.helpers.aiohttp_client import async_create_clientsession

if TYPE_CHECKING:
    from homeassistant.components.zeroconf import ZeroconfServiceInfo

from .api import (
    OversightApiClient,
    OversightApiClientCommunicationError,
    OversightApiClientError,
)
from .const import CONF_HOST, CONF_PORT, DEFAULT_PORT, DOMAIN, LOGGER


class OversightConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Config flow for OverSight Android TV."""

    VERSION = 1

    def __init__(self) -> None:
        """Initialize the config flow."""
        self._discovered_host: str | None = None
        self._discovered_port: int | None = None
        self._discovered_name: str | None = None
        self._discovered_device_id: str | None = None

    async def async_step_user(
        self,
        user_input: dict[str, Any] | None = None,
    ) -> config_entries.ConfigFlowResult:
        """Handle manual configuration via host/port."""
        errors: dict[str, str] = {}

        if user_input is not None:
            host = user_input[CONF_HOST]
            port = user_input[CONF_PORT]
            try:
                info = await self._test_connection(host, port)
            except OversightApiClientCommunicationError:
                errors["base"] = "connection"
            except OversightApiClientError:
                errors["base"] = "unknown"
            else:
                device_id = info.get("deviceId", "")
                device_name = (info.get("settings") or {}).get(
                    "deviceName", "OverSight Device"
                )
                await self.async_set_unique_id(device_id)
                self._abort_if_unique_id_configured()
                return self.async_create_entry(
                    title=device_name,
                    data={
                        CONF_HOST: host,
                        CONF_PORT: int(port),
                    },
                )

        return self.async_show_form(
            step_id="user",
            data_schema=vol.Schema(
                {
                    vol.Required(
                        CONF_HOST,
                        default=(user_input or {}).get(CONF_HOST, vol.UNDEFINED),
                    ): selector.TextSelector(
                        selector.TextSelectorConfig(
                            type=selector.TextSelectorType.TEXT,
                        ),
                    ),
                    vol.Required(
                        CONF_PORT,
                        default=(user_input or {}).get(CONF_PORT, DEFAULT_PORT),
                    ): selector.NumberSelector(
                        selector.NumberSelectorConfig(
                            min=1,
                            max=65535,
                            mode=selector.NumberSelectorMode.BOX,
                        ),
                    ),
                },
            ),
            errors=errors,
        )

    async def async_step_zeroconf(
        self,
        discovery_info: ZeroconfServiceInfo,
    ) -> config_entries.ConfigFlowResult:
        """Handle zeroconf discovery of an OverSight device."""
        host = str(discovery_info.host)
        port = discovery_info.port or DEFAULT_PORT

        # Extract device info from mDNS TXT records
        properties = discovery_info.properties or {}
        device_id = properties.get("deviceId", "")
        device_name = properties.get("deviceName", discovery_info.name or "OverSight Device")

        if not device_id:
            # Try to get deviceId from the API if not in TXT records
            try:
                info = await self._test_connection(host, port)
                device_id = info.get("deviceId", "")
                device_name = (info.get("settings") or {}).get(
                    "deviceName", device_name
                )
            except OversightApiClientError:
                return self.async_abort(reason="connection")

        if not device_id:
            return self.async_abort(reason="unknown")

        await self.async_set_unique_id(device_id)
        self._abort_if_unique_id_configured(
            updates={CONF_HOST: host, CONF_PORT: port}
        )

        self._discovered_host = host
        self._discovered_port = port
        self._discovered_name = device_name
        self._discovered_device_id = device_id

        self.context["title_placeholders"] = {"name": device_name}
        return await self.async_step_zeroconf_confirm()

    async def async_step_zeroconf_confirm(
        self,
        user_input: dict[str, Any] | None = None,
    ) -> config_entries.ConfigFlowResult:
        """Confirm zeroconf discovery."""
        if user_input is not None:
            return self.async_create_entry(
                title=self._discovered_name or "OverSight Device",
                data={
                    CONF_HOST: self._discovered_host,
                    CONF_PORT: self._discovered_port,
                },
            )

        return self.async_show_form(
            step_id="zeroconf_confirm",
            description_placeholders={"name": self._discovered_name},
        )

    async def _test_connection(
        self, host: str, port: int
    ) -> dict[str, Any]:
        """Test connection to an OverSight device and return info."""
        client = OversightApiClient(
            host=host,
            port=int(port),
            session=async_create_clientsession(self.hass),
        )
        return await client.async_get_info()
