from __future__ import annotations

import numpy as np

from navfusion.api import run_replay
from navfusion.simulation import generate_imu_gnss_scenario


def test_replay_is_deterministic_for_same_events() -> None:
    events, _ = generate_imu_gnss_scenario(duration_s=15.0, seed=23)
    result_a = run_replay(events)
    result_b = run_replay(events)

    assert result_a.summary == result_b.summary
    assert np.allclose(result_a.final_state().position_m, result_b.final_state().position_m)
