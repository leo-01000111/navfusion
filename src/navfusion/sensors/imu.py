"""IMU raw packet adapter."""

from __future__ import annotations

import numpy as np

from navfusion.core.events import MeasurementEvent
from navfusion.core.time import TimestampUnit, to_timestamp_ns
from navfusion.validation import require_shape


class IMUSensorAdapter:
    def __init__(self, timestamp_unit: TimestampUnit = "ns", frame_id: str = "body") -> None:
        self._unit = timestamp_unit
        self._frame_id = frame_id

    def to_event(self, raw: dict[str, object], sequence_id: int) -> MeasurementEvent:
        if "timestamp" not in raw:
            raise ValueError("IMU raw packet missing timestamp")
        if "angular_velocity_rps" not in raw:
            raise ValueError("IMU raw packet missing angular_velocity_rps")
        if "linear_acceleration_mps2" not in raw:
            raise ValueError("IMU raw packet missing linear_acceleration_mps2")

        timestamp_value = raw["timestamp"]
        if not isinstance(timestamp_value, (int, float)):
            raise ValueError("IMU timestamp must be int or float")
        timestamp_ns = to_timestamp_ns(float(timestamp_value), self._unit)
        omega = np.asarray(raw["angular_velocity_rps"], dtype=np.float64)
        accel = np.asarray(raw["linear_acceleration_mps2"], dtype=np.float64)
        require_shape("raw.angular_velocity_rps", omega, (3,))
        require_shape("raw.linear_acceleration_mps2", accel, (3,))

        return MeasurementEvent(
            timestamp_ns=timestamp_ns,
            sensor_type="imu",
            payload={
                "angular_velocity_rps": omega,
                "linear_acceleration_mps2": accel,
            },
            frame_id=self._frame_id,
            sequence_id=sequence_id,
        )
