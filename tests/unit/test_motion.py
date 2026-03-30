from __future__ import annotations

import numpy as np

from navfusion.config import ProcessNoiseConfig
from navfusion.core.state import GaussianBelief, NavState
from navfusion.models.motion import IMUInput, IMUKinematicsModel


def test_motion_propagation_advances_time_and_covariance() -> None:
    model = IMUKinematicsModel(ProcessNoiseConfig())
    state = NavState.zeros(timestamp_ns=0)
    belief = GaussianBelief(state=state, covariance=np.eye(15, dtype=np.float64))
    imu = IMUInput(
        angular_velocity_rps=np.array([0.0, 0.0, 0.01], dtype=np.float64),
        linear_acceleration_mps2=np.array([0.0, 0.0, 9.80665], dtype=np.float64),
    )

    step = model.propagate(belief, target_timestamp_ns=10_000_000, imu=imu)

    assert step.dt_s > 0.0
    assert step.propagated_belief.state.timestamp_ns == 10_000_000
    cov = step.propagated_belief.covariance
    assert np.allclose(cov, cov.T, atol=1e-9)
    assert np.trace(cov) > np.trace(belief.covariance)
