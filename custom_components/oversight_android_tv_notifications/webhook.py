"""
Webhook the device calls to announce its address.

Integration side of address tracking across subnets, where mDNS can't reach
Home Assistant: the integration pushes this webhook's URL to the device, and
the device posts its deviceId, host and port to it on startup and whenever its
network changes. A new address is checked against the device before the entry
is updated, so a stray post can't point the entry at another host.
"""

from __future__ import annotations

import asyncio
import ipaddress
import secrets
from http import HTTPStatus
from typing import TYPE_CHECKING, Any

from aiohttp import web
from homeassistant.components import webhook
from homeassistant.components.network import async_get_source_ip
from homeassistant.const import CONF_HOST, CONF_PORT, CONF_WEBHOOK_ID
from homeassistant.core import callback
from homeassistant.exceptions import HomeAssistantError
from homeassistant.helpers.aiohttp_client import async_get_clientsession

from .api import OversightApiClient, OversightApiClientError
from .const import DOMAIN, LOGGER, WEBHOOK_ID_PREFIX

if TYPE_CHECKING:
    from homeassistant.config_entries import ConfigEntry
    from homeassistant.core import HomeAssistant

MAX_PORT = 65535


@callback
def async_ensure_webhook_id(hass: HomeAssistant, entry: ConfigEntry) -> str:
    """Return the entry's webhook ID, creating one for entries that predate it."""
    if webhook_id := entry.data.get(CONF_WEBHOOK_ID):
        return webhook_id
    webhook_id = f"{WEBHOOK_ID_PREFIX}{secrets.token_hex(16)}"
    hass.config_entries.async_update_entry(
        entry, data={**entry.data, CONF_WEBHOOK_ID: webhook_id}
    )
    return webhook_id


@callback
def async_register_webhook(hass: HomeAssistant, entry: ConfigEntry) -> None:
    """
    Register the entry's webhook if it isn't already.

    It stays registered while setup retries (the device may be unreachable
    precisely because it moved), so it is only removed on unload or removal.
    """

    async def handle(
        hass: HomeAssistant,
        webhook_id: str,  # noqa: ARG001
        request: web.Request,
    ) -> web.Response:
        return await _async_handle_announce(hass, entry, request)

    try:
        webhook.async_register(
            hass,
            DOMAIN,
            entry.title,
            entry.data[CONF_WEBHOOK_ID],
            handle,
            local_only=True,
            allowed_methods=["POST"],
        )
    except ValueError:
        LOGGER.debug("Webhook for %s is already registered", entry.title)


@callback
def async_unregister_webhook(hass: HomeAssistant, entry: ConfigEntry) -> None:
    """Remove the entry's webhook."""
    if webhook_id := entry.data.get(CONF_WEBHOOK_ID):
        webhook.async_unregister(hass, webhook_id)


async def async_get_webhook_url(hass: HomeAssistant, entry: ConfigEntry) -> str | None:
    """
    Return the webhook URL the device should call.

    Uses Home Assistant's own address on the interface that reaches the
    device, so it bypasses any reverse proxy and its authentication.
    """
    try:
        source_ip = await async_get_source_ip(hass, target_ip=entry.data[CONF_HOST])
    except HomeAssistantError:
        return None
    api = hass.config.api
    if source_ip is None or api is None:
        return None
    host = f"[{source_ip}]" if ":" in source_ip else source_ip
    scheme = "https" if api.use_ssl else "http"
    path = webhook.async_generate_path(entry.data[CONF_WEBHOOK_ID])
    return f"{scheme}://{host}:{api.port}{path}"


async def _async_handle_announce(
    hass: HomeAssistant,
    entry: ConfigEntry,
    request: web.Request,
) -> web.Response:
    """Update the entry when the device announces a new address."""
    if (address := await _async_parse_announcement(entry, request)) is None:
        return web.Response(status=HTTPStatus.BAD_REQUEST)
    host, port = address

    if port == entry.data[CONF_PORT] and await _async_same_host(
        entry.data[CONF_HOST], host
    ):
        return web.Response(status=HTTPStatus.OK)

    client = OversightApiClient(
        host=host, port=port, session=async_get_clientsession(hass)
    )
    try:
        info = await client.async_get_info()
    except OversightApiClientError as err:
        LOGGER.debug("Announced address %s:%s is not reachable: %s", host, port, err)
        # The device retries, by which time it may be reachable
        return web.Response(status=HTTPStatus.SERVICE_UNAVAILABLE)
    if info.get("deviceId") != entry.unique_id:
        LOGGER.warning(
            "Ignoring announced address %s:%s for %s: another device answers there",
            host,
            port,
            entry.title,
        )
        return web.Response(status=HTTPStatus.BAD_REQUEST)

    LOGGER.info(
        "%s moved from %s:%s to %s:%s",
        entry.title,
        entry.data[CONF_HOST],
        entry.data[CONF_PORT],
        host,
        port,
    )
    hass.config_entries.async_update_entry(
        entry, data={**entry.data, CONF_HOST: host, CONF_PORT: port}
    )
    hass.config_entries.async_schedule_reload(entry.entry_id)
    return web.Response(status=HTTPStatus.OK)


async def _async_parse_announcement(
    entry: ConfigEntry, request: web.Request
) -> tuple[str, int] | None:
    """Return the announced (host, port), or None if the post is invalid."""
    try:
        data: Any = await request.json()
    except ValueError:
        return None
    if not isinstance(data, dict) or data.get("deviceId") != entry.unique_id:
        return None
    host = data.get("host") or request.remote
    port = data.get("port", entry.data[CONF_PORT])
    if not _valid_host(host) or not _valid_port(port):
        return None
    return host, port


async def _async_same_host(configured: str, announced: str) -> bool:
    """
    Return whether the configured host already points at the announced IP.

    A configured hostname that still resolves to the device is kept rather
    than replaced with a bare IP.
    """
    if configured == announced:
        return True
    if _valid_host(configured):
        return False
    try:
        infos = await asyncio.get_running_loop().getaddrinfo(configured, None)
    except OSError:
        return False
    return any(info[4][0] == announced for info in infos)


def _valid_host(host: Any) -> bool:
    """Return whether host is an IP address (the device always sends one)."""
    if not isinstance(host, str):
        return False
    try:
        ipaddress.ip_address(host)
    except ValueError:
        return False
    return True


def _valid_port(port: Any) -> bool:
    """Return whether port is a usable TCP port."""
    return isinstance(port, int) and not isinstance(port, bool) and 0 < port <= MAX_PORT
