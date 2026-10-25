"""OverSight Android TV integration for Home Assistant."""

from __future__ import annotations

from typing import TYPE_CHECKING

from homeassistant.const import Platform
from homeassistant.helpers.aiohttp_client import async_get_clientsession

from .api import OversightApiClient
from .const import CONF_HOST, CONF_PORT, LOGGER
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
        config_entry=entry,
        client=client,
    )

    await coordinator.async_config_entry_first_refresh()

    entry.runtime_data = OversightData(
        client=client,
        coordinator=coordinator,
    )

    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    entry.async_on_unload(entry.add_update_listener(async_reload_entry))

    return True


async def async_unload_entry(
    hass: HomeAssistant,
    entry: OversightConfigEntry,
) -> bool:
    """Handle removal of an entry."""
    return await hass.config_entries.async_unload_platforms(entry, PLATFORMS)


async def async_reload_entry(
    hass: HomeAssistant,
    entry: OversightConfigEntry,
) -> None:
    """Reload config entry."""
    await hass.config_entries.async_reload(entry.entry_id)
