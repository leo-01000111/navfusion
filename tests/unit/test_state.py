from __future__ import annotations

import numpy as np

from navfusion.core.state import (
    NavState,
    apply_error_state,
    normalize_quaternion,
    quaternion_to_rotation_matrix,
)


def test_normalize_quaternion_unit_norm() -> None:
    q = np.array([2.0, 0.0, 0.0, 0.0], dtype=np.float64)
    qn = normalize_quaternion(q)
    assert np.isclose(np.linalg.norm(qn), 1.0)


def test_apply_error_state_updates_position_velocity_and_biases() -> None:
    state = NavState.zeros(timestamp_ns=0)
    dx = np.zeros(15, dtype=np.float64)
    dx[0:3] = np.array([1.0, -2.0, 0.5], dtype=np.float64)
    dx[3:6] = np.array([0.1, 0.2, -0.3], dtype=np.float64)
    dx[9:12] = np.array([0.01, -0.02, 0.03], dtype=np.float64)
    dx[12:15] = np.array([-0.1, 0.2, 0.0], dtype=np.float64)

    updated = apply_error_state(state, dx)

    assert np.allclose(updated.position_m, dx[0:3])
    assert np.allclose(updated.velocity_mps, dx[3:6])
    assert np.allclose(updated.gyro_bias_rps, dx[9:12])
    assert np.allclose(updated.accel_bias_mps2, dx[12:15])


def test_rotation_matrix_is_orthonormal() -> None:
    q = np.array([0.9238795, 0.0, 0.0, 0.3826834], dtype=np.float64)
    rot = quaternion_to_rotation_matrix(q)
    ident = rot @ rot.T
    assert np.allclose(ident, np.eye(3), atol=1e-6)
