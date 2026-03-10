from __future__ import annotations

import asyncio
import logging
from collections.abc import Callable
from typing import Any

from bleak import BleakClient
from homeassistant.components import bluetooth
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant, callback

from .const import BLEAK_CONNECT_TIMEOUT, NOTIFY_CHAR_UUID, WRITE_CHAR_UUID
from .protocol import (
    SequenceStep,
    build_hold_steps,
    build_instruct_payload,
    build_prepare_steps,
    build_preset_steps,
    decode_notification,
    inferred_action_state,
)

_LOGGER = logging.getLogger(__name__)


class ErgomotionKsbtHub:
    def __init__(self, hass: HomeAssistant, entry: ConfigEntry) -> None:
        self.hass = hass
        self.entry = entry
        self.address: str = entry.unique_id or entry.data["address"]
        self.name: str = entry.title or self.address

        self._connected = False
        self._last_notification: bytes | None = None
        self._listeners: set[Callable[[], None]] = set()
        self._command_lock = asyncio.Lock()
        self._debug_logging_enabled = False
        self._optimistic_state: dict[str, Any] = {
            "preset": None,
            "massage_mode": None,
        }
        self._decoded_state: dict[str, Any] = {
            "notification_type": None,
            "notification_length": None,
            "token": None,
            "token_counter": None,
            "light_enabled": None,
            "light_level": None,
            "massage_frame": None,
            "massage_timer_minutes": None,
            "massage_head_active": None,
            "massage_foot_active": None,
            "snapshot_counter": None,
            "status_frame": None,
            "extended_status_frame": None,
            "extended_status_code": None,
        }

    @property
    def connected(self) -> bool:
        return self._connected

    @property
    def available(self) -> bool:
        return self._connected or bluetooth.async_address_present(
            self.hass, self.address, connectable=True
        )

    @property
    def last_notification(self) -> bytes | None:
        return self._last_notification

    @property
    def last_notification_hex(self) -> str | None:
        if self._last_notification is None:
            return None
        return self._last_notification.hex(" ")

    @property
    def debug_logging_enabled(self) -> bool:
        return self._debug_logging_enabled

    def get_optimistic_state(self, key: str) -> Any:
        return self._optimistic_state.get(key)

    def get_decoded_state(self, key: str) -> Any:
        return self._decoded_state.get(key)

    @callback
    def async_set_debug_logging(self, enabled: bool) -> None:
        self._debug_logging_enabled = enabled
        _LOGGER.warning(
            "Ergomotion KSBT debug logging %s for %s (%s)",
            "enabled" if enabled else "disabled",
            self.name,
            self.address,
        )
        self._notify_listeners()

    def async_log_debug_snapshot(self) -> None:
        _LOGGER.warning(
            "Ergomotion KSBT state for %s (%s): connected=%s last_notification=%s decoded=%s optimistic=%s",
            self.name,
            self.address,
            self._connected,
            self.last_notification_hex,
            self._decoded_state,
            self._optimistic_state,
        )

    @callback
    def async_add_listener(self, listener: Callable[[], None]) -> Callable[[], None]:
        self._listeners.add(listener)

        @callback
        def _remove() -> None:
            self._listeners.discard(listener)

        return _remove

    @callback
    def async_update_discovery(
        self, service_info: bluetooth.BluetoothServiceInfoBleak
    ) -> None:
        local_name = service_info.name or service_info.device.name
        if local_name:
            self.name = local_name
        self._notify_listeners()

    async def async_prepare(self) -> None:
        await self._async_run_steps(build_prepare_steps())

    async def async_press_action(
        self,
        action: str,
        optimistic_updates: dict[str, Any] | None = None,
    ) -> None:
        await self._async_run_steps(build_preset_steps(action))
        updates = dict(inferred_action_state(action))
        if optimistic_updates:
            updates.update(optimistic_updates)
        if updates:
            self._optimistic_state.update(updates)
            self._notify_listeners()

    async def async_hold_action(self, action: str, duration: float) -> None:
        await self._async_run_steps(build_hold_steps(action, duration=duration))

    async def async_stop(self) -> None:
        stop_payload = build_instruct_payload(0)
        await self._async_run_steps(
            [*build_prepare_steps(), SequenceStep(stop_payload, 0.2), SequenceStep(stop_payload, 0.0)]
        )

    async def _async_run_steps(self, steps: list[SequenceStep]) -> None:
        async with self._command_lock:
            ble_device = bluetooth.async_ble_device_from_address(
                self.hass, self.address, connectable=True
            )
            if ble_device is None:
                raise RuntimeError(
                    f"No connectable Bluetooth device is available for {self.address}"
                )

            _LOGGER.debug("Connecting to %s", self.address)
            async with BleakClient(ble_device, timeout=BLEAK_CONNECT_TIMEOUT) as client:
                self._set_connected(True)
                try:
                    await client.start_notify(NOTIFY_CHAR_UUID, self._handle_notification)
                    for step in steps:
                        _LOGGER.debug("Sending %s", step.payload.hex())
                        await client.write_gatt_char(
                            WRITE_CHAR_UUID, step.payload, response=False
                        )
                        if step.delay_after > 0:
                            await asyncio.sleep(step.delay_after)
                finally:
                    self._set_connected(False)

    @callback
    def _handle_notification(self, _sender: object, data: bytearray) -> None:
        self._last_notification = bytes(data)
        self._decoded_state.update(decode_notification(self._last_notification))
        if self._debug_logging_enabled:
            _LOGGER.warning(
                "Ergomotion KSBT notify for %s (%s): raw=%s decoded=%s",
                self.name,
                self.address,
                self.last_notification_hex,
                self._decoded_state,
            )
        self._notify_listeners()

    @callback
    def _set_connected(self, value: bool) -> None:
        self._connected = value
        self._notify_listeners()

    @callback
    def _notify_listeners(self) -> None:
        for listener in list(self._listeners):
            listener()
