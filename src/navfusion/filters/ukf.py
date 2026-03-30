"""Unscented Kalman Filter implementation for IMU + GNSS fusion."""

from __future__ import annotations

from collections.abc import Mapping
from typing import cast

import numpy as np
from numpy.typing import NDArray
from scipy.linalg import cho_factor, cho_solve

from navfusion.config import UKFConfig
from navfusion.core.events import MeasurementEvent
from navfusion.core.state import STATE_SPEC, GaussianBelief, apply_error_state
from navfusion.models.measurement import MeasurementModel, compute_innovation_stats
from navfusion.models.motion import IMUInput, IMUKinematicsModel
from navfusion.results import PredictRecord, UpdateRecord
from navfusion.validation import require_covariance


class UnscentedKalmanFilter:
    """UKF backend using sigma-point measurement updates and shared motion propagation."""

    def __init__(
        self,
        belief: GaussianBelief,
        motion_model: IMUKinematicsModel,
        measurement_models: Mapping[str, MeasurementModel],
        gate_enabled: bool,
        gate_threshold: float,
        ukf_config: UKFConfig,
    ) -> None:
        self._belief = belief
        self._motion_model = motion_model
        self._measurement_models = dict(measurement_models)
        self._gate_enabled = gate_enabled
        self._gate_threshold = gate_threshold
        self._alpha = ukf_config.alpha
        self._beta = ukf_config.beta
        self._kappa = ukf_config.kappa

        self._n = STATE_SPEC.error_size
        self._lambda = self._alpha * self._alpha * (self._n + self._kappa) - self._n
        self._scaling = self._n + self._lambda
        if self._scaling <= 0.0:
            raise ValueError("UKF scaling must be positive; adjust alpha/kappa")

        self._weights_mean, self._weights_cov = self._build_weights()

    @property
    def belief(self) -> GaussianBelief:
        return self._belief

    def predict(self, timestamp_ns: int, imu: IMUInput) -> PredictRecord:
        # Reuse the same physically grounded motion propagation as EKF for v1.
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
        r_mat = event.R.copy() if event.R is not None else model.covariance()
        require_covariance("measurement covariance", r_mat, model.dimension)

        sigma_deltas = self._sigma_deltas(self._belief.covariance)
        sigma_states = [apply_error_state(self._belief.state, delta) for delta in sigma_deltas]
        sigma_meas = np.stack([model.measurement(state) for state in sigma_states], axis=0)

        z_mean = np.sum(self._weights_mean[:, None] * sigma_meas, axis=0)
        innovations = sigma_meas - z_mean

        innovation_cov = np.zeros((model.dimension, model.dimension), dtype=np.float64)
        for idx in range(sigma_deltas.shape[0]):
            innovation_cov += self._weights_cov[idx] * np.outer(innovations[idx], innovations[idx])
        innovation_cov += r_mat

        residual = z - z_mean
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

        cross_cov = np.zeros((self._n, model.dimension), dtype=np.float64)
        for idx in range(sigma_deltas.shape[0]):
            cross_cov += self._weights_cov[idx] * np.outer(sigma_deltas[idx], innovations[idx])

        kalman_gain = self._kalman_gain(cross_cov, innovation_cov)
        delta_x = kalman_gain @ residual

        updated_state = apply_error_state(self._belief.state, delta_x)
        updated_state.timestamp_ns = event.timestamp_ns

        cov_updated = self._belief.covariance - kalman_gain @ innovation_cov @ kalman_gain.T
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

    def _build_weights(self) -> tuple[NDArray[np.float64], NDArray[np.float64]]:
        num_sigma = 2 * self._n + 1
        weights_mean = np.full(num_sigma, 1.0 / (2.0 * self._scaling), dtype=np.float64)
        weights_cov = weights_mean.copy()
        weights_mean[0] = self._lambda / self._scaling
        weights_cov[0] = weights_mean[0] + (1.0 - self._alpha * self._alpha + self._beta)
        return weights_mean, weights_cov

    def _sigma_deltas(self, cov: NDArray[np.float64]) -> NDArray[np.float64]:
        chol = self._chol_with_jitter(cov * self._scaling)
        sigma = np.zeros((2 * self._n + 1, self._n), dtype=np.float64)
        sigma[1 : self._n + 1, :] = chol.T
        sigma[self._n + 1 :, :] = -chol.T
        return sigma

    def _chol_with_jitter(self, cov: NDArray[np.float64]) -> NDArray[np.float64]:
        cov_sym = 0.5 * (cov + cov.T)
        jitter = 1e-10
        for _ in range(6):
            try:
                return np.linalg.cholesky(cov_sym + jitter * np.eye(self._n, dtype=np.float64))
            except np.linalg.LinAlgError:
                jitter *= 10.0
        raise ValueError("Covariance is not positive definite even with jitter")

    def _kalman_gain(
        self,
        cross_cov: NDArray[np.float64],
        innovation_cov: NDArray[np.float64],
    ) -> NDArray[np.float64]:
        factor, lower = cho_factor(innovation_cov, check_finite=True)
        gain_t = cast(NDArray[np.float64], cho_solve((factor, lower), cross_cov.T))
        return gain_t.T
