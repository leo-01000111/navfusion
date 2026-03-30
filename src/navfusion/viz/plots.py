"""Visualization helpers for trajectories and diagnostics."""

from __future__ import annotations

from collections.abc import Sequence
from typing import Any

import numpy as np
from numpy.typing import NDArray

from navfusion.results import RunResult


def plot_trajectory_3d(result: RunResult) -> tuple[Any, Any]:
    try:
        import matplotlib.pyplot as plt
    except Exception as exc:  # pragma: no cover
        raise RuntimeError("matplotlib is required for visualization") from exc

    xyz = result.trajectory_xyz()
    fig = plt.figure(figsize=(8, 5))
    ax: Any = fig.add_subplot(111, projection="3d")
    if xyz.shape[0] > 0:
        ax.plot(xyz[:, 0], xyz[:, 1], xyz[:, 2], label="Estimated trajectory", linewidth=2)
    ax.set_xlabel("x [m]")
    ax.set_ylabel("y [m]")
    ax.set_zlabel("z [m]")
    ax.legend()
    ax.set_title("navfusion trajectory")
    return fig, ax


def plot_innovation_mahalanobis(
    result: RunResult,
    threshold: float | None = None,
) -> tuple[Any, Any]:
    try:
        import matplotlib.pyplot as plt
    except Exception as exc:  # pragma: no cover
        raise RuntimeError("matplotlib is required for visualization") from exc

    times = np.array([u.timestamp_ns * 1e-9 for u in result.update_history], dtype=np.float64)
    mahal = np.array([u.mahalanobis for u in result.update_history], dtype=np.float64)

    fig, ax = plt.subplots(figsize=(8, 4))
    if times.size > 0:
        ax.plot(times, mahal, marker="o", linestyle="-", label="Mahalanobis")
    if threshold is not None:
        ax.axhline(threshold, color="red", linestyle="--", label="Gate threshold")
    ax.set_xlabel("time [s]")
    ax.set_ylabel("mahalanobis")
    ax.set_title("Innovation gating trace")
    ax.legend()
    return fig, ax


def plot_covariance_trace(result: RunResult) -> tuple[Any, Any]:
    try:
        import matplotlib.pyplot as plt
    except Exception as exc:  # pragma: no cover
        raise RuntimeError("matplotlib is required for visualization") from exc

    times = np.array([s.timestamp_ns * 1e-9 for s in result.state_history], dtype=np.float64)
    trace = np.array([s.covariance_trace for s in result.state_history], dtype=np.float64)

    fig, ax = plt.subplots(figsize=(8, 4))
    if times.size > 0:
        ax.plot(times, trace, linewidth=2)
    ax.set_xlabel("time [s]")
    ax.set_ylabel("trace(P)")
    ax.set_title("Covariance trace over time")
    return fig, ax


def summarize_update_reasons(result: RunResult) -> dict[str, int]:
    counts: dict[str, int] = {}
    for update in result.update_history:
        counts[update.reason] = counts.get(update.reason, 0) + 1
    return counts


def trajectory_rmse(result: RunResult, truth_positions: Sequence[NDArray[np.float64]]) -> float:
    estimate = result.trajectory_xyz()
    truth = np.stack([np.asarray(p, dtype=np.float64) for p in truth_positions], axis=0)
    n = min(estimate.shape[0], truth.shape[0])
    if n == 0:
        return 0.0
    err = estimate[:n] - truth[:n]
    mse = np.mean(np.sum(err * err, axis=1))
    return float(np.sqrt(mse))
