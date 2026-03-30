"""Filter comparison metrics (accuracy, consistency, throughput helpers)."""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass

import numpy as np

from navfusion.analysis.consistency import nees_position_velocity_report, nis_report
from navfusion.results import RunResult, StateRecord
from navfusion.simulation import TruthSample


@dataclass(frozen=True)
class FilterPerformanceReport:
    rmse_position_m: float
    rmse_velocity_mps: float
    anis_mean: float
    anis_samples: int
    anees_mean: float
    anees_samples: int


def summarize_filter_performance(
    result: RunResult,
    truth: Sequence[TruthSample],
) -> FilterPerformanceReport:
    pairs = _align_by_timestamp(result, truth)
    if not pairs:
        raise ValueError("No aligned state/truth samples available for performance summary")

    pos_error_sq = []
    vel_error_sq = []
    for state, truth_sample in pairs:
        pos_err = state.position_m - truth_sample.position_m
        vel_err = state.velocity_mps - truth_sample.velocity_mps
        pos_error_sq.append(float(np.dot(pos_err, pos_err)))
        vel_error_sq.append(float(np.dot(vel_err, vel_err)))

    rmse_position = float(np.sqrt(np.mean(np.asarray(pos_error_sq, dtype=np.float64))))
    rmse_velocity = float(np.sqrt(np.mean(np.asarray(vel_error_sq, dtype=np.float64))))

    nis = nis_report(result)
    nees = nees_position_velocity_report(result, truth)

    return FilterPerformanceReport(
        rmse_position_m=rmse_position,
        rmse_velocity_mps=rmse_velocity,
        anis_mean=nis.mean_value,
        anis_samples=nis.sample_count,
        anees_mean=nees.mean_value,
        anees_samples=nees.sample_count,
    )


def _align_by_timestamp(
    result: RunResult,
    truth: Sequence[TruthSample],
) -> list[tuple[StateRecord, TruthSample]]:
    latest_state_by_timestamp: dict[int, StateRecord] = {}
    for state_record in result.state_history:
        latest_state_by_timestamp[state_record.timestamp_ns] = state_record

    pairs: list[tuple[StateRecord, TruthSample]] = []
    for truth_sample in truth:
        aligned_state = latest_state_by_timestamp.get(truth_sample.timestamp_ns)
        if aligned_state is None:
            continue
        pairs.append((aligned_state, truth_sample))
    return pairs
