from __future__ import annotations

from homeassistant.components.button import ButtonEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import (
    CONF_FEET_HOLD_SECONDS,
    CONF_HEAD_HOLD_SECONDS,
    CONF_LUMBAR_HOLD_SECONDS,
    DEFAULT_HOLD_SECONDS,
    DOMAIN,
)
from .entity import ErgomotionKsbtEntity
from .models import ButtonActionDescription

BUTTONS: tuple[ButtonActionDescription, ...] = (
    ButtonActionDescription("back_up", "Back Up", "mdi:arrow-up-bold-box-outline"),
    ButtonActionDescription("back_down", "Back Down", "mdi:arrow-down-bold-box-outline"),
    ButtonActionDescription("feet_up", "Feet Up", "mdi:arrow-up-bold-box-outline"),
    ButtonActionDescription("feet_down", "Feet Down", "mdi:arrow-down-bold-box-outline"),
    ButtonActionDescription("lumbar_up", "Lumbar Up", "mdi:arrow-up-bold-box-outline"),
    ButtonActionDescription("lumbar_down", "Lumbar Down", "mdi:arrow-down-bold-box-outline"),
    ButtonActionDescription("stop", "Stop", "mdi:stop-circle-outline"),
    ButtonActionDescription("zero_g", "Zero G", "mdi:bed-outline"),
    ButtonActionDescription("flat", "Flat", "mdi:bed-empty"),
    ButtonActionDescription("relax", "Relax", "mdi:sofa-outline"),
    ButtonActionDescription("anti_snore", "Anti Snore", "mdi:sleep"),
    ButtonActionDescription("tv", "TV", "mdi:television"),
    ButtonActionDescription("memory", "Memory", "mdi:bookmark"),
    ButtonActionDescription("massage_all", "Massage All", "mdi:waves"),
    ButtonActionDescription("massage_head", "Massage Head", "mdi:head"),
    ButtonActionDescription("massage_foot", "Massage Foot", "mdi:foot-print"),
    ButtonActionDescription("massage_timer", "Massage Timer", "mdi:timer-outline"),
    ButtonActionDescription("light", "Light", "mdi:lightbulb-outline"),
)

HOLD_OPTION_KEYS = {
    "back_up": CONF_HEAD_HOLD_SECONDS,
    "back_down": CONF_HEAD_HOLD_SECONDS,
    "feet_up": CONF_FEET_HOLD_SECONDS,
    "feet_down": CONF_FEET_HOLD_SECONDS,
    "lumbar_up": CONF_LUMBAR_HOLD_SECONDS,
    "lumbar_down": CONF_LUMBAR_HOLD_SECONDS,
}


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    hub = hass.data[DOMAIN][entry.entry_id]
    async_add_entities(
        [ErgomotionKsbtButtonEntity(hub, entry, description) for description in BUTTONS]
    )


class ErgomotionKsbtButtonEntity(ErgomotionKsbtEntity, ButtonEntity):
    def __init__(self, hub, entry: ConfigEntry, description: ButtonActionDescription) -> None:
        super().__init__(hub, description.key)
        self.entry = entry
        self._description = description
        self._attr_name = description.name
        self._attr_icon = description.icon

    async def async_press(self) -> None:
        key = self._description.key
        if key == "stop":
            await self.hub.async_stop()
            return
        if key in HOLD_OPTION_KEYS:
            duration = float(self.entry.options.get(HOLD_OPTION_KEYS[key], DEFAULT_HOLD_SECONDS))
            await self.hub.async_hold_action(key, duration)
            return
        await self.hub.async_press_action(key)
