# navfusion

`navfusion` is a real-time-first Python package for modular 3D navigation sensor fusion.

## Why this repo is different

- Deterministic async event handling with bounded out-of-order buffering.
- Engineering diagnostics (innovation gating + consistency metrics) instead of EKF-only math demos.
- Reproducible artifact pipeline for benchmarks and failure-mode demo images.

## MVP in this repo

- Error-state EKF and UKF backends with quaternion attitude state
- IMU propagation and GNSS position/velocity updates
- Asynchronous event engine with bounded out-of-order handling
- Innovation gating and run diagnostics
- Deterministic replay utilities, tests, and demo scenarios
- NIS/NEES consistency reports for CI guardrails

## Architecture at a glance

```mermaid
flowchart LR
    A[Raw Sensor Packets] --> B[Sensor Adapters]
    B --> C[MeasurementEvent]
    C --> D[Reorder Buffer]
    D --> E[Fusion Engine]
    E --> F[IMU Predict]
    E --> G[GNSS Update + Gating]
    F --> H[EKF or UKF Backend]
    G --> H
    H --> I[RunResult + Diagnostics]
    I --> J[Plots + Benchmarks + Docs Artifacts]
```

## Failure-mode demos

Dropout trajectory and covariance growth:

![GNSS dropout trajectory](docs/assets/dropout_trajectory.png)
![Dropout covariance trace](docs/assets/dropout_covariance_trace.png)

Out-of-order and outlier diagnostics:

![Out-of-order innovation trace](docs/assets/out_of_order_innovation.png)
![Outlier innovation trace](docs/assets/outlier_innovation.png)

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

## Generate portfolio artifacts

```bash
python examples/generate_demo_assets.py
python benchmarks/benchmark_replay.py
```

Outputs:

- `docs/assets/*.png` and `docs/assets/demo_summary.md`
- `benchmarks/artifacts/replay_benchmark.csv`
- `benchmarks/artifacts/replay_summary.md`

## Development

```bash
pre-commit install
pytest
ruff check .
mypy src
mkdocs serve
```
