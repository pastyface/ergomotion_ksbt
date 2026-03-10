from __future__ import annotations

from homeassistant.components.cover import CoverEntity, CoverEntityFeature
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .client import ErgomotionKsbtHub
from .const import (
    CONF_FEET_HOLD_SECONDS,
    CONF_HEAD_HOLD_SECONDS,
    CONF_LUMBAR_HOLD_SECONDS,
    DEFAULT_HOLD_SECONDS,
    DOMAIN,
)
from .entity import ErgomotionKsbtEntity
from .models import CoverActionDescription

COVERS: tuple[CoverActionDescription, ...] = (
    CoverActionDescription("head", "Head", "mdi:bed-king-outline", "head_up", "head_down"),
    CoverActionDescription("feet", "Feet", "mdi:foot-print", "feet_up", "feet_down"),
    CoverActionDescription("lumbar", "Lumbar", "mdi:human-male-height-variant", "lumbar_up", "lumbar_down"),
)

HOLD_OPTION_KEYS = {
    "head": CONF_HEAD_HOLD_SECONDS,
    "feet": CONF_FEET_HOLD_SECONDS,
    "lumbar": CONF_LUMBAR_HOLD_SECONDS,
}


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    hub = hass.data[DOMAIN][entry.entry_id]
    async_add_entities(
        [ErgomotionKsbtCoverEntity(hub, entry, description) for description in COVERS]
    )


class ErgomotionKsbtCoverEntity(ErgomotionKsbtEntity, CoverEntity):
    _attr_supported_features = (
        CoverEntityFeature.OPEN | CoverEntityFeature.CLOSE | CoverEntityFeature.STOP
    )
    _attr_assumed_state = True

    def __init__(
        self,
        hub: ErgomotionKsbtHub,
        entry: ConfigEntry,
        description: CoverActionDescription,
    ) -> None:
        super().__init__(hub, description.key)
        self.entry = entry
        self._description = description
        self._attr_name = description.name
        self._attr_icon = description.icon
        self._attr_current_cover_position = 0
        self._attr_is_closed = True
        self._attr_is_opening = False
        self._attr_is_closing = False
        self._attr_extra_state_attributes = {"hold_seconds": self._hold_seconds}

    @property
    def extra_state_attributes(self) -> dict[str, float]:
        self._attr_extra_state_attributes = {"hold_seconds": self._hold_seconds}
        return self._attr_extra_state_attributes

    @property
    def _hold_seconds(self) -> float:
        option_key = HOLD_OPTION_KEYS[self._description.key]
        return float(self.entry.options.get(option_key, DEFAULT_HOLD_SECONDS))

    async def async_open_cover(self, **kwargs) -> None:
        self._attr_is_opening = True
        self._attr_is_closing = False
        self.async_write_ha_state()
        await self.hub.async_hold_action(
            self._description.open_action, self._hold_seconds
        )
        self._attr_current_cover_position = 100
        self._attr_is_closed = False
        self._attr_is_opening = False
        self.async_write_ha_state()

    async def async_close_cover(self, **kwargs) -> None:
        self._attr_is_closing = True
        self._attr_is_opening = False
        self.async_write_ha_state()
        await self.hub.async_hold_action(
            self._description.close_action, self._hold_seconds
        )
        self._attr_current_cover_position = 0
        self._attr_is_closed = True
        self._attr_is_closing = False
        self.async_write_ha_state()

    async def async_stop_cover(self, **kwargs) -> None:
        self._attr_is_opening = False
        self._attr_is_closing = False
        await self.hub.async_stop()
        self.async_write_ha_state()
