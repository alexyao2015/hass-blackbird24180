"""The Blackbird24180 integration."""

import logging

from aioblackbird24180 import Blackbird24180

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONF_HOST, CONF_PORT, Platform
from homeassistant.core import HomeAssistant

from .coordinator import Blackbird24180DataUpdateCoordinator

PLATFORMS = [Platform.MEDIA_PLAYER]

_LOGGER = logging.getLogger(__name__)

type Blackbird24180ConfigEntry = ConfigEntry[Blackbird24180DataUpdateCoordinator]


async def async_setup_entry(
    hass: HomeAssistant, entry: Blackbird24180ConfigEntry
) -> bool:
    """Set up Blackbird24180 from a config entry."""

    client = Blackbird24180(entry.data[CONF_HOST], entry.data[CONF_PORT])

    coordinator = Blackbird24180DataUpdateCoordinator(hass, client=client)
    await coordinator.async_config_entry_first_refresh()

    entry.runtime_data = coordinator

    entry.async_on_unload(entry.add_update_listener(_update_listener))

    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)

    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a config entry."""
    unload_ok = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
    if not unload_ok:
        return False

    return True


async def async_reload_entry(hass: HomeAssistant, entry: ConfigEntry) -> None:
    """Reload config entry."""
    await hass.config_entries.async_schedule_reload(entry.entry_id)


async def _update_listener(hass: HomeAssistant, entry: ConfigEntry) -> None:
    """Handle options update."""
    await hass.config_entries.async_reload(entry.entry_id)
