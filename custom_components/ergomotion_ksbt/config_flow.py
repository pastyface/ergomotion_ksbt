from __future__ import annotations

import re

import voluptuous as vol
from homeassistant.components import bluetooth
from homeassistant.config_entries import ConfigFlow, OptionsFlow
from homeassistant.const import CONF_ADDRESS, CONF_NAME

from .const import (
    CONF_FEET_HOLD_SECONDS,
    CONF_HEAD_HOLD_SECONDS,
    CONF_LUMBAR_HOLD_SECONDS,
    DEFAULT_HOLD_SECONDS,
    DOMAIN,
)

MAC_RE = re.compile(r"^(?:[0-9A-Fa-f]{2}:){5}[0-9A-Fa-f]{2}$")


def _discovered_ksbt_devices(hass) -> list[bluetooth.BluetoothServiceInfoBleak]:
    devices = bluetooth.async_discovered_service_info(hass, connectable=True)
    return sorted(
        [
            service_info
            for service_info in devices
            if (service_info.name or service_info.device.name or "").startswith("KSBT")
        ],
        key=lambda info: info.address,
    )


def _options_schema(config_entry):
    return vol.Schema(
        {
            vol.Required(
                CONF_HEAD_HOLD_SECONDS,
                default=float(
                    config_entry.options.get(CONF_HEAD_HOLD_SECONDS, DEFAULT_HOLD_SECONDS)
                ),
            ): vol.All(vol.Coerce(float), vol.Range(min=0.2, max=10.0)),
            vol.Required(
                CONF_FEET_HOLD_SECONDS,
                default=float(
                    config_entry.options.get(CONF_FEET_HOLD_SECONDS, DEFAULT_HOLD_SECONDS)
                ),
            ): vol.All(vol.Coerce(float), vol.Range(min=0.2, max=10.0)),
            vol.Required(
                CONF_LUMBAR_HOLD_SECONDS,
                default=float(
                    config_entry.options.get(CONF_LUMBAR_HOLD_SECONDS, DEFAULT_HOLD_SECONDS)
                ),
            ): vol.All(vol.Coerce(float), vol.Range(min=0.2, max=10.0)),
        }
    )


class ErgomotionKsbtConfigFlow(ConfigFlow, domain=DOMAIN):
    VERSION = 1

    def __init__(self) -> None:
        self._discovered_device: bluetooth.BluetoothServiceInfoBleak | None = None

    async def async_step_user(self, user_input=None):
        errors: dict[str, str] = {}

        if user_input is not None:
            address = user_input[CONF_ADDRESS].upper()
            if not MAC_RE.match(address):
                errors["base"] = "invalid_address"
            else:
                await self.async_set_unique_id(address)
                self._abort_if_unique_id_configured()

                title = user_input.get(CONF_NAME) or address
                return self.async_create_entry(
                    title=title,
                    data={CONF_ADDRESS: address, CONF_NAME: user_input.get(CONF_NAME, "")},
                )

        discovered = _discovered_ksbt_devices(self.hass)
        discovered_lines = "\n".join(
            f"- {info.address} ({info.name or info.device.name or 'unknown'})"
            for info in discovered
        ) or "None yet. You can still enter the MAC address manually."
        default_address = discovered[0].address if discovered else ""
        default_name = discovered[0].name if discovered else ""

        return self.async_show_form(
            step_id="user",
            data_schema=vol.Schema(
                {
                    vol.Required(CONF_ADDRESS, default=default_address): str,
                    vol.Optional(CONF_NAME, default=default_name): str,
                }
            ),
            errors=errors,
            description_placeholders={"discovered_devices": discovered_lines},
        )

    async def async_step_bluetooth(
        self, discovery_info: bluetooth.BluetoothServiceInfoBleak
    ):
        await self.async_set_unique_id(discovery_info.address)
        self._abort_if_unique_id_configured()

        local_name = discovery_info.name or discovery_info.device.name or ""
        if not local_name.startswith("KSBT"):
            return self.async_abort(reason="not_supported")

        self._discovered_device = discovery_info
        self.context["title_placeholders"] = {"name": local_name}
        return await self.async_step_bluetooth_confirm()

    async def async_step_bluetooth_confirm(self, user_input=None):
        assert self._discovered_device is not None

        if user_input is not None:
            return self.async_create_entry(
                title=self._discovered_device.name or self._discovered_device.address,
                data={
                    CONF_ADDRESS: self._discovered_device.address,
                    CONF_NAME: self._discovered_device.name or "",
                },
            )

        self._set_confirm_only()
        return self.async_show_form(
            step_id="bluetooth_confirm",
            description_placeholders={
                "name": self._discovered_device.name or self._discovered_device.address,
                "address": self._discovered_device.address,
            },
        )

    @staticmethod
    def async_get_options_flow(config_entry):
        return ErgomotionKsbtOptionsFlow(config_entry)


class ErgomotionKsbtOptionsFlow(OptionsFlow):
    def __init__(self, config_entry) -> None:
        self.config_entry = config_entry

    async def async_step_init(self, user_input=None):
        if user_input is not None:
            return self.async_create_entry(title="", data=user_input)

        return self.async_show_form(
            step_id="init",
            data_schema=_options_schema(self.config_entry),
        )
