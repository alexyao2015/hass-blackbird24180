"""Config flow for Blackbird24180 integration."""

from __future__ import annotations

import logging
from typing import Any

from aioblackbird24180 import Blackbird24180, ConnectError
import voluptuous as vol

from homeassistant.config_entries import (
    ConfigEntry,
    ConfigFlow,
    ConfigFlowResult,
    OptionsFlow,
)
from homeassistant.const import CONF_HOST, CONF_PORT
from homeassistant.core import callback
from homeassistant.helpers.typing import VolDictType

from .const import CONF_INPUTS, DOMAIN, INPUTS

_LOGGER = logging.getLogger(__name__)

OPTIONS_FOR_DATA: VolDictType = {vol.Optional(source): str for source in INPUTS}

DATA_SCHEMA = vol.Schema(
    {
        vol.Required(CONF_HOST): str,
        vol.Required(CONF_PORT, default=80): int,
        **OPTIONS_FOR_DATA,
    }
)


@callback
def _selected_options(
    data: dict[str, str], selected_options: list[str]
) -> dict[str, str]:
    """Return the selected options."""
    # This will provide a mapping for all inputs the user named in the config flow
    sources_config = {}
    for idx, source_name in enumerate(selected_options):
        user_defined_name = data.get(source_name)
        if user_defined_name is None or user_defined_name.strip() == "":
            continue
        sources_config[str(idx + 1)] = user_defined_name.strip()

    # idx -> user_defined_name
    return sources_config


def _get_options_from_user_input(user_input: dict[str, Any]) -> dict[str, str]:
    return {
        CONF_INPUTS: _selected_options(user_input, INPUTS),
    }


async def validate_input(data: dict[str, Any]) -> dict[str, str]:
    """Validate the user input allows us to connect.

    Data has the keys from DATA_SCHEMA with values provided by the user.
    """
    try:
        client = Blackbird24180(data[CONF_HOST], data[CONF_PORT])
        await client.get_matrix()
    except ConnectError as ex:
        _LOGGER.error(
            "Error connecting to Blackbird Matrix at %s:%s",
            data[CONF_HOST],
            data[CONF_PORT],
        )
        raise ex

    return {CONF_HOST: data[CONF_HOST], CONF_PORT: data[CONF_PORT]}


class Blackbird24180ConfigFlow(ConfigFlow, domain=DOMAIN):
    """Handle a config flow for Blackbird24180."""

    VERSION = 1

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Handle the initial step."""
        errors = {}
        if user_input is not None:
            try:
                data = await validate_input(user_input)
                options = _get_options_from_user_input(user_input)

                return self.async_create_entry(
                    title=f"{user_input[CONF_HOST]}:{user_input[CONF_PORT]}",
                    data=data,
                    options=options,
                )
            except ConnectError:
                errors["base"] = "cannot_connect"
            except Exception:
                _LOGGER.exception("Unexpected exception")
                errors["base"] = "unknown"

        return self.async_show_form(
            step_id="user", data_schema=DATA_SCHEMA, errors=errors
        )

    @staticmethod
    @callback
    def async_get_options_flow(
        config_entry: ConfigEntry,
    ) -> Blackbird24810OptionsFlowHandler:
        """Define the config flow to handle options."""
        return Blackbird24810OptionsFlowHandler(config_entry)


class Blackbird24810OptionsFlowHandler(OptionsFlow):
    """Handle a Monoprice options flow."""

    def __init__(self, config_entry: ConfigEntry) -> None:
        """Initialize."""
        self.config_entry = config_entry

    async def async_step_init(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Manage the options."""
        if user_input is not None:
            return self.async_create_entry(
                title="", data=_get_options_from_user_input(user_input)
            )

        # Generate compatible existing options that match the options schema
        existing_input_settings = {
            f"input_{input_id}": v
            for input_id, v in self.config_entry.options.get(CONF_INPUTS, {}).items()
        }

        return self.async_show_form(
            step_id="init",
            data_schema=self.add_suggested_values_to_schema(
                vol.Schema(OPTIONS_FOR_DATA), existing_input_settings
            ),
        )
