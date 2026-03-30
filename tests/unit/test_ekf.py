from __future__ import annotations

import numpy as np

from navfusion.config import FusionConfig
from navfusion.core.events import MeasurementEvent
from navfusion.core.state import GaussianBelief, NavState
from navfusion.filters import ErrorStateEKF
from navfusion.models import GNSSPositionVelocityModel, IMUInput, IMUKinematicsModel


def _build_filter() -> ErrorStateEKF:
    config = FusionConfig()
    state = NavState.zeros(timestamp_ns=0)
    belief = GaussianBelief(state=state, covariance=np.eye(15, dtype=np.float64))
    motion = IMUKinematicsModel(config.process_noise, gravity_mps2=config.gravity_mps2)
    gnss = GNSSPositionVelocityModel(config.gnss_noise)
    return ErrorStateEKF(
        belief=belief,
        motion_model=motion,
        measurement_models={"gnss": gnss},
        gate_enabled=True,
        gate_threshold=16.812,
    )


def test_ekf_predict_then_accepts_nominal_update() -> None:
    ekf = _build_filter()
    ekf.predict(
        timestamp_ns=10_000_000,
        imu=IMUInput(
            angular_velocity_rps=np.array([0.0, 0.0, 0.0], dtype=np.float64),
            linear_acceleration_mps2=np.array([0.0, 0.0, 9.80665], dtype=np.float64),
        ),
    )

    event = MeasurementEvent(
        timestamp_ns=10_000_000,
        sensor_type="gnss",
        payload={
            "position_m": ekf.belief.state.position_m.copy(),
            "velocity_mps": ekf.belief.state.velocity_mps.copy(),
        },
    )
    update = ekf.update(event)
    assert update.accepted


def test_ekf_rejects_large_outlier_with_gating() -> None:
    ekf = _build_filter()
    ekf.predict(
        timestamp_ns=20_000_000,
        imu=IMUInput(
            angular_velocity_rps=np.array([0.0, 0.0, 0.0], dtype=np.float64),
            linear_acceleration_mps2=np.array([0.0, 0.0, 9.80665], dtype=np.float64),
        ),
    )

    event = MeasurementEvent(
        timestamp_ns=20_000_000,
        sensor_type="gnss",
        payload={
            "position_m": np.array([1000.0, 1000.0, 1000.0], dtype=np.float64),
            "velocity_mps": np.array([50.0, 50.0, 50.0], dtype=np.float64),
        },
    )
    update = ekf.update(event)
    assert not update.accepted
    assert update.reason == "gate_reject"
