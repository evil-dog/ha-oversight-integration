"""OverSight Android TV integration for Home Assistant."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

import voluptuous as vol
from homeassistant.const import Platform
from homeassistant.core import ServiceCall, SupportsResponse
from homeassistant.helpers import entity_registry as er
from homeassistant.helpers.aiohttp_client import async_get_clientsession

from .api import OversightApiClient
from .const import CONF_HOST, CONF_PORT, DOMAIN, LOGGER
from .coordinator import OversightDataUpdateCoordinator
from .data import OversightData

if TYPE_CHECKING:
    from homeassistant.core import HomeAssistant

    from .data import OversightConfigEntry

PLATFORMS: list[Platform] = [
    Platform.BINARY_SENSOR,
    Platform.NOTIFY,
    Platform.NUMBER,
    Platform.SELECT,
    Platform.SWITCH,
]


async def async_setup_entry(
    hass: HomeAssistant,
    entry: OversightConfigEntry,
) -> bool:
    """Set up OverSight Android TV from a config entry."""
    client = OversightApiClient(
        host=entry.data[CONF_HOST],
        port=int(entry.data[CONF_PORT]),
        session=async_get_clientsession(hass),
    )

    coordinator = OversightDataUpdateCoordinator(
        hass=hass,
        logger=LOGGER,
        name=f"{DOMAIN}_{entry.unique_id}",
        client=client,
    )

    await coordinator.async_config_entry_first_refresh()

    entry.runtime_data = OversightData(
        client=client,
        coordinator=coordinator,
    )

    # Store entry data for service lookups
    hass.data.setdefault(DOMAIN, {})
    hass.data[DOMAIN][entry.entry_id] = entry.runtime_data

    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    entry.async_on_unload(entry.add_update_listener(async_reload_entry))

    # Register services once (first entry)
    if not hass.services.has_service(DOMAIN, "send_fixed_notification"):
        _register_services(hass)

    return True


async def async_unload_entry(
    hass: HomeAssistant,
    entry: OversightConfigEntry,
) -> bool:
    """Handle removal of an entry."""
    result = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
    if result:
        hass.data[DOMAIN].pop(entry.entry_id, None)
        if not hass.data[DOMAIN]:
            hass.data.pop(DOMAIN, None)
    return result


async def async_reload_entry(
    hass: HomeAssistant,
    entry: OversightConfigEntry,
) -> None:
    """Reload config entry."""
    await hass.config_entries.async_reload(entry.entry_id)


def _get_client_for_entity(
    hass: HomeAssistant, entity_id: str
) -> OversightApiClient | None:
    """Resolve an entity_id to its OversightApiClient."""
    ent_reg = er.async_get(hass)
    entry = ent_reg.async_get(entity_id)
    if entry is None or entry.config_entry_id is None:
        return None
    data = hass.data.get(DOMAIN, {}).get(entry.config_entry_id)
    if data is None:
        return None
    return data.client


def _get_client_from_call(
    hass: HomeAssistant, call: ServiceCall
) -> OversightApiClient:
    """Get a client from a service call's entity target."""
    entity_ids = call.data.get("entity_id", [])
    if isinstance(entity_ids, str):
        entity_ids = [entity_ids]

    # Try entity targeting first
    for eid in entity_ids:
        client = _get_client_for_entity(hass, eid)
        if client is not None:
            return client

    # Fallback: use first available entry
    entries = hass.data.get(DOMAIN, {})
    if entries:
        first = next(iter(entries.values()))
        return first.client

    msg = "No OverSight devices configured"
    raise ValueError(msg)


def _register_services(hass: HomeAssistant) -> None:
    """Register custom services for OverSight."""

    async def handle_send_fixed_notification(call: ServiceCall) -> None:
        """Handle the send_fixed_notification service call."""
        client = _get_client_from_call(hass, call)
        data: dict[str, Any] = {"id": call.data["id"]}
        for field in (
            "icon",
            "text",
            "icon_color",
            "message_color",
            "background_color",
            "border_color",
            "shape",
            "size",
            "expiration",
            "show_duration",
            "collapse_duration",
            "repeat_expand",
        ):
            if field in call.data:
                # Convert snake_case to camelCase for the API
                camel = _to_camel_case(field)
                data[camel] = call.data[field]
        await client.async_send_fixed_notification(data)

    async def handle_remove_fixed_notification(call: ServiceCall) -> None:
        """Handle the remove_fixed_notification service call."""
        client = _get_client_from_call(hass, call)
        await client.async_send_fixed_notification(
            {"id": call.data["id"], "visible": False}
        )

    async def handle_screen_on(call: ServiceCall) -> None:
        """Handle the screen_on service call."""
        client = _get_client_from_call(hass, call)
        await client.async_screen_on()

    hass.services.async_register(
        DOMAIN,
        "send_fixed_notification",
        handle_send_fixed_notification,
        schema=vol.Schema(
            {
                vol.Required("id"): str,
                vol.Optional("icon"): str,
                vol.Optional("text"): str,
                vol.Optional("icon_color"): str,
                vol.Optional("message_color"): str,
                vol.Optional("background_color"): str,
                vol.Optional("border_color"): str,
                vol.Optional("shape"): str,
                vol.Optional("size"): str,
                vol.Optional("expiration"): str,
                vol.Optional("show_duration"): int,
                vol.Optional("collapse_duration"): int,
                vol.Optional("repeat_expand"): bool,
            },
            extra=vol.ALLOW_EXTRA,
        ),
    )

    hass.services.async_register(
        DOMAIN,
        "remove_fixed_notification",
        handle_remove_fixed_notification,
        schema=vol.Schema(
            {vol.Required("id"): str},
            extra=vol.ALLOW_EXTRA,
        ),
    )

    hass.services.async_register(
        DOMAIN,
        "screen_on",
        handle_screen_on,
        schema=vol.Schema({}, extra=vol.ALLOW_EXTRA),
    )


def _to_camel_case(snake_str: str) -> str:
    """Convert snake_case to camelCase."""
    parts = snake_str.split("_")
    return parts[0] + "".join(word.capitalize() for word in parts[1:])
