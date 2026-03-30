from __future__ import annotations

import numpy as np

from navfusion.core.events import MeasurementEvent
from navfusion.core.time import EventReorderBuffer, to_timestamp_ns


def _imu_event(ts_ns: int, seq: int) -> MeasurementEvent:
    return MeasurementEvent(
        timestamp_ns=ts_ns,
        sensor_type="imu",
        payload={
            "angular_velocity_rps": np.zeros(3, dtype=np.float64),
            "linear_acceleration_mps2": np.zeros(3, dtype=np.float64),
        },
        sequence_id=seq,
    )


def test_to_timestamp_ns_conversions() -> None:
    assert to_timestamp_ns(1.5, "s") == 1_500_000_000
    assert to_timestamp_ns(1500, "ms") == 1_500_000_000
    assert to_timestamp_ns(1_500_000, "us") == 1_500_000_000


def test_reorder_buffer_emits_in_order_within_window() -> None:
    buffer: EventReorderBuffer[MeasurementEvent] = EventReorderBuffer(window_ns=100)
    assert buffer.push(_imu_event(1_000, 1))
    assert buffer.push(_imu_event(900, 2))
    ready = buffer.pop_ready()
    assert [event.timestamp_ns for event in ready] == [900]

    assert buffer.push(_imu_event(1_300, 3))
    ready2 = buffer.pop_ready()
    assert [event.timestamp_ns for event in ready2] == [1_000]

    remaining = buffer.flush()
    assert [event.timestamp_ns for event in remaining] == [1_300]


def test_reorder_buffer_drops_late_events() -> None:
    buffer: EventReorderBuffer[MeasurementEvent] = EventReorderBuffer(window_ns=50)
    assert buffer.push(_imu_event(1_000, 1))
    _ = buffer.flush()

    accepted = buffer.push(_imu_event(900, 2))
    assert not accepted
    assert buffer.stats.late_dropped == 1
