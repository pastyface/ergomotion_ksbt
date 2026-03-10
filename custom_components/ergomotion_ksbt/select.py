from __future__ import annotations

from homeassistant.components.select import SelectEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import DOMAIN
from .entity import ErgomotionKsbtEntity

PRESET_OPTIONS: dict[str, str] = {
    "Zero G": "zero_g",
    "Flat": "flat",
    "Relax": "relax",
    "Anti Snore": "anti_snore",
    "TV": "tv",
    "Memory": "memory",
}

MASSAGE_OPTIONS: dict[str, str] = {
    "Massage All": "massage_all",
    "Massage Head": "massage_head",
    "Massage Foot": "massage_foot",
    "Massage Timer": "massage_timer",
}


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    hub = hass.data[DOMAIN][entry.entry_id]
    async_add_entities(
        [
            ErgomotionKsbtPresetSelect(hub),
            ErgomotionKsbtMassageSelect(hub),
        ]
    )


class _BaseErgomotionKsbtSelect(ErgomotionKsbtEntity, SelectEntity):
    state_key: str
    option_to_action: dict[str, str]

    def __init__(self, hub, unique_suffix: str, name: str, icon: str) -> None:
        super().__init__(hub, unique_suffix)
        self._attr_name = name
        self._attr_icon = icon
        self._attr_options = list(self.option_to_action)

    @property
    def current_option(self) -> str | None:
        return self.hub.get_optimistic_state(self.state_key)

    async def async_select_option(self, option: str) -> None:
        action = self.option_to_action[option]
        await self.hub.async_press_action(action, {self.state_key: option})


class ErgomotionKsbtPresetSelect(_BaseErgomotionKsbtSelect):
    state_key = "preset"
    option_to_action = PRESET_OPTIONS

    def __init__(self, hub) -> None:
        super().__init__(hub, "preset", "Preset", "mdi:bed")


class ErgomotionKsbtMassageSelect(_BaseErgomotionKsbtSelect):
    state_key = "massage_mode"
    option_to_action = MASSAGE_OPTIONS

    def __init__(self, hub) -> None:
        super().__init__(hub, "massage_mode", "Massage Mode", "mdi:waves")
