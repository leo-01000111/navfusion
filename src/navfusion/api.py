"""Public API for building and running navfusion pipelines."""

from __future__ import annotations

from collections.abc import Iterable, Mapping
from dataclasses import dataclass

from navfusion.config import FusionConfig, default_initial_belief
from navfusion.core.events import MeasurementEvent
from navfusion.core.state import GaussianBelief
from navfusion.engine import FusionEngine
from navfusion.filters import ErrorStateEKF
from navfusion.models import GNSSPositionVelocityModel, IMUKinematicsModel
from navfusion.results import RunResult
from navfusion.sensors import SensorAdapter


@dataclass
class StreamRunner:
    """Stateful streaming API for real-time ingestion."""

    engine: FusionEngine
    adapters: Mapping[str, SensorAdapter] | None = None
    _sequence_counter: int = 1

    def ingest_event(self, event: MeasurementEvent) -> None:
        self.engine.ingest(event.with_sequence(self._sequence_counter))
        self._sequence_counter += 1

    def ingest_raw(self, sensor_type: str, raw_packet: dict[str, object]) -> None:
        if self.adapters is None:
            raise ValueError("No adapters configured for raw ingestion")
        if sensor_type not in self.adapters:
            raise ValueError(f"No adapter registered for sensor_type={sensor_type}")
        event = self.adapters[sensor_type].to_event(raw_packet, sequence_id=self._sequence_counter)
        self.engine.ingest(event)
        self._sequence_counter += 1

    def finalize(self) -> RunResult:
        return self.engine.finalize()


def build_default_filter(
    config: FusionConfig | None = None,
    initial_belief: GaussianBelief | None = None,
) -> ErrorStateEKF:
    cfg = config or FusionConfig()
    belief = initial_belief or default_initial_belief(cfg)
    motion_model = IMUKinematicsModel(
        process_noise=cfg.process_noise,
        gravity_mps2=cfg.gravity_mps2,
    )
    measurement_models = {
        "gnss": GNSSPositionVelocityModel(noise=cfg.gnss_noise),
    }
    return ErrorStateEKF(
        belief=belief,
        motion_model=motion_model,
        measurement_models=measurement_models,
        gate_enabled=cfg.gate.enabled,
        gate_threshold=cfg.gate.threshold,
    )


def build_default_engine(
    config: FusionConfig | None = None,
    initial_belief: GaussianBelief | None = None,
) -> FusionEngine:
    cfg = config or FusionConfig()
    filter_impl = build_default_filter(cfg, initial_belief)
    return FusionEngine(
        filter_impl=filter_impl,
        reorder_window_ns=cfg.engine.reorder_window_ns,
        degrade_after_s=cfg.engine.degrade_after_s,
    )


def run_replay(
    events: Iterable[MeasurementEvent],
    config: FusionConfig | None = None,
    initial_belief: GaussianBelief | None = None,
) -> RunResult:
    engine = build_default_engine(config=config, initial_belief=initial_belief)
    engine.ingest_many(events)
    return engine.finalize()


def run_stream(
    events: Iterable[MeasurementEvent],
    config: FusionConfig | None = None,
    initial_belief: GaussianBelief | None = None,
) -> RunResult:
    # Same core path as replay, exposed separately for API clarity.
    return run_replay(events=events, config=config, initial_belief=initial_belief)


def create_stream_runner(
    config: FusionConfig | None = None,
    initial_belief: GaussianBelief | None = None,
    adapters: Mapping[str, SensorAdapter] | None = None,
) -> StreamRunner:
    engine = build_default_engine(config=config, initial_belief=initial_belief)
    return StreamRunner(engine=engine, adapters=adapters)
