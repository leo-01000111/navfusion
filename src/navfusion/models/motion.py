"""Motion models for propagation using IMU data."""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np
from numpy.typing import NDArray

from navfusion.config import ProcessNoiseConfig
from navfusion.core.state import (
    STATE_SPEC,
    GaussianBelief,
    quaternion_from_small_angle,
    quaternion_multiply,
    quaternion_to_rotation_matrix,
    skew,
)
from navfusion.validation import require_error_covariance, require_finite, require_shape

Vec3 = NDArray[np.float64]


@dataclass(frozen=True)
class IMUInput:
    angular_velocity_rps: Vec3
    linear_acceleration_mps2: Vec3


@dataclass(frozen=True)
class MotionStep:
    dt_s: float
    propagated_belief: GaussianBelief


class IMUKinematicsModel:
    """Continuous-time IMU kinematics with first-order covariance discretization."""

    def __init__(self, process_noise: ProcessNoiseConfig, gravity_mps2: float = 9.80665) -> None:
        self._noise = process_noise
        self._gravity_world = np.array([0.0, 0.0, -gravity_mps2], dtype=np.float64)

    def propagate(
        self,
        belief: GaussianBelief,
        target_timestamp_ns: int,
        imu: IMUInput,
    ) -> MotionStep:
        state = belief.state.copy()
        cov = belief.covariance.copy()
        require_error_covariance(cov)
        require_shape("imu.angular_velocity_rps", imu.angular_velocity_rps, (3,))
        require_shape("imu.linear_acceleration_mps2", imu.linear_acceleration_mps2, (3,))
        require_finite("imu.angular_velocity_rps", imu.angular_velocity_rps)
        require_finite("imu.linear_acceleration_mps2", imu.linear_acceleration_mps2)

        if target_timestamp_ns < state.timestamp_ns:
            raise ValueError("target_timestamp_ns cannot be earlier than current state timestamp")

        dt_s = float(target_timestamp_ns - state.timestamp_ns) * 1e-9
        if dt_s <= 0.0:
            return MotionStep(dt_s=0.0, propagated_belief=belief.copy())

        omega_corr = imu.angular_velocity_rps - state.gyro_bias_rps
        accel_body_corr = imu.linear_acceleration_mps2 - state.accel_bias_mps2

        dq = quaternion_from_small_angle(omega_corr * dt_s)
        attitude_next = quaternion_multiply(state.attitude_wxyz, dq)

        rot_world_body = quaternion_to_rotation_matrix(state.attitude_wxyz)
        accel_world = rot_world_body @ accel_body_corr + self._gravity_world

        position_next = (
            state.position_m + state.velocity_mps * dt_s + 0.5 * accel_world * dt_s * dt_s
        )
        velocity_next = state.velocity_mps + accel_world * dt_s

        state.position_m = position_next
        state.velocity_mps = velocity_next
        state.attitude_wxyz = attitude_next
        state.timestamp_ns = target_timestamp_ns

        cov_next = self._propagate_covariance(
            cov,
            rot_world_body,
            accel_body_corr,
            omega_corr,
            dt_s,
        )

        return MotionStep(
            dt_s=dt_s,
            propagated_belief=GaussianBelief(
                state=state,
                covariance=cov_next,
                degraded=belief.degraded,
            ),
        )

    def _propagate_covariance(
        self,
        cov: NDArray[np.float64],
        rot_world_body: NDArray[np.float64],
        accel_body_corr: Vec3,
        omega_corr: Vec3,
        dt_s: float,
    ) -> NDArray[np.float64]:
        f_mat = np.zeros((STATE_SPEC.error_size, STATE_SPEC.error_size), dtype=np.float64)
        f_mat[STATE_SPEC.p, STATE_SPEC.v] = np.eye(3, dtype=np.float64)
        f_mat[STATE_SPEC.v, STATE_SPEC.theta] = -rot_world_body @ skew(accel_body_corr)
        f_mat[STATE_SPEC.v, STATE_SPEC.accel_bias] = -rot_world_body
        f_mat[STATE_SPEC.theta, STATE_SPEC.theta] = -skew(omega_corr)
        f_mat[STATE_SPEC.theta, STATE_SPEC.gyro_bias] = -np.eye(3, dtype=np.float64)

        g_mat = np.zeros((STATE_SPEC.error_size, 12), dtype=np.float64)
        g_mat[STATE_SPEC.v, 0:3] = rot_world_body
        g_mat[STATE_SPEC.theta, 3:6] = -np.eye(3, dtype=np.float64)
        g_mat[STATE_SPEC.gyro_bias, 6:9] = np.eye(3, dtype=np.float64)
        g_mat[STATE_SPEC.accel_bias, 9:12] = np.eye(3, dtype=np.float64)

        q_cont = np.diag(
            np.array(
                [
                    self._noise.accel_noise_std_mps2**2,
                    self._noise.accel_noise_std_mps2**2,
                    self._noise.accel_noise_std_mps2**2,
                    self._noise.gyro_noise_std_rps**2,
                    self._noise.gyro_noise_std_rps**2,
                    self._noise.gyro_noise_std_rps**2,
                    self._noise.gyro_bias_rw_std_rps**2,
                    self._noise.gyro_bias_rw_std_rps**2,
                    self._noise.gyro_bias_rw_std_rps**2,
                    self._noise.accel_bias_rw_std_mps2**2,
                    self._noise.accel_bias_rw_std_mps2**2,
                    self._noise.accel_bias_rw_std_mps2**2,
                ],
                dtype=np.float64,
            )
        )

        phi = np.eye(STATE_SPEC.error_size, dtype=np.float64) + f_mat * dt_s
        q_disc = (g_mat @ q_cont @ g_mat.T) * dt_s

        cov_next = phi @ cov @ phi.T + q_disc
        cov_next = 0.5 * (cov_next + cov_next.T)
        return cov_next


def zero_imu_input() -> IMUInput:
    return IMUInput(
        angular_velocity_rps=np.zeros(3, dtype=np.float64),
        linear_acceleration_mps2=np.zeros(3, dtype=np.float64),
    )
