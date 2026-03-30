# Benchmarks

Run benchmark and export artifacts:

```bash
python benchmarks/benchmark_replay.py
```

Artifacts:

- `benchmarks/artifacts/replay_benchmark.csv`
- `benchmarks/artifacts/replay_summary.md`

You can customize durations, filter backends, and output location:

```bash
python benchmarks/benchmark_replay.py --durations 30 120 300 --filter-types ekf ukf --output-dir benchmarks/artifacts
```

The Markdown summary includes runtime context (Python version, platform) for reproducibility.
