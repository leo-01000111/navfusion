from __future__ import annotations

from navfusion.api import build_default_filter
from navfusion.config import FusionConfig
from navfusion.filters import ErrorStateEKF, UnscentedKalmanFilter


def test_build_default_filter_selects_ekf() -> None:
    filter_impl = build_default_filter(FusionConfig(filter_type="ekf"))
    assert isinstance(filter_impl, ErrorStateEKF)


def test_build_default_filter_selects_ukf() -> None:
    filter_impl = build_default_filter(FusionConfig(filter_type="ukf"))
    assert isinstance(filter_impl, UnscentedKalmanFilter)
