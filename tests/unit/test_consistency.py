from __future__ import annotations

import numpy as np
import pytest

from navfusion.analysis import nees_position_velocity_report, nis_report
from navfusion.api import run_replay
from navfusion.results import RunResult
from navfusion.simulation import generate_imu_gnss_scenario


def test_nis_report_has_expected_shape() -> None:
    events, _truth = generate_imu_gnss_scenario(duration_s=30.0, seed=19)
    result = run_replay(events)

    report = nis_report(result)

    assert report.metric == "NIS(gnss)"
    assert report.sample_count > 0
    assert report.mean_value > 0.0
    assert report.upper_95 > report.lower_95


def test_nees_report_has_expected_shape() -> None:
    events, truth = generate_imu_gnss_scenario(duration_s=30.0, seed=23)
    result = run_replay(events)

    report = nees_position_velocity_report(result, truth)

    assert report.metric == "NEES(pos+vel)"
    assert report.sample_count > 0
    assert report.mean_value > 0.0
    assert np.isfinite(report.mean_value)


def test_nis_report_raises_if_no_updates() -> None:
    empty_result = RunResult(
        state_history=tuple(),
        predict_history=tuple(),
        update_history=tuple(),
        summary=run_replay([]).summary,
    )

    with pytest.raises(ValueError):
        _ = nis_report(empty_result)
