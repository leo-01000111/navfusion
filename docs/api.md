# API

## High-level

```python
from navfusion.api import run_replay

result = run_replay(events)
```

## Streaming

```python
from navfusion.api import create_stream_runner

runner = create_stream_runner()
for event in events:
    runner.ingest_event(event)
result = runner.finalize()
```

## Main return type

`RunResult` includes:

- `state_history` (with covariance snapshots)
- `predict_history`
- `update_history`
- `summary`

## Consistency module

```python
from navfusion.analysis import nis_report, nees_position_velocity_report
```
