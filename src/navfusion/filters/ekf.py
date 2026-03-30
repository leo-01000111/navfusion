"""Error-state EKF implementation for IMU + GNSS fusion."""

from __future__ import annotations

from collections.abc import Mapping
from typing import cast

import numpy as np
from numpy.typing import NDArray
from scipy.linalg import cho_factor, cho_solve

from navfusion.core.events import MeasurementEvent
from navfusion.core.state import STATE_SPEC, GaussianBelief, apply_error_state
from navfusion.models.measurement import MeasurementModel, compute_innovation_stats
from navfusion.models.motion import IMUInput, IMUKinematicsModel
from navfusion.results import PredictRecord, UpdateRecord
from navfusion.validation import require_covariance


class ErrorStateEKF:
    """v1 EKF implementation with generic measurement-model dispatch."""

    def __init__(
        self,
        belief: GaussianBelief,
        motion_model: IMUKinematicsModel,
        measurement_models: Mapping[str, MeasurementModel],
        gate_enabled: bool,
        gate_threshold: float,
    ) -> None:
        self._belief = belief
        self._motion_model = motion_model
        self._measurement_models = dict(measurement_models)
        self._gate_enabled = gate_enabled
        self._gate_threshold = gate_threshold

    @property
    def belief(self) -> GaussianBelief:
        return self._belief

    def predict(self, timestamp_ns: int, imu: IMUInput) -> PredictRecord:
        motion_step = self._motion_model.propagate(self._belief, timestamp_ns, imu)
        self._belief = motion_step.propagated_belief
        cov_trace = float(np.trace(self._belief.covariance))
        return PredictRecord(
            timestamp_ns=timestamp_ns,
            dt_s=motion_step.dt_s,
            covariance_trace=cov_trace,
        )

    def update(self, event: MeasurementEvent) -> UpdateRecord:
        model = self._measurement_models.get(event.sensor_type)
        if model is None:
            return UpdateRecord(
                timestamp_ns=event.timestamp_ns,
                sensor_type=event.sensor_type,
                accepted=False,
                innovation_norm=0.0,
                mahalanobis=0.0,
                reason="unsupported_sensor",
            )

        if self._belief.state.timestamp_ns != event.timestamp_ns:
            return UpdateRecord(
                timestamp_ns=event.timestamp_ns,
                sensor_type=event.sensor_type,
                accepted=False,
                innovation_norm=0.0,
                mahalanobis=0.0,
                reason="timestamp_mismatch",
            )

        z = model.extract_measurement(event.payload)
        z_hat = model.measurement(self._belief.state)
        residual = z - z_hat

        h_mat = model.jacobian(self._belief.state)
        r_mat = event.R.copy() if event.R is not None else model.covariance()
        require_covariance("measurement covariance", r_mat, model.dimension)

        innovation_cov = h_mat @ self._belief.covariance @ h_mat.T + r_mat
        innovation_stats = compute_innovation_stats(residual, innovation_cov)

        if self._gate_enabled and innovation_stats.mahalanobis > self._gate_threshold:
            return UpdateRecord(
                timestamp_ns=event.timestamp_ns,
                sensor_type=event.sensor_type,
                accepted=False,
                innovation_norm=float(np.linalg.norm(residual)),
                mahalanobis=innovation_stats.mahalanobis,
                reason="gate_reject",
            )

        kalman_gain = self._compute_kalman_gain(self._belief.covariance, h_mat, innovation_cov)
        delta_x = kalman_gain @ residual

        updated_state = apply_error_state(self._belief.state, delta_x)
        updated_state.timestamp_ns = event.timestamp_ns

        identity = np.eye(STATE_SPEC.error_size, dtype=np.float64)
        kh = kalman_gain @ h_mat
        cov = self._belief.covariance
        cov_updated = (
            (identity - kh) @ cov @ (identity - kh).T + kalman_gain @ r_mat @ kalman_gain.T
        )
        cov_updated = 0.5 * (cov_updated + cov_updated.T)

        self._belief = GaussianBelief(
            state=updated_state,
            covariance=cov_updated,
            degraded=self._belief.degraded,
        )

        return UpdateRecord(
            timestamp_ns=event.timestamp_ns,
            sensor_type=event.sensor_type,
            accepted=True,
            innovation_norm=float(np.linalg.norm(residual)),
            mahalanobis=innovation_stats.mahalanobis,
            reason="accepted",
        )

    def _compute_kalman_gain(
        self,
        cov: NDArray[np.float64],
        h_mat: NDArray[np.float64],
        innovation_cov: NDArray[np.float64],
    ) -> NDArray[np.float64]:
        factor, lower = cho_factor(innovation_cov, check_finite=True)
        cross = cov @ h_mat.T
        gain_t = cast(NDArray[np.float64], cho_solve((factor, lower), cross.T))
        return gain_t.T
