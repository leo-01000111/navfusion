from __future__ import annotations

import numpy as np

from navfusion.api import run_replay
from navfusion.config import FusionConfig
from navfusion.simulation import generate_imu_gnss_scenario


def test_replay_pipeline_runs_with_ukf() -> None:
    events, _truth = generate_imu_gnss_scenario(duration_s=20.0, seed=41)
    result = run_replay(events, config=FusionConfig(filter_type="ukf"))

    assert result.summary.total_events > 0
    assert result.summary.accepted_updates > 0
    assert result.summary.rejected_updates >= 0

    final = result.final_state()
    assert np.all(np.isfinite(final.position_m))
    assert np.all(np.isfinite(final.velocity_mps))
