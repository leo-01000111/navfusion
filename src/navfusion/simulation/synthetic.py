"""Synthetic scenarios for demos and integration tests."""

from __future__ import annotations

from collections.abc import Iterable
from dataclasses import dataclass

import numpy as np
from numpy.typing import NDArray

from navfusion.core.events import MeasurementEvent
from navfusion.core.state import (
    quaternion_from_small_angle,
    quaternion_multiply,
    quaternion_to_rotation_matrix,
)


@dataclass(frozen=True)
class TruthSample:
    timestamp_ns: int
    position_m: NDArray[np.float64]
    velocity_mps: NDArray[np.float64]
    attitude_wxyz: NDArray[np.float64]


def generate_imu_gnss_scenario(
    duration_s: float,
    imu_hz: float = 100.0,
    gnss_hz: float = 5.0,
    seed: int = 7,
    dropout_windows_s: Iterable[tuple[float, float]] | None = None,
    gnss_outlier_times_s: Iterable[float] | None = None,
) -> tuple[list[MeasurementEvent], list[TruthSample]]:
    rng = np.random.default_rng(seed)

    dt_imu = 1.0 / imu_hz
    dt_gnss = 1.0 / gnss_hz

    imu_times = np.arange(0.0, duration_s + 1e-9, dt_imu)
    gnss_times = np.arange(0.0, duration_s + 1e-9, dt_gnss)

    gyro_bias = np.array([0.002, -0.001, 0.001], dtype=np.float64)
    accel_bias = np.array([0.08, -0.04, 0.03], dtype=np.float64)
    gravity = np.array([0.0, 0.0, -9.80665], dtype=np.float64)

    yaw_rate = 0.02
    q = np.array([1.0, 0.0, 0.0, 0.0], dtype=np.float64)
    position = np.zeros(3, dtype=np.float64)
    velocity = np.zeros(3, dtype=np.float64)

    truths: list[TruthSample] = []
    events: list[MeasurementEvent] = []

    gnss_dropouts = list(dropout_windows_s or [])
    outlier_times = list(gnss_outlier_times_s or [])

    gnss_time_set = {int(round(t * 1e9)): t for t in gnss_times}

    for t in imu_times:
        timestamp_ns = int(round(t * 1e9))

        omega_true = np.array([0.0, 0.0, yaw_rate], dtype=np.float64)
        dq = quaternion_from_small_angle(omega_true * dt_imu)
        q = quaternion_multiply(q, dq)

        accel_world = np.array(
            [0.4 * np.sin(0.3 * t), 0.3 * np.cos(0.2 * t), 0.05 * np.sin(0.15 * t)],
            dtype=np.float64,
        )
        velocity = velocity + accel_world * dt_imu
        position = position + velocity * dt_imu + 0.5 * accel_world * dt_imu * dt_imu

        rot_world_body = quaternion_to_rotation_matrix(q)
        specific_force_body = rot_world_body.T @ (accel_world - gravity)

        imu_event = MeasurementEvent(
            timestamp_ns=timestamp_ns,
            sensor_type="imu",
            payload={
                "angular_velocity_rps": omega_true + gyro_bias + rng.normal(0.0, 0.01, 3),
                "linear_acceleration_mps2": (
                    specific_force_body + accel_bias + rng.normal(0.0, 0.2, 3)
                ),
            },
            sequence_id=0,
        )
        events.append(imu_event)

        truths.append(
            TruthSample(
                timestamp_ns=timestamp_ns,
                position_m=position.copy(),
                velocity_mps=velocity.copy(),
                attitude_wxyz=q.copy(),
            )
        )

        if timestamp_ns not in gnss_time_set:
            continue

        t_gnss = gnss_time_set[timestamp_ns]
        dropped = any(start <= t_gnss <= end for start, end in gnss_dropouts)
        if dropped:
            continue

        pos_meas = position + rng.normal(0.0, 2.0, 3)
        vel_meas = velocity + rng.normal(0.0, 0.35, 3)

        if any(abs(t_gnss - t_outlier) <= 1e-6 for t_outlier in outlier_times):
            pos_meas = pos_meas + np.array([25.0, -20.0, 8.0], dtype=np.float64)

        gnss_event = MeasurementEvent(
            timestamp_ns=timestamp_ns,
            sensor_type="gnss",
            payload={"position_m": pos_meas, "velocity_mps": vel_meas},
            sequence_id=0,
        )
        events.append(gnss_event)

    events.sort(key=lambda event: (event.timestamp_ns, 0 if event.sensor_type == "imu" else 1))
    return events, truths
