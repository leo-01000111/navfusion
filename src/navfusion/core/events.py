"""Canonical event definitions for fusion processing."""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from typing import Literal

import numpy as np
from numpy.typing import NDArray

SensorType = Literal["imu", "gnss"]


@dataclass(frozen=True)
class MeasurementEvent:
    """Canonical sensor event with timestamp and covariance metadata."""

    timestamp_ns: int
    sensor_type: SensorType
    payload: Mapping[str, NDArray[np.float64]]
    R: NDArray[np.float64] | None = None
    frame_id: str = "world"
    sequence_id: int = 0

    def with_sequence(self, sequence_id: int) -> MeasurementEvent:
        return MeasurementEvent(
            timestamp_ns=self.timestamp_ns,
            sensor_type=self.sensor_type,
            payload=self.payload,
            R=self.R,
            frame_id=self.frame_id,
            sequence_id=sequence_id,
        )
