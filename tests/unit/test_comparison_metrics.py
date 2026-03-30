from __future__ import annotations

import numpy as np

from navfusion.analysis import summarize_filter_performance
from navfusion.api import run_replay
from navfusion.simulation import generate_imu_gnss_scenario


def test_summarize_filter_performance_returns_finite_metrics() -> None:
    events, truth = generate_imu_gnss_scenario(duration_s=20.0, seed=53)
    result = run_replay(events)

    report = summarize_filter_performance(result, truth)

    assert report.rmse_position_m > 0.0
    assert report.rmse_velocity_mps > 0.0
    assert report.anis_samples > 0
    assert report.anees_samples > 0
    assert np.isfinite(report.anis_mean)
    assert np.isfinite(report.anees_mean)
