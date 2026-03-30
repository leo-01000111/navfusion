"""Simple replay throughput benchmark."""

from __future__ import annotations

import time

from navfusion.api import run_replay
from navfusion.simulation import generate_imu_gnss_scenario


def main() -> None:
    durations = [30.0, 120.0, 300.0]
    for duration in durations:
        events, _truth = generate_imu_gnss_scenario(duration_s=duration)
        start = time.perf_counter()
        result = run_replay(events)
        elapsed = time.perf_counter() - start
        eps = result.summary.total_events / elapsed if elapsed > 0 else 0.0
        print(
            f"duration={duration:6.1f}s events={result.summary.total_events:6d} "
            f"elapsed={elapsed:7.3f}s throughput={eps:9.1f} events/s"
        )


if __name__ == "__main__":
    main()
