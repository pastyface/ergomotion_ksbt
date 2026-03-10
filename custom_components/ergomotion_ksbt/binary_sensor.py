from __future__ import annotations

from homeassistant.components.binary_sensor import BinarySensorEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import EntityCategory
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import DOMAIN
from .entity import ErgomotionKsbtEntity


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    hub = hass.data[DOMAIN][entry.entry_id]
    async_add_entities(
        [
            ErgomotionKsbtConnectionEntity(hub),
            ErgomotionKsbtLightEnabledEntity(hub),
            ErgomotionKsbtMassageHeadActiveEntity(hub),
            ErgomotionKsbtMassageFootActiveEntity(hub),
        ]
    )


class ErgomotionKsbtConnectionEntity(ErgomotionKsbtEntity, BinarySensorEntity):
    _attr_name = "Connection"
    _attr_entity_category = EntityCategory.DIAGNOSTIC
    _attr_icon = "mdi:bluetooth-connect"

    def __init__(self, hub) -> None:
        super().__init__(hub, "connection")

    @property
    def is_on(self) -> bool:
        return self.hub.connected


class ErgomotionKsbtLightEnabledEntity(ErgomotionKsbtEntity, BinarySensorEntity):
    _attr_name = "Light Enabled"
    _attr_icon = "mdi:lightbulb-on-outline"

    def __init__(self, hub) -> None:
        super().__init__(hub, "light_enabled")

    @property
    def is_on(self) -> bool | None:
        value = self.hub.get_decoded_state("light_enabled")
        return None if value is None else bool(value)


class ErgomotionKsbtMassageHeadActiveEntity(ErgomotionKsbtEntity, BinarySensorEntity):
    _attr_name = "Massage Head Active"
    _attr_icon = "mdi:head"

    def __init__(self, hub) -> None:
        super().__init__(hub, "massage_head_active")

    @property
    def is_on(self) -> bool | None:
        value = self.hub.get_decoded_state("massage_head_active")
        return None if value is None else bool(value)


class ErgomotionKsbtMassageFootActiveEntity(ErgomotionKsbtEntity, BinarySensorEntity):
    _attr_name = "Massage Foot Active"
    _attr_icon = "mdi:foot-print"

    def __init__(self, hub) -> None:
        super().__init__(hub, "massage_foot_active")

    @property
    def is_on(self) -> bool | None:
        value = self.hub.get_decoded_state("massage_foot_active")
        return None if value is None else bool(value)
