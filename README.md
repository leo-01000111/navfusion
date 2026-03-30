# navfusion

`navfusion` is a real-time-first Python package for modular 3D navigation sensor fusion.

## MVP in this repo

- Error-state EKF with quaternion attitude state
- IMU propagation and GNSS position/velocity updates
- Asynchronous event engine with bounded out-of-order handling
- Innovation gating and run diagnostics
- Deterministic replay utilities, tests, and demo scenarios

## Install

```bash
pip install -e .[dev,viz,docs]
```

## Quick start

```python
from navfusion.api import run_replay
from navfusion.simulation.synthetic import generate_imu_gnss_scenario

events, truth = generate_imu_gnss_scenario(duration_s=30.0)
result = run_replay(events)
print(result.summary)
```

## Development

```bash
pre-commit install
pytest
ruff check .
mypy src
mkdocs serve
```
