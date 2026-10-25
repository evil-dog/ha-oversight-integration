"""OverSight Android TV integration for Home Assistant."""

from __future__ import annotations

from typing import TYPE_CHECKING

from homeassistant.const import CONF_HOST, CONF_PORT, Platform
from homeassistant.helpers import config_validation as cv
from homeassistant.helpers.aiohttp_client import async_get_clientsession

from .api import OversightApiClient
from .const import DOMAIN, LOGGER
from .coordinator import OversightDataUpdateCoordinator
from .data import OversightData
from .services import async_setup_services

if TYPE_CHECKING:
    from homeassistant.core import HomeAssistant
    from homeassistant.helpers.typing import ConfigType

    from .data import OversightConfigEntry

PLATFORMS: list[Platform] = [
    Platform.BINARY_SENSOR,
    Platform.BUTTON,
    Platform.NOTIFY,
    Platform.NUMBER,
    Platform.SELECT,
    Platform.SWITCH,
    Platform.TEXT,
]

CONFIG_SCHEMA = cv.config_entry_only_config_schema(DOMAIN)


async def async_setup(hass: HomeAssistant, config: ConfigType) -> bool:  # noqa: ARG001
    """Set up the OverSight Android TV actions."""
    async_setup_services(hass)
    return True


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

    entry.runtime_data = OversightData(coordinator=coordinator)

    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)

    return True


async def async_unload_entry(
    hass: HomeAssistant,
    entry: OversightConfigEntry,
) -> bool:
    """Handle removal of an entry."""
    return await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
