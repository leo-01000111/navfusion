"""GNSS raw packet adapter."""

from __future__ import annotations

import numpy as np

from navfusion.core.events import MeasurementEvent
from navfusion.core.time import TimestampUnit, to_timestamp_ns
from navfusion.validation import require_shape


class GNSSSensorAdapter:
    def __init__(self, timestamp_unit: TimestampUnit = "ns", frame_id: str = "world") -> None:
        self._unit = timestamp_unit
        self._frame_id = frame_id

    def to_event(self, raw: dict[str, object], sequence_id: int) -> MeasurementEvent:
        if "timestamp" not in raw:
            raise ValueError("GNSS raw packet missing timestamp")
        if "position_m" not in raw:
            raise ValueError("GNSS raw packet missing position_m")
        if "velocity_mps" not in raw:
            raise ValueError("GNSS raw packet missing velocity_mps")

        timestamp_value = raw["timestamp"]
        if not isinstance(timestamp_value, (int, float)):
            raise ValueError("GNSS timestamp must be int or float")
        timestamp_ns = to_timestamp_ns(float(timestamp_value), self._unit)
        position = np.asarray(raw["position_m"], dtype=np.float64)
        velocity = np.asarray(raw["velocity_mps"], dtype=np.float64)
        require_shape("raw.position_m", position, (3,))
        require_shape("raw.velocity_mps", velocity, (3,))

        r_cov = None
        if "R" in raw:
            r_cov = np.asarray(raw["R"], dtype=np.float64)

        return MeasurementEvent(
            timestamp_ns=timestamp_ns,
            sensor_type="gnss",
            payload={"position_m": position, "velocity_mps": velocity},
            R=r_cov,
            frame_id=self._frame_id,
            sequence_id=sequence_id,
        )
