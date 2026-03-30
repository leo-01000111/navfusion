"""Sensor adapter interfaces."""

from __future__ import annotations

from typing import Protocol

from navfusion.core.events import MeasurementEvent


class SensorAdapter(Protocol):
    def to_event(self, raw: dict[str, object], sequence_id: int) -> MeasurementEvent:
        ...
