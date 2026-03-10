from __future__ import annotations

from dataclasses import dataclass

from .const import (
    DEFAULT_HOLD_SECONDS,
    PREPARE_QUERY_DELAY_SECONDS,
    PREPARE_READY_DELAY_SECONDS,
    PRESET_SETTLE_SECONDS,
    REPEAT_INTERVAL_SECONDS,
)

INSTRUCT_VALUES: dict[str, int] = {
    "stop": 0,
    "head_up": 1,
    "back_up": 1,
    "head_down": 2,
    "back_down": 2,
    "foot_up": 4,
    "feet_up": 4,
    "foot_down": 8,
    "feet_down": 8,
    "lumbar_up": 64,
    "lumbar_down": 128,
    "massage_all": 256,
    "massage_timer": 512,
    "massage_foot": 1024,
    "massage_head": 2048,
    "zero_g": 4096,
    "relax": 8192,
    "tv": 16384,
    "anti_snore": 32768,
    "memory": 65536,
    "light": 131072,
    "flat": 134217728,
}

CANONICAL_ACTIONS: tuple[str, ...] = (
    "back_up",
    "back_down",
    "feet_up",
    "feet_down",
    "lumbar_up",
    "lumbar_down",
    "zero_g",
    "flat",
    "relax",
    "anti_snore",
    "tv",
    "memory",
    "massage_all",
    "massage_head",
    "massage_foot",
    "massage_timer",
    "light",
)

PRESET_LABELS = {
    "zero_g": "Zero G",
    "flat": "Flat",
    "relax": "Relax",
    "anti_snore": "Anti Snore",
    "tv": "TV",
    "memory": "Memory",
}

MASSAGE_LABELS = {
    "massage_all": "Massage All",
    "massage_head": "Massage Head",
    "massage_foot": "Massage Foot",
    "massage_timer": "Massage Timer",
}


@dataclass(frozen=True)
class SequenceStep:
    payload: bytes
    delay_after: float = 0.0


def signed_byte_sum(data: bytes) -> int:
    return sum(value if value < 0x80 else value - 0x100 for value in data)


def build_instruct_payload(value: int) -> bytes:
    payload = bytearray.fromhex("AA 03 00 0A 00 04 01 00 00 00 00 00 F3 55")
    payload[7:11] = int(value).to_bytes(4, byteorder="little", signed=True)
    payload[11] = (~signed_byte_sum(payload[5:11])) & 0xFF
    return bytes(payload)


def build_light_query_payload(level: int = 0, enabled: bool = True) -> bytes:
    payload = bytearray.fromhex("AA 01 00 09 01 21 00 00 02 00 00 00 55")
    payload[4] = 1 if enabled else 0
    payload[10] = level & 0xFF
    payload[11] = (~signed_byte_sum(payload[1:11])) & 0xFF
    return bytes(payload)


def build_query_alarm_payload() -> bytes:
    return b"7102060680"


def build_prepare_steps() -> list[SequenceStep]:
    return [
        SequenceStep(build_query_alarm_payload(), PREPARE_QUERY_DELAY_SECONDS),
        SequenceStep(build_light_query_payload(), PREPARE_READY_DELAY_SECONDS),
    ]


def build_preset_steps(action: str) -> list[SequenceStep]:
    payload = build_instruct_payload(INSTRUCT_VALUES[action])
    stop_payload = build_instruct_payload(INSTRUCT_VALUES["stop"])
    return [
        *build_prepare_steps(),
        SequenceStep(payload, PRESET_SETTLE_SECONDS),
        SequenceStep(stop_payload, REPEAT_INTERVAL_SECONDS),
        SequenceStep(stop_payload, REPEAT_INTERVAL_SECONDS),
        SequenceStep(stop_payload, 0.0),
    ]


def build_hold_steps(
    action: str,
    duration: float = DEFAULT_HOLD_SECONDS,
    interval: float = REPEAT_INTERVAL_SECONDS,
) -> list[SequenceStep]:
    payload = build_instruct_payload(INSTRUCT_VALUES[action])
    stop_payload = build_instruct_payload(INSTRUCT_VALUES["stop"])
    repeats = max(1, round(duration / interval))
    steps = [*build_prepare_steps()]
    steps.extend(SequenceStep(payload, interval) for _ in range(repeats))
    steps.append(SequenceStep(stop_payload, 0.0))
    return steps


def decode_notification(data: bytes) -> dict[str, object]:
    decoded: dict[str, object] = {
        "notification_type": "raw",
        "notification_length": len(data),
    }

    if data == bytes.fromhex("8e03010a0063"):
        decoded["notification_type"] = "heartbeat"
        return decoded

    if len(data) >= 15 and data[:4] == bytes.fromhex("ddee0886"):
        token = data[9:12]
        decoded.update(
            {
                "notification_type": "token",
                "token": token.hex(" "),
                "token_counter": token[2],
            }
        )
        return decoded

    if len(data) >= 13 and data[:4] == bytes.fromhex("ddee0693"):
        decoded.update(
            {
                "notification_type": "light_state",
                "light_enabled": bool(data[9]),
                "light_level": int(data[10]),
            }
        )
        return decoded

    if len(data) >= 19 and data[:5] == bytes.fromhex("ddee0c0120"):
        decoded.update(
            {
                "notification_type": "massage_state",
                "massage_frame": data.hex(" "),
                "massage_timer_minutes": int(data[5]),
                "massage_head_active": bool(data[8]),
                "massage_foot_active": bool(data[9]),
            }
        )
        return decoded

    if len(data) >= 6 and data[1:4] == bytes.fromhex("990200"):
        decoded.update(
            {
                "notification_type": "snapshot",
                "snapshot_counter": int(data[4]),
            }
        )
        return decoded

    if len(data) >= 17 and data[0] == 0x8A:
        decoded.update(
            {
                "notification_type": "status_ack",
                "status_frame": data.hex(" "),
            }
        )
        return decoded

    if len(data) >= 22 and data[0] == 0x91:
        decoded.update(
            {
                "notification_type": "extended_status",
                "extended_status_frame": data.hex(" "),
                "extended_status_code": int(data[17]),
            }
        )
        return decoded

    if len(data) >= 3 and data[0] == 0x88:
        decoded["notification_type"] = "safety_frame"
        return decoded

    return decoded


def inferred_action_state(action: str) -> dict[str, object]:
    updates: dict[str, object] = {}
    if action in PRESET_LABELS:
        updates["preset"] = PRESET_LABELS[action]
    if action in MASSAGE_LABELS:
        updates["massage_mode"] = MASSAGE_LABELS[action]
    return updates

