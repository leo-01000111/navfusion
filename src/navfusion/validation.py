"""Validation helpers for runtime checks and user-facing errors."""

from __future__ import annotations

import numpy as np
from numpy.typing import NDArray

from navfusion.core.state import STATE_SPEC


def require_shape(name: str, value: NDArray[np.float64], shape: tuple[int, ...]) -> None:
    if value.shape != shape:
        raise ValueError(f"{name} must have shape {shape}, got {value.shape}")


def require_finite(name: str, value: NDArray[np.float64]) -> None:
    if not np.all(np.isfinite(value)):
        raise ValueError(f"{name} must be finite")


def require_covariance(name: str, cov: NDArray[np.float64], dim: int) -> None:
    require_shape(name, cov, (dim, dim))
    require_finite(name, cov)
    if not np.allclose(cov, cov.T, atol=1e-9):
        raise ValueError(f"{name} must be symmetric")
    eig = np.linalg.eigvalsh(cov)
    if float(np.min(eig)) < -1e-9:
        raise ValueError(f"{name} must be positive semi-definite")


def require_error_covariance(cov: NDArray[np.float64]) -> None:
    require_covariance("error covariance", cov, STATE_SPEC.error_size)
