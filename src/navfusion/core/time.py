"""Time normalization and bounded reorder buffer."""

from __future__ import annotations

import heapq
from dataclasses import dataclass, field
from typing import Generic, Literal, TypeVar

from navfusion.core.events import MeasurementEvent

TimestampUnit = Literal["ns", "us", "ms", "s"]


_SCALE_TO_NS: dict[TimestampUnit, int] = {
    "ns": 1,
    "us": 1_000,
    "ms": 1_000_000,
    "s": 1_000_000_000,
}


def to_timestamp_ns(value: int | float, unit: TimestampUnit = "ns") -> int:
    scale = _SCALE_TO_NS[unit]
    return int(round(float(value) * float(scale)))


T = TypeVar("T", bound=MeasurementEvent)


@dataclass(order=True)
class _QueueItem(Generic[T]):
    timestamp_ns: int
    sequence_id: int
    event: T = field(compare=False)


@dataclass
class ReorderStats:
    late_dropped: int = 0


class EventReorderBuffer(Generic[T]):
    """Maintains deterministic timestamp ordering with a bounded lateness window."""

    def __init__(self, window_ns: int) -> None:
        if window_ns < 0:
            raise ValueError("window_ns must be non-negative")
        self._window_ns = window_ns
        self._heap: list[_QueueItem[T]] = []
        self._max_seen_ns: int | None = None
        self._last_emitted_ns: int | None = None
        self.stats = ReorderStats()

    @property
    def last_emitted_ns(self) -> int | None:
        return self._last_emitted_ns

    def push(self, event: T) -> bool:
        if self._last_emitted_ns is not None and event.timestamp_ns < self._last_emitted_ns:
            self.stats.late_dropped += 1
            return False

        if self._max_seen_ns is None:
            self._max_seen_ns = event.timestamp_ns
        else:
            self._max_seen_ns = max(self._max_seen_ns, event.timestamp_ns)

        heapq.heappush(
            self._heap,
            _QueueItem(timestamp_ns=event.timestamp_ns, sequence_id=event.sequence_id, event=event),
        )
        return True

    def pop_ready(self) -> list[T]:
        if self._max_seen_ns is None:
            return []
        watermark_ns = self._max_seen_ns - self._window_ns
        out: list[T] = []
        while self._heap and self._heap[0].timestamp_ns <= watermark_ns:
            out.append(self._pop_one())
        return out

    def flush(self) -> list[T]:
        out: list[T] = []
        while self._heap:
            out.append(self._pop_one())
        return out

    def _pop_one(self) -> T:
        item = heapq.heappop(self._heap)
        self._last_emitted_ns = item.timestamp_ns
        return item.event
