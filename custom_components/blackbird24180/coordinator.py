"""The Blackbird24180 integration."""

from __future__ import annotations

from datetime import timedelta
import logging

from aioblackbird24180 import Blackbird24180, ConnectError, MatrixState

from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .const import DOMAIN

_LOGGER = logging.getLogger(__name__)

SCAN_INTERVAL = timedelta(seconds=60)


class Blackbird24180DataUpdateCoordinator(DataUpdateCoordinator[MatrixState]):
    """Class to manage fetching data from the API."""

    def __init__(self, hass: HomeAssistant, client: Blackbird24180) -> None:
        """Initialize."""
        self.client = client

        super().__init__(hass, _LOGGER, name=DOMAIN, update_interval=SCAN_INTERVAL)

    async def _async_update_data(self) -> MatrixState:
        """Update data via library."""
        try:
            return await self.client.get_matrix()
        except ConnectError as ex:
            raise UpdateFailed("Error connecting to Blackbird Matrix") from ex
