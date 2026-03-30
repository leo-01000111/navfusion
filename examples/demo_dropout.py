"""Demo: IMU+GNSS fusion with GNSS dropout intervals."""

from __future__ import annotations

from navfusion.api import run_replay
from navfusion.config import FusionConfig
from navfusion.simulation import generate_imu_gnss_scenario


def main() -> None:
    events, _truth = generate_imu_gnss_scenario(
        duration_s=90.0,
        dropout_windows_s=[(20.0, 35.0), (55.0, 70.0)],
    )

    config = FusionConfig()
    result = run_replay(events, config=config)

    print("Summary:", result.summary)
    print("Total states:", len(result.state_history))
    print("Total updates:", len(result.update_history))


if __name__ == "__main__":
    main()
