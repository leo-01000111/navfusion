"""Runtime configuration dataclasses for navfusion v1."""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np
from numpy.typing import NDArray

from navfusion.core.state import STATE_SPEC, GaussianBelief, NavState


@dataclass(frozen=True)
class ProcessNoiseConfig:
    accel_noise_std_mps2: float = 0.6
    gyro_noise_std_rps: float = 0.03
    accel_bias_rw_std_mps2: float = 0.02
    gyro_bias_rw_std_rps: float = 0.001


@dataclass(frozen=True)
class GnssNoiseConfig:
    position_std_m: float = 2.0
    velocity_std_mps: float = 0.4

    def covariance(self) -> NDArray[np.float64]:
        pos_var = self.position_std_m * self.position_std_m
        vel_var = self.velocity_std_mps * self.velocity_std_mps
        return np.diag([pos_var, pos_var, pos_var, vel_var, vel_var, vel_var]).astype(np.float64)


@dataclass(frozen=True)
class GateConfig:
    enabled: bool = True
    threshold: float = 16.812  # chi-square p=0.99 for dof=6


@dataclass(frozen=True)
class EngineConfig:
    reorder_window_ns: int = 200_000_000
    degrade_after_s: float = 2.0


@dataclass(frozen=True)
class InitialUncertaintyConfig:
    position_std_m: float = 5.0
    velocity_std_mps: float = 1.0
    attitude_std_rad: float = 0.2
    gyro_bias_std_rps: float = 0.05
    accel_bias_std_mps2: float = 0.2

    def covariance(self) -> NDArray[np.float64]:
        diag = np.zeros(STATE_SPEC.error_size, dtype=np.float64)
        diag[STATE_SPEC.p] = self.position_std_m**2
        diag[STATE_SPEC.v] = self.velocity_std_mps**2
        diag[STATE_SPEC.theta] = self.attitude_std_rad**2
        diag[STATE_SPEC.gyro_bias] = self.gyro_bias_std_rps**2
        diag[STATE_SPEC.accel_bias] = self.accel_bias_std_mps2**2
        return np.diag(diag)


@dataclass(frozen=True)
class FusionConfig:
    gravity_mps2: float = 9.80665
    frame_id: str = "world"
    process_noise: ProcessNoiseConfig = ProcessNoiseConfig()
    gnss_noise: GnssNoiseConfig = GnssNoiseConfig()
    gate: GateConfig = GateConfig()
    engine: EngineConfig = EngineConfig()
    initial_uncertainty: InitialUncertaintyConfig = InitialUncertaintyConfig()


def default_initial_belief(config: FusionConfig | None = None) -> GaussianBelief:
    cfg = config or FusionConfig()
    return GaussianBelief(
        state=NavState.zeros(timestamp_ns=0),
        covariance=cfg.initial_uncertainty.covariance(),
    )
