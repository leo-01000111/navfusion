from __future__ import annotations

from navfusion.api import run_replay
from navfusion.config import EngineConfig, FusionConfig
from navfusion.simulation import generate_imu_gnss_scenario


def _inject_delayed_gnss(events):
    modified = list(events)
    gnss_idxs = [idx for idx, event in enumerate(modified) if event.sensor_type == "gnss"]
    if len(gnss_idxs) < 5:
        return modified

    moved = modified.pop(gnss_idxs[2])
    modified.insert(min(len(modified), gnss_idxs[2] + 40), moved)

    moved2 = modified.pop(gnss_idxs[4])
    modified.append(moved2)
    return modified


def test_out_of_order_and_late_drop_behavior() -> None:
    events, _ = generate_imu_gnss_scenario(duration_s=20.0, seed=13)
    arrival = _inject_delayed_gnss(events)

    config = FusionConfig(engine=EngineConfig(reorder_window_ns=100_000_000, degrade_after_s=2.0))
    result = run_replay(arrival, config=config)

    assert result.summary.total_events > 0
    assert result.summary.late_dropped_events >= 1
