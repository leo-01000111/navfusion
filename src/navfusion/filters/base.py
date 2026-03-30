"""Filter interfaces."""

from __future__ import annotations

from typing import Protocol

from navfusion.core.events import MeasurementEvent
from navfusion.core.state import GaussianBelief
from navfusion.models.motion import IMUInput
from navfusion.results import PredictRecord, UpdateRecord


class Filter(Protocol):
    @property
    def belief(self) -> GaussianBelief:
        ...

    def predict(self, timestamp_ns: int, imu: IMUInput) -> PredictRecord:
        ...

    def update(self, event: MeasurementEvent) -> UpdateRecord:
        ...
