from __future__ import annotations

from navfusion.analysis import nees_position_velocity_report, nis_report
from navfusion.api import run_replay
from navfusion.simulation import generate_imu_gnss_scenario

# Thresholds are intentionally explicit and stable for CI.
MAX_ANIS = 12.5
MAX_ANEES_POS_VEL = 18.0
MIN_SAMPLES = 40


def test_consistency_thresholds_for_nominal_scenario() -> None:
    events, truth = generate_imu_gnss_scenario(duration_s=60.0, seed=31)
    result = run_replay(events)

    nis = nis_report(result, sensor_type="gnss", dof=6)
    nees = nees_position_velocity_report(result, truth)

    assert nis.sample_count >= MIN_SAMPLES
    assert nees.sample_count >= MIN_SAMPLES

    assert nis.mean_value <= MAX_ANIS
    assert nees.mean_value <= MAX_ANEES_POS_VEL
