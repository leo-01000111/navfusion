"""Fusion orchestrator with asynchronous event buffering."""

from __future__ import annotations

from collections.abc import Iterable

import numpy as np

from navfusion.core.events import MeasurementEvent
from navfusion.core.time import EventReorderBuffer
from navfusion.filters.base import Filter
from navfusion.models.motion import IMUInput, zero_imu_input
from navfusion.results import (
    PredictRecord,
    RunResult,
    RunSummary,
    StateRecord,
    UpdateRecord,
    state_record_from_nav_state,
)


class FusionEngine:
    """Event-driven fusion runner with bounded out-of-order handling."""

    def __init__(
        self,
        filter_impl: Filter,
        reorder_window_ns: int,
        degrade_after_s: float = 2.0,
    ) -> None:
        self._filter = filter_impl
        self._buffer: EventReorderBuffer[MeasurementEvent] = EventReorderBuffer(
            window_ns=reorder_window_ns
        )
        self._degrade_after_ns = int(round(degrade_after_s * 1e9))
        self._next_sequence_id = 1

        self._state_history: list[StateRecord] = []
        self._predict_history: list[PredictRecord] = []
        self._update_history: list[UpdateRecord] = []

        self._total_events = 0
        self._imu_events = 0
        self._gnss_events = 0
        self._accepted_updates = 0
        self._rejected_updates = 0

        self._last_imu_input: IMUInput | None = None
        self._last_gnss_accepted_ns: int | None = None

        self._record_state()

    def ingest(self, event: MeasurementEvent) -> None:
        queued = self._buffer.push(event.with_sequence(self._next_sequence_id))
        self._next_sequence_id += 1
        if not queued:
            return
        for ready_event in self._buffer.pop_ready():
            self._process_event(ready_event)

    def ingest_many(self, events: Iterable[MeasurementEvent]) -> None:
        for event in events:
            self.ingest(event)

    def finalize(self) -> RunResult:
        for ready_event in self._buffer.flush():
            self._process_event(ready_event)

        summary = RunSummary(
            total_events=self._total_events,
            imu_events=self._imu_events,
            gnss_events=self._gnss_events,
            accepted_updates=self._accepted_updates,
            rejected_updates=self._rejected_updates,
            late_dropped_events=self._buffer.stats.late_dropped,
            final_covariance_trace=float(np.trace(self._filter.belief.covariance)),
        )

        return RunResult(
            state_history=tuple(self._state_history),
            predict_history=tuple(self._predict_history),
            update_history=tuple(self._update_history),
            summary=summary,
        )

    def _process_event(self, event: MeasurementEvent) -> None:
        self._total_events += 1
        if event.sensor_type == "imu":
            self._imu_events += 1
            imu = IMUInput(
                angular_velocity_rps=np.asarray(
                    event.payload["angular_velocity_rps"],
                    dtype=np.float64,
                ),
                linear_acceleration_mps2=np.asarray(
                    event.payload["linear_acceleration_mps2"],
                    dtype=np.float64,
                ),
            )
            predict = self._filter.predict(event.timestamp_ns, imu)
            self._last_imu_input = imu
            self._predict_history.append(predict)
            self._apply_degraded_flag(event.timestamp_ns)
            self._record_state()
            return

        if event.sensor_type == "gnss":
            self._gnss_events += 1
            current_ts = self._filter.belief.state.timestamp_ns
            if event.timestamp_ns > current_ts:
                hold_imu = (
                    self._last_imu_input
                    if self._last_imu_input is not None
                    else zero_imu_input()
                )
                predict = self._filter.predict(event.timestamp_ns, hold_imu)
                self._predict_history.append(predict)

            update = self._filter.update(event)
            self._update_history.append(update)
            if update.accepted:
                self._accepted_updates += 1
                self._last_gnss_accepted_ns = event.timestamp_ns
            else:
                self._rejected_updates += 1

            self._apply_degraded_flag(event.timestamp_ns)
            self._record_state()
            return

    def _apply_degraded_flag(self, now_ns: int) -> None:
        if self._last_gnss_accepted_ns is None:
            self._filter.belief.degraded = True
            return
        if now_ns - self._last_gnss_accepted_ns > self._degrade_after_ns:
            self._filter.belief.degraded = True
        else:
            self._filter.belief.degraded = False

    def _record_state(self) -> None:
        state = self._filter.belief.state
        cov_trace = float(np.trace(self._filter.belief.covariance))
        self._state_history.append(
            state_record_from_nav_state(
                state=state,
                covariance=self._filter.belief.covariance,
                covariance_trace=cov_trace,
                degraded=self._filter.belief.degraded,
            )
        )
