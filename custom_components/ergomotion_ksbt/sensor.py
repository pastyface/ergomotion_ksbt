from __future__ import annotations

from homeassistant.components.sensor import SensorEntity
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
            ErgomotionKsbtLastNotificationSensor(hub),
            ErgomotionKsbtNotificationTypeSensor(hub),
            ErgomotionKsbtTokenSensor(hub),
            ErgomotionKsbtTokenCounterSensor(hub),
            ErgomotionKsbtLightLevelSensor(hub),
            ErgomotionKsbtMassageTimerSensor(hub),
            ErgomotionKsbtSnapshotCounterSensor(hub),
        ]
    )


class ErgomotionKsbtLastNotificationSensor(ErgomotionKsbtEntity, SensorEntity):
    _attr_name = "Last Notification"
    _attr_entity_category = EntityCategory.DIAGNOSTIC
    _attr_icon = "mdi:message-badge-outline"

    def __init__(self, hub) -> None:
        super().__init__(hub, "last_notification")

    @property
    def native_value(self) -> str | None:
        return self.hub.last_notification_hex

    @property
    def extra_state_attributes(self) -> dict[str, object]:
        return {
            key: value
            for key, value in {
                "notification_type": self.hub.get_decoded_state("notification_type"),
                "notification_length": self.hub.get_decoded_state("notification_length"),
                "token": self.hub.get_decoded_state("token"),
                "token_counter": self.hub.get_decoded_state("token_counter"),
                "light_enabled": self.hub.get_decoded_state("light_enabled"),
                "light_level": self.hub.get_decoded_state("light_level"),
                "massage_frame": self.hub.get_decoded_state("massage_frame"),
                "massage_timer_minutes": self.hub.get_decoded_state("massage_timer_minutes"),
                "massage_head_active": self.hub.get_decoded_state("massage_head_active"),
                "massage_foot_active": self.hub.get_decoded_state("massage_foot_active"),
                "snapshot_counter": self.hub.get_decoded_state("snapshot_counter"),
                "status_frame": self.hub.get_decoded_state("status_frame"),
                "extended_status_frame": self.hub.get_decoded_state("extended_status_frame"),
                "extended_status_code": self.hub.get_decoded_state("extended_status_code"),
            }.items()
            if value is not None
        }


class ErgomotionKsbtNotificationTypeSensor(ErgomotionKsbtEntity, SensorEntity):
    _attr_name = "Notification Type"
    _attr_entity_category = EntityCategory.DIAGNOSTIC
    _attr_icon = "mdi:label-outline"

    def __init__(self, hub) -> None:
        super().__init__(hub, "notification_type")

    @property
    def native_value(self) -> str | None:
        return self.hub.get_decoded_state("notification_type")


class ErgomotionKsbtTokenSensor(ErgomotionKsbtEntity, SensorEntity):
    _attr_name = "Last Token"
    _attr_entity_category = EntityCategory.DIAGNOSTIC
    _attr_icon = "mdi:key-wireless"

    def __init__(self, hub) -> None:
        super().__init__(hub, "token")

    @property
    def native_value(self) -> str | None:
        return self.hub.get_decoded_state("token")


class ErgomotionKsbtTokenCounterSensor(ErgomotionKsbtEntity, SensorEntity):
    _attr_name = "Token Counter"
    _attr_entity_category = EntityCategory.DIAGNOSTIC
    _attr_icon = "mdi:counter"

    def __init__(self, hub) -> None:
        super().__init__(hub, "token_counter")

    @property
    def native_value(self) -> int | None:
        return self.hub.get_decoded_state("token_counter")


class ErgomotionKsbtLightLevelSensor(ErgomotionKsbtEntity, SensorEntity):
    _attr_name = "Light Level"
    _attr_icon = "mdi:brightness-6"

    def __init__(self, hub) -> None:
        super().__init__(hub, "light_level")

    @property
    def native_value(self) -> int | None:
        return self.hub.get_decoded_state("light_level")


class ErgomotionKsbtMassageTimerSensor(ErgomotionKsbtEntity, SensorEntity):
    _attr_name = "Massage Timer"
    _attr_icon = "mdi:timer-outline"
    _attr_native_unit_of_measurement = "min"

    def __init__(self, hub) -> None:
        super().__init__(hub, "massage_timer_minutes")

    @property
    def native_value(self) -> int | None:
        return self.hub.get_decoded_state("massage_timer_minutes")


class ErgomotionKsbtSnapshotCounterSensor(ErgomotionKsbtEntity, SensorEntity):
    _attr_name = "Snapshot Counter"
    _attr_entity_category = EntityCategory.DIAGNOSTIC
    _attr_icon = "mdi:counter"

    def __init__(self, hub) -> None:
        super().__init__(hub, "snapshot_counter")

    @property
    def native_value(self) -> int | None:
        return self.hub.get_decoded_state("snapshot_counter")
