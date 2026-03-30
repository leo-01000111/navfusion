"""State representation and quaternion math primitives."""

from __future__ import annotations

from dataclasses import dataclass, field

import numpy as np
from numpy.typing import NDArray

Vec3 = NDArray[np.float64]
Vec4 = NDArray[np.float64]
Mat15 = NDArray[np.float64]


@dataclass(frozen=True)
class StateSpec:
    """Canonical state layout for v1 error-state EKF."""

    error_size: int = 15
    p: slice = field(default_factory=lambda: slice(0, 3))
    v: slice = field(default_factory=lambda: slice(3, 6))
    theta: slice = field(default_factory=lambda: slice(6, 9))
    gyro_bias: slice = field(default_factory=lambda: slice(9, 12))
    accel_bias: slice = field(default_factory=lambda: slice(12, 15))


STATE_SPEC = StateSpec()


@dataclass
class NavState:
    """Nominal 3D navigation state in world frame (ENU-like, z-up)."""

    timestamp_ns: int
    position_m: Vec3
    velocity_mps: Vec3
    attitude_wxyz: Vec4
    gyro_bias_rps: Vec3
    accel_bias_mps2: Vec3

    @classmethod
    def zeros(cls, timestamp_ns: int = 0) -> NavState:
        return cls(
            timestamp_ns=timestamp_ns,
            position_m=np.zeros(3, dtype=np.float64),
            velocity_mps=np.zeros(3, dtype=np.float64),
            attitude_wxyz=np.array([1.0, 0.0, 0.0, 0.0], dtype=np.float64),
            gyro_bias_rps=np.zeros(3, dtype=np.float64),
            accel_bias_mps2=np.zeros(3, dtype=np.float64),
        )

    def copy(self) -> NavState:
        return NavState(
            timestamp_ns=self.timestamp_ns,
            position_m=self.position_m.copy(),
            velocity_mps=self.velocity_mps.copy(),
            attitude_wxyz=self.attitude_wxyz.copy(),
            gyro_bias_rps=self.gyro_bias_rps.copy(),
            accel_bias_mps2=self.accel_bias_mps2.copy(),
        )


@dataclass
class GaussianBelief:
    """Nominal state plus error covariance."""

    state: NavState
    covariance: Mat15
    degraded: bool = False

    def copy(self) -> GaussianBelief:
        return GaussianBelief(
            state=self.state.copy(),
            covariance=self.covariance.copy(),
            degraded=self.degraded,
        )


def normalize_quaternion(q_wxyz: Vec4) -> Vec4:
    norm = np.linalg.norm(q_wxyz)
    if norm <= 0.0:
        raise ValueError("Quaternion norm must be positive")
    return q_wxyz / norm


def quaternion_multiply(lhs_wxyz: Vec4, rhs_wxyz: Vec4) -> Vec4:
    w1, x1, y1, z1 = lhs_wxyz
    w2, x2, y2, z2 = rhs_wxyz
    out = np.array(
        [
            w1 * w2 - x1 * x2 - y1 * y2 - z1 * z2,
            w1 * x2 + x1 * w2 + y1 * z2 - z1 * y2,
            w1 * y2 - x1 * z2 + y1 * w2 + z1 * x2,
            w1 * z2 + x1 * y2 - y1 * x2 + z1 * w2,
        ],
        dtype=np.float64,
    )
    return normalize_quaternion(out)


def quaternion_from_small_angle(delta_theta: Vec3) -> Vec4:
    half = 0.5 * delta_theta
    squared = float(np.dot(half, half))
    w = np.sqrt(max(0.0, 1.0 - squared))
    return normalize_quaternion(np.array([w, half[0], half[1], half[2]], dtype=np.float64))


def quaternion_to_rotation_matrix(q_wxyz: Vec4) -> NDArray[np.float64]:
    q = normalize_quaternion(q_wxyz)
    w, x, y, z = q
    return np.array(
        [
            [1.0 - 2.0 * (y * y + z * z), 2.0 * (x * y - z * w), 2.0 * (x * z + y * w)],
            [2.0 * (x * y + z * w), 1.0 - 2.0 * (x * x + z * z), 2.0 * (y * z - x * w)],
            [2.0 * (x * z - y * w), 2.0 * (y * z + x * w), 1.0 - 2.0 * (x * x + y * y)],
        ],
        dtype=np.float64,
    )


def skew(v_xyz: Vec3) -> NDArray[np.float64]:
    vx, vy, vz = v_xyz
    return np.array(
        [
            [0.0, -vz, vy],
            [vz, 0.0, -vx],
            [-vy, vx, 0.0],
        ],
        dtype=np.float64,
    )


def apply_error_state(nominal: NavState, delta_x: NDArray[np.float64]) -> NavState:
    if delta_x.shape != (STATE_SPEC.error_size,):
        raise ValueError(f"delta_x must have shape ({STATE_SPEC.error_size},)")

    updated = nominal.copy()
    updated.position_m = updated.position_m + delta_x[STATE_SPEC.p]
    updated.velocity_mps = updated.velocity_mps + delta_x[STATE_SPEC.v]
    dq = quaternion_from_small_angle(delta_x[STATE_SPEC.theta])
    updated.attitude_wxyz = quaternion_multiply(updated.attitude_wxyz, dq)
    updated.gyro_bias_rps = updated.gyro_bias_rps + delta_x[STATE_SPEC.gyro_bias]
    updated.accel_bias_mps2 = updated.accel_bias_mps2 + delta_x[STATE_SPEC.accel_bias]
    return updated
