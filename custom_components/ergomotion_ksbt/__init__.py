from __future__ import annotations

import voluptuous as vol
from homeassistant.components import bluetooth
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant, ServiceCall, callback

from .client import ErgomotionKsbtHub
from .const import DOMAIN, PLATFORMS
from .protocol import CANONICAL_ACTIONS

SERVICE_PRESS_ACTION = "press_action"
SERVICE_HOLD_ACTION = "hold_action"
SERVICE_PREPARE = "prepare"
SERVICE_STOP = "stop"
SERVICE_SET_DEBUG_LOGGING = "set_debug_logging"
SERVICE_DUMP_DEBUG_STATE = "dump_debug_state"

SERVICE_ADDRESS = "address"
SERVICE_ACTION = "action"
SERVICE_DURATION = "duration"
SERVICE_ENABLED = "enabled"

PRESS_ACTION_SCHEMA = vol.Schema(
    {
        vol.Optional(SERVICE_ADDRESS): str,
        vol.Required(SERVICE_ACTION): vol.In(CANONICAL_ACTIONS),
    }
)
HOLD_ACTION_SCHEMA = vol.Schema(
    {
        vol.Optional(SERVICE_ADDRESS): str,
        vol.Required(SERVICE_ACTION): vol.In(
            [
                "back_up",
                "back_down",
                "feet_up",
                "feet_down",
                "lumbar_up",
                "lumbar_down",
            ]
        ),
        vol.Optional(SERVICE_DURATION, default=2.0): vol.All(
            vol.Coerce(float), vol.Range(min=0.2, max=30.0)
        ),
    }
)
ADDRESS_ONLY_SCHEMA = vol.Schema({vol.Optional(SERVICE_ADDRESS): str})
DEBUG_LOGGING_SCHEMA = vol.Schema(
    {
        vol.Optional(SERVICE_ADDRESS): str,
        vol.Required(SERVICE_ENABLED): bool,
    }
)


async def async_setup(hass: HomeAssistant, _config) -> bool:
    hass.data.setdefault(DOMAIN, {})

    async def _async_handle_press_action(call: ServiceCall) -> None:
        hub = _resolve_hub(hass, call.data.get(SERVICE_ADDRESS))
        await hub.async_press_action(call.data[SERVICE_ACTION])

    async def _async_handle_hold_action(call: ServiceCall) -> None:
        hub = _resolve_hub(hass, call.data.get(SERVICE_ADDRESS))
        await hub.async_hold_action(call.data[SERVICE_ACTION], call.data[SERVICE_DURATION])

    async def _async_handle_prepare(call: ServiceCall) -> None:
        hub = _resolve_hub(hass, call.data.get(SERVICE_ADDRESS))
        await hub.async_prepare()

    async def _async_handle_stop(call: ServiceCall) -> None:
        hub = _resolve_hub(hass, call.data.get(SERVICE_ADDRESS))
        await hub.async_stop()

    async def _async_handle_set_debug_logging(call: ServiceCall) -> None:
        hub = _resolve_hub(hass, call.data.get(SERVICE_ADDRESS))
        hub.async_set_debug_logging(call.data[SERVICE_ENABLED])

    async def _async_handle_dump_debug_state(call: ServiceCall) -> None:
        hub = _resolve_hub(hass, call.data.get(SERVICE_ADDRESS))
        hub.async_log_debug_snapshot()

    if not hass.services.has_service(DOMAIN, SERVICE_PRESS_ACTION):
        hass.services.async_register(
            DOMAIN,
            SERVICE_PRESS_ACTION,
            _async_handle_press_action,
            schema=PRESS_ACTION_SCHEMA,
        )
        hass.services.async_register(
            DOMAIN,
            SERVICE_HOLD_ACTION,
            _async_handle_hold_action,
            schema=HOLD_ACTION_SCHEMA,
        )
        hass.services.async_register(
            DOMAIN,
            SERVICE_PREPARE,
            _async_handle_prepare,
            schema=ADDRESS_ONLY_SCHEMA,
        )
        hass.services.async_register(
            DOMAIN,
            SERVICE_STOP,
            _async_handle_stop,
            schema=ADDRESS_ONLY_SCHEMA,
        )
        hass.services.async_register(
            DOMAIN,
            SERVICE_SET_DEBUG_LOGGING,
            _async_handle_set_debug_logging,
            schema=DEBUG_LOGGING_SCHEMA,
        )
        hass.services.async_register(
            DOMAIN,
            SERVICE_DUMP_DEBUG_STATE,
            _async_handle_dump_debug_state,
            schema=ADDRESS_ONLY_SCHEMA,
        )

    return True


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    hub = ErgomotionKsbtHub(hass, entry)
    hass.data.setdefault(DOMAIN, {})[entry.entry_id] = hub

    if service_info := bluetooth.async_last_service_info(
        hass, hub.address, connectable=True
    ):
        hub.async_update_discovery(service_info)

    @callback
    def _async_update_ble(
        service_info: bluetooth.BluetoothServiceInfoBleak,
        _change: bluetooth.BluetoothChange,
    ) -> None:
        hub.async_update_discovery(service_info)

    entry.async_on_unload(
        bluetooth.async_register_callback(
            hass,
            _async_update_ble,
            {"address": hub.address, "connectable": True},
            bluetooth.BluetoothScanningMode.ACTIVE,
        )
    )

    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    unloaded = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
    if unloaded:
        hass.data[DOMAIN].pop(entry.entry_id, None)
    return unloaded


def _resolve_hub(hass: HomeAssistant, address: str | None) -> ErgomotionKsbtHub:
    hubs: dict[str, ErgomotionKsbtHub] = hass.data.get(DOMAIN, {})
    if not hubs:
        raise vol.Invalid("No Ergomotion KSBT beds are configured")

    if address:
        target = address.upper()
        for hub in hubs.values():
            if hub.address.upper() == target:
                return hub
        raise vol.Invalid(f"No configured bed matches address {address}")

    if len(hubs) == 1:
        return next(iter(hubs.values()))

    raise vol.Invalid("Multiple beds are configured; specify address")
