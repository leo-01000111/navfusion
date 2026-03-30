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

- `state_history`
- `predict_history`
- `update_history`
- `summary`
