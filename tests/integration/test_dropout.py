from __future__ import annotations

from navfusion.api import run_replay
from navfusion.simulation import generate_imu_gnss_scenario


def test_dropout_scenario_keeps_running_with_fewer_gnss_updates() -> None:
    events_nominal, _ = generate_imu_gnss_scenario(duration_s=30.0, seed=11)
    events_dropout, _ = generate_imu_gnss_scenario(
        duration_s=30.0,
        seed=11,
        dropout_windows_s=[(8.0, 16.0)],
    )

    nominal = run_replay(events_nominal)
    dropout = run_replay(events_dropout)

    assert dropout.summary.gnss_events < nominal.summary.gnss_events
    assert len(dropout.state_history) > 0
    assert any(state.degraded for state in dropout.state_history)
