"""Demo: IMU+GNSS fusion with GNSS dropout intervals."""

from __future__ import annotations

from navfusion.analysis import nees_position_velocity_report
from navfusion.api import run_replay
from navfusion.config import FusionConfig
from navfusion.simulation import generate_imu_gnss_scenario


def main() -> None:
    events, truth = generate_imu_gnss_scenario(
        duration_s=90.0,
        dropout_windows_s=[(20.0, 35.0), (55.0, 70.0)],
    )

    config = FusionConfig()
    result = run_replay(events, config=config)
    nees = nees_position_velocity_report(result, truth)

    print("Summary:", result.summary)
    print("Total states:", len(result.state_history))
    print("Total updates:", len(result.update_history))
    print(
        f"ANEES(pos+vel)={nees.mean_value:.3f} "
        f"(95% bounds [{nees.lower_95:.3f}, {nees.upper_95:.3f}], n={nees.sample_count})"
    )


if __name__ == "__main__":
    main()
