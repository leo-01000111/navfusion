# Benchmarks

## Replay throughput

Run benchmark and export artifacts:

```bash
python benchmarks/benchmark_replay.py
```

Artifacts:

- `benchmarks/artifacts/replay_benchmark.csv`
- `benchmarks/artifacts/replay_summary.md`

Customize durations, filter backends, and output location:

```bash
python benchmarks/benchmark_replay.py --durations 30 120 300 --filter-types ekf ukf --output-dir benchmarks/artifacts
```

## EKF vs UKF comparison report

Generate an accuracy/consistency/speed comparison across fixed scenarios:

```bash
python benchmarks/compare_filters.py --scenarios nominal dropout outlier --duration 60 --filter-types ekf ukf --output-dir benchmarks/artifacts
```

Artifacts:

- `benchmarks/artifacts/filter_comparison.csv`
- `benchmarks/artifacts/filter_comparison.md`

Included metrics:

- Position RMSE (`rmse_position_m`)
- Velocity RMSE (`rmse_velocity_mps`)
- ANIS (`anis_mean`)
- ANEES (`anees_mean`)
- Throughput (`throughput_eps`)

The Markdown report also includes per-scenario takeaway bullets comparing best accuracy vs best speed.
