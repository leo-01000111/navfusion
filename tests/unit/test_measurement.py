from __future__ import annotations

import numpy as np

from navfusion.config import GnssNoiseConfig
from navfusion.core.state import NavState
from navfusion.models.measurement import GNSSPositionVelocityModel, compute_innovation_stats


def test_gnss_measurement_model_shapes() -> None:
    model = GNSSPositionVelocityModel(GnssNoiseConfig())
    state = NavState.zeros()
    zhat = model.measurement(state)
    h = model.jacobian(state)
    r = model.covariance()
    assert zhat.shape == (6,)
    assert h.shape == (6, 15)
    assert r.shape == (6, 6)


def test_innovation_stats_positive_for_nonzero_residual() -> None:
    residual = np.array([1.0, 0.0, 0.0], dtype=np.float64)
    s = np.eye(3, dtype=np.float64)
    stats = compute_innovation_stats(residual, s)
    assert stats.mahalanobis > 0.0
