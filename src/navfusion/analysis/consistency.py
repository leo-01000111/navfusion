"""Consistency metrics for estimator health checks (NIS/NEES)."""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass

import numpy as np
from numpy.typing import NDArray
from scipy.linalg import cho_factor, cho_solve
from scipy.stats import chi2

from navfusion.results import RunResult, StateRecord, UpdateRecord
from navfusion.simulation import TruthSample


@dataclass(frozen=True)
class ConsistencyReport:
    metric: str
    dof: int
    sample_count: int
    mean_value: float
    lower_95: float
    upper_95: float

    @property
    def within_95_bounds(self) -> bool:
        return self.lower_95 <= self.mean_value <= self.upper_95


def nis_report(
    result: RunResult,
    sensor_type: str = "gnss",
    dof: int = 6,
    alpha: float = 0.05,
) -> ConsistencyReport:
    samples = [
        update.mahalanobis
        for update in result.update_history
        if _use_update_for_nis(update, sensor_type=sensor_type)
    ]
    return _build_report(metric=f"NIS({sensor_type})", samples=samples, dof=dof, alpha=alpha)


def nees_position_velocity_report(
    result: RunResult,
    truth: Sequence[TruthSample],
    alpha: float = 0.05,
) -> ConsistencyReport:
    truth_by_timestamp = {sample.timestamp_ns: sample for sample in truth}
    latest_state_by_timestamp: dict[int, StateRecord] = {}
    for state in result.state_history:
        latest_state_by_timestamp[state.timestamp_ns] = state

    samples: list[float] = []
    for timestamp_ns, state in latest_state_by_timestamp.items():
        truth_sample = truth_by_timestamp.get(timestamp_ns)
        if truth_sample is None:
            continue

        err = np.concatenate(
            [
                state.position_m - truth_sample.position_m,
                state.velocity_mps - truth_sample.velocity_mps,
            ]
        ).astype(np.float64)
        cov = state.covariance[0:6, 0:6]
        samples.append(_mahalanobis(err, cov))

    return _build_report(metric="NEES(pos+vel)", samples=samples, dof=6, alpha=alpha)


def _use_update_for_nis(update: UpdateRecord, sensor_type: str) -> bool:
    if update.sensor_type != sensor_type:
        return False
    if not update.accepted:
        return False
    return bool(np.isfinite(update.mahalanobis))


def _mahalanobis(error: NDArray[np.float64], cov: NDArray[np.float64]) -> float:
    cov_sym = 0.5 * (cov + cov.T)
    jitter = 1e-9
    stabilized = cov_sym + jitter * np.eye(cov_sym.shape[0], dtype=np.float64)

    factor, lower = cho_factor(stabilized, check_finite=True)
    solved = cho_solve((factor, lower), error)
    return float(error.T @ solved)


def _build_report(
    metric: str,
    samples: Sequence[float],
    dof: int,
    alpha: float,
) -> ConsistencyReport:
    if dof <= 0:
        raise ValueError("dof must be positive")

    finite_samples = [float(value) for value in samples if np.isfinite(value)]
    n = len(finite_samples)
    if n == 0:
        raise ValueError(f"No valid samples available for {metric}")

    total_dof = dof * n
    lower = float(chi2.ppf(alpha / 2.0, total_dof) / n)
    upper = float(chi2.ppf(1.0 - alpha / 2.0, total_dof) / n)
    mean_value = float(np.mean(np.asarray(finite_samples, dtype=np.float64)))

    return ConsistencyReport(
        metric=metric,
        dof=dof,
        sample_count=n,
        mean_value=mean_value,
        lower_95=lower,
        upper_95=upper,
    )
