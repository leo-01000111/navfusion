"""Measurement models and innovation utilities."""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from typing import Protocol, runtime_checkable

import numpy as np
from numpy.typing import NDArray
from scipy.linalg import cho_factor, cho_solve

from navfusion.config import GnssNoiseConfig
from navfusion.core.state import STATE_SPEC, NavState
from navfusion.validation import require_covariance, require_shape

Vec = NDArray[np.float64]
Mat = NDArray[np.float64]


@runtime_checkable
class MeasurementModel(Protocol):
    sensor_type: str
    dimension: int

    def measurement(self, state: NavState) -> Vec:
        ...

    def jacobian(self, state: NavState) -> Mat:
        ...

    def covariance(self) -> Mat:
        ...

    def extract_measurement(self, payload: Mapping[str, NDArray[np.float64]]) -> Vec:
        ...


@dataclass(frozen=True)
class InnovationStats:
    residual: Vec
    mahalanobis: float


class GNSSPositionVelocityModel:
    sensor_type = "gnss"
    dimension = 6

    def __init__(self, noise: GnssNoiseConfig) -> None:
        self._R = noise.covariance()

    def measurement(self, state: NavState) -> Vec:
        return np.concatenate([state.position_m, state.velocity_mps]).astype(np.float64)

    def jacobian(self, state: NavState) -> Mat:
        _ = state
        h_mat = np.zeros((self.dimension, STATE_SPEC.error_size), dtype=np.float64)
        h_mat[0:3, STATE_SPEC.p] = np.eye(3, dtype=np.float64)
        h_mat[3:6, STATE_SPEC.v] = np.eye(3, dtype=np.float64)
        return h_mat

    def covariance(self) -> Mat:
        return self._R.copy()

    def extract_measurement(self, payload: Mapping[str, NDArray[np.float64]]) -> Vec:
        if "position_m" not in payload:
            raise ValueError("GNSS payload missing position_m")
        if "velocity_mps" not in payload:
            raise ValueError("GNSS payload missing velocity_mps")

        pos = payload["position_m"].astype(np.float64)
        vel = payload["velocity_mps"].astype(np.float64)
        require_shape("gnss.position_m", pos, (3,))
        require_shape("gnss.velocity_mps", vel, (3,))
        return np.concatenate([pos, vel])


def compute_innovation_stats(
    residual: Vec,
    innovation_cov: Mat,
) -> InnovationStats:
    require_shape("residual", residual, (residual.shape[0],))
    require_covariance("innovation covariance", innovation_cov, residual.shape[0])

    factor, lower = cho_factor(innovation_cov, check_finite=True)
    solved = cho_solve((factor, lower), residual)
    mahal = float(residual.T @ solved)
    return InnovationStats(residual=residual, mahalanobis=mahal)
