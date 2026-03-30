from __future__ import annotations

import numpy as np

from navfusion.core.events import MeasurementEvent
from navfusion.sensors import GNSSSensorAdapter, IMUSensorAdapter


def test_imu_adapter_emits_canonical_event() -> None:
    adapter = IMUSensorAdapter(timestamp_unit="s")
    event = adapter.to_event(
        {
            "timestamp": 1.5,
            "angular_velocity_rps": [0.1, 0.0, 0.0],
            "linear_acceleration_mps2": [0.0, 0.0, 9.8],
        },
        sequence_id=12,
    )

    assert isinstance(event, MeasurementEvent)
    assert event.timestamp_ns == 1_500_000_000
    assert event.sensor_type == "imu"
    assert np.asarray(event.payload["angular_velocity_rps"]).shape == (3,)


def test_gnss_adapter_emits_canonical_event() -> None:
    adapter = GNSSSensorAdapter(timestamp_unit="ms")
    event = adapter.to_event(
        {
            "timestamp": 2500.0,
            "position_m": [1.0, 2.0, 3.0],
            "velocity_mps": [0.1, 0.2, 0.3],
        },
        sequence_id=3,
    )

    assert isinstance(event, MeasurementEvent)
    assert event.timestamp_ns == 2_500_000_000
    assert event.sensor_type == "gnss"
    assert np.asarray(event.payload["position_m"]).shape == (3,)
