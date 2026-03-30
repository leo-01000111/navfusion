"""Demo: GNSS outlier rejection via innovation gating."""

from __future__ import annotations

from navfusion.api import run_replay
from navfusion.config import FusionConfig, GateConfig
from navfusion.simulation import generate_imu_gnss_scenario
from navfusion.viz import summarize_update_reasons


def main() -> None:
    events, _truth = generate_imu_gnss_scenario(
        duration_s=60.0,
        gnss_outlier_times_s=[12.0, 24.0, 37.0, 48.0],
    )

    config = FusionConfig(gate=GateConfig(enabled=True, threshold=16.812))
    result = run_replay(events, config=config)

    print("Summary:", result.summary)
    print("Update reasons:", summarize_update_reasons(result))


if __name__ == "__main__":
    main()
