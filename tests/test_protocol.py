from custom_components.ergomotion_ksbt.protocol import (
    build_instruct_payload,
    build_light_query_payload,
    build_query_alarm_payload,
    decode_notification,
)


def test_build_query_alarm_payload() -> None:
    assert build_query_alarm_payload() == b"7102060680"


def test_build_light_query_payload() -> None:
    assert build_light_query_payload().hex() == "aa01000901210000020000d155"


def test_build_instruct_payload_for_back_up() -> None:
    assert build_instruct_payload(1).hex() == "aa03000a00040101000000f9f355"


def test_build_instruct_payload_for_flat() -> None:
    assert build_instruct_payload(134217728).hex() == "aa03000a00040100000008f2f355"


def test_decode_light_notification() -> None:
    decoded = decode_notification(bytes.fromhex("dd ee 06 93 00 00 02 00 00 01 64 ee dd"))
    assert decoded["notification_type"] == "light_state"
    assert decoded["light_enabled"] is True
    assert decoded["light_level"] == 100


def test_decode_token_notification() -> None:
    decoded = decode_notification(bytes.fromhex("dd ee 08 86 14 1a 03 09 01 0d 26 00 03 ee dd"))
    assert decoded["notification_type"] == "token"
    assert decoded["token"] == "0d 26 00"


def test_decode_massage_notification() -> None:
    decoded = decode_notification(bytes.fromhex("dd ee 0c 01 20 0a 00 00 01 00 54 ea 00 00 02 01 86 ee dd"))
    assert decoded["notification_type"] == "massage_state"
    assert decoded["massage_timer_minutes"] == 10
    assert decoded["massage_head_active"] is True
    assert decoded["massage_foot_active"] is False
