from __future__ import annotations

from homeassistant.helpers.device_registry import CONNECTION_BLUETOOTH
from homeassistant.helpers.entity import DeviceInfo, Entity

from .client import ErgomotionKsbtHub
from .const import DOMAIN


class ErgomotionKsbtEntity(Entity):
    _attr_should_poll = False

    def __init__(self, hub: ErgomotionKsbtHub, unique_suffix: str) -> None:
        self.hub = hub
        self._attr_unique_id = f"{hub.address.lower().replace(':', '')}_{unique_suffix}"
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, hub.address)},
            connections={(CONNECTION_BLUETOOTH, hub.address)},
            manufacturer="Ergomotion",
            model="KSBT bed",
            name=hub.name,
        )
        self._remove_listener = None

    @property
    def available(self) -> bool:
        return self.hub.available

    async def async_added_to_hass(self) -> None:
        self._remove_listener = self.hub.async_add_listener(self._handle_hub_update)

    async def async_will_remove_from_hass(self) -> None:
        if self._remove_listener:
            self._remove_listener()
            self._remove_listener = None

    def _handle_hub_update(self) -> None:
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, self.hub.address)},
            connections={(CONNECTION_BLUETOOTH, self.hub.address)},
            manufacturer="Ergomotion",
            model="KSBT bed",
            name=self.hub.name,
        )
        self.async_write_ha_state()
