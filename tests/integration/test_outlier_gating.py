from __future__ import annotations

from navfusion.api import run_replay
from navfusion.config import FusionConfig, GateConfig
from navfusion.simulation import generate_imu_gnss_scenario


def test_outlier_gating_rejects_measurements() -> None:
    events, _ = generate_imu_gnss_scenario(
        duration_s=30.0,
        seed=17,
        gnss_outlier_times_s=[10.0, 14.0, 18.0],
    )

    config = FusionConfig(gate=GateConfig(enabled=True, threshold=12.592))
    result = run_replay(events, config=config)

    assert result.summary.rejected_updates > 0
    assert result.summary.accepted_updates > 0
