"""Demo: GNSS outlier rejection via innovation gating."""

from __future__ import annotations

from navfusion.analysis import nis_report
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
    nis = nis_report(result)

    print("Summary:", result.summary)
    print("Update reasons:", summarize_update_reasons(result))
    print(
        f"ANIS={nis.mean_value:.3f} "
        f"(95% bounds [{nis.lower_95:.3f}, {nis.upper_95:.3f}], n={nis.sample_count})"
    )


if __name__ == "__main__":
    main()
