"""Support for interfacing with Blackbird24180."""

import logging

from homeassistant.components.media_player import (
    MediaPlayerDeviceClass,
    MediaPlayerEntity,
    MediaPlayerEntityFeature,
    MediaPlayerState,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONF_HOST, CONF_PORT
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import CONF_INPUTS, DOMAIN, OUTPUTS
from .coordinator import Blackbird24180DataUpdateCoordinator

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(
    hass: HomeAssistant,
    config_entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up the Blackbird24180 platform."""
    device_path = f"{config_entry.data[CONF_HOST]}:{config_entry.data[CONF_PORT]}"

    client = config_entry.runtime_data

    entities = []
    for output_id in range(1, len(OUTPUTS) + 1):
        _LOGGER.debug("Adding output %d for device %s", output_id, device_path)
        entities.append(
            BlackbirdOutput(
                client,
                config_entry.options[CONF_INPUTS],
                config_entry.entry_id,
                output_id,
            )
        )

    async_add_entities(entities)


class BlackbirdOutput(
    CoordinatorEntity[Blackbird24180DataUpdateCoordinator], MediaPlayerEntity
):
    """Representation of a Blackbird24180 output."""

    _attr_device_class = MediaPlayerDeviceClass.RECEIVER
    _attr_supported_features = MediaPlayerEntityFeature.SELECT_SOURCE
    _attr_has_entity_name = True
    _attr_name = None
    # There is no way to toggle the power state of the output it is always on
    _attr_state = MediaPlayerState.ON

    def __init__(
        self,
        coordinator: Blackbird24180DataUpdateCoordinator,
        source_mapping: dict[str, str],
        entry_id: str,
        output_id: int,
    ) -> None:
        """Initialize new zone."""
        super().__init__(coordinator)
        self._source_id_name = source_mapping
        # invert config mapping to name -> id
        self._source_name_id = {v: k for k, v in source_mapping.items()}
        # ordered list of all source names
        self._attr_source_list = sorted(source_mapping.values())
        self._output_id = output_id
        self._attr_unique_id = f"{entry_id}_{self._output_id}"
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, self._attr_unique_id)},
            manufacturer="Monoprice",
            model="Blackbird 24180 8x8 HDMI Matrix",
            name=f"Output {self._output_id}",
        )

    @property
    def source(self) -> str:
        """Return the current source."""
        input_id = self.coordinator.data.get_output(self._output_id)
        return self._source_id_name.get(str(input_id))

    @callback
    def _handle_coordinator_update(self) -> None:
        """Handle updated data from the coordinator."""
        self.async_write_ha_state()

    async def async_select_source(self, source: str) -> None:
        """Set input source."""
        if not self._source_name_id.get(source):
            _LOGGER.warning("Invalid source %s for output %d", source, self._output_id)
            return
        await self.coordinator.client.set_output(
            self._output_id, int(self._source_name_id[source])
        )
        await self.coordinator.async_request_refresh()
