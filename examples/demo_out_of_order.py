"""Demo: asynchronous delayed/out-of-order GNSS packets."""

from __future__ import annotations

from navfusion.api import run_replay
from navfusion.config import EngineConfig, FusionConfig
from navfusion.simulation import generate_imu_gnss_scenario


def make_out_of_order(events):
    shifted = list(events)
    gnss_indices = [idx for idx, event in enumerate(shifted) if event.sensor_type == "gnss"]
    if len(gnss_indices) < 6:
        return shifted

    idx = gnss_indices[3]
    event = shifted.pop(idx)
    insert_at = min(len(shifted), idx + 120)
    shifted.insert(insert_at, event)

    idx2 = gnss_indices[5]
    event2 = shifted.pop(idx2)
    insert_at2 = min(len(shifted), idx2 + 600)
    shifted.insert(insert_at2, event2)
    return shifted


def main() -> None:
    events, _truth = generate_imu_gnss_scenario(duration_s=45.0)
    events = make_out_of_order(events)

    config = FusionConfig(engine=EngineConfig(reorder_window_ns=300_000_000, degrade_after_s=2.0))
    result = run_replay(events, config=config)

    print("Summary:", result.summary)


if __name__ == "__main__":
    main()
