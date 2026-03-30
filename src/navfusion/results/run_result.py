"""Run diagnostics and immutable result containers."""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np
from numpy.typing import NDArray

from navfusion.core.state import NavState

Vec = NDArray[np.float64]
Mat = NDArray[np.float64]


@dataclass(frozen=True)
class StateRecord:
    timestamp_ns: int
    position_m: Vec
    velocity_mps: Vec
    attitude_wxyz: Vec
    covariance: Mat
    covariance_trace: float
    degraded: bool


@dataclass(frozen=True)
class PredictRecord:
    timestamp_ns: int
    dt_s: float
    covariance_trace: float


@dataclass(frozen=True)
class UpdateRecord:
    timestamp_ns: int
    sensor_type: str
    accepted: bool
    innovation_norm: float
    mahalanobis: float
    reason: str


@dataclass(frozen=True)
class RunSummary:
    total_events: int
    imu_events: int
    gnss_events: int
    accepted_updates: int
    rejected_updates: int
    late_dropped_events: int
    final_covariance_trace: float


@dataclass(frozen=True)
class RunResult:
    state_history: tuple[StateRecord, ...]
    predict_history: tuple[PredictRecord, ...]
    update_history: tuple[UpdateRecord, ...]
    summary: RunSummary

    def final_state(self) -> StateRecord:
        if not self.state_history:
            raise ValueError("No states were recorded")
        return self.state_history[-1]

    def trajectory_xyz(self) -> NDArray[np.float64]:
        if not self.state_history:
            return np.empty((0, 3), dtype=np.float64)
        return np.stack([entry.position_m for entry in self.state_history], axis=0)


def state_record_from_nav_state(
    state: NavState,
    covariance: Mat,
    covariance_trace: float,
    degraded: bool,
) -> StateRecord:
    return StateRecord(
        timestamp_ns=state.timestamp_ns,
        position_m=state.position_m.copy(),
        velocity_mps=state.velocity_mps.copy(),
        attitude_wxyz=state.attitude_wxyz.copy(),
        covariance=covariance.copy(),
        covariance_trace=covariance_trace,
        degraded=degraded,
    )
