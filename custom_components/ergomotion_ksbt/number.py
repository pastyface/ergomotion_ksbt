from __future__ import annotations

import voluptuous as vol
from homeassistant.components.number import NumberEntity, NumberMode
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import (
    CONF_FEET_HOLD_SECONDS,
    CONF_HEAD_HOLD_SECONDS,
    CONF_LUMBAR_HOLD_SECONDS,
    DEFAULT_HOLD_SECONDS,
    DOMAIN,
    HOLD_SECONDS_STEP,
    MAX_HOLD_SECONDS,
    MIN_HOLD_SECONDS,
)
from .entity import ErgomotionKsbtEntity

NUMBER_DEFINITIONS = (
    (CONF_HEAD_HOLD_SECONDS, "Head Hold Duration", "mdi:timer-cog-outline"),
    (CONF_FEET_HOLD_SECONDS, "Feet Hold Duration", "mdi:timer-cog-outline"),
    (CONF_LUMBAR_HOLD_SECONDS, "Lumbar Hold Duration", "mdi:timer-cog-outline"),
)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    hub = hass.data[DOMAIN][entry.entry_id]
    async_add_entities(
        ErgomotionKsbtHoldDurationNumber(hub, entry, option_key, name, icon)
        for option_key, name, icon in NUMBER_DEFINITIONS
    )


class ErgomotionKsbtHoldDurationNumber(ErgomotionKsbtEntity, NumberEntity):
    _attr_mode = NumberMode.BOX
    _attr_native_min_value = MIN_HOLD_SECONDS
    _attr_native_max_value = MAX_HOLD_SECONDS
    _attr_native_step = HOLD_SECONDS_STEP
    _attr_native_unit_of_measurement = "s"

    def __init__(self, hub, entry: ConfigEntry, option_key: str, name: str, icon: str) -> None:
        super().__init__(hub, option_key)
        self.entry = entry
        self.option_key = option_key
        self._attr_name = name
        self._attr_icon = icon

    @property
    def native_value(self) -> float:
        return float(self.entry.options.get(self.option_key, DEFAULT_HOLD_SECONDS))

    async def async_set_native_value(self, value: float) -> None:
        value = round(float(value), 1)
        if value < MIN_HOLD_SECONDS or value > MAX_HOLD_SECONDS:
            raise vol.Invalid("Hold duration is out of range")
        options = dict(self.entry.options)
        options[self.option_key] = value
        self.hass.config_entries.async_update_entry(self.entry, options=options)
        self.async_write_ha_state()
