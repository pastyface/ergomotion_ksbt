from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class ButtonActionDescription:
    key: str
    name: str
    icon: str


@dataclass(frozen=True)
class CoverActionDescription:
    key: str
    name: str
    icon: str
    open_action: str
    close_action: str
