from __future__ import annotations

import subprocess
import sys
from pathlib import Path


def test_benchmark_script_writes_artifacts(tmp_path: Path) -> None:
    output_dir = tmp_path / "artifacts"
    cmd = [
        sys.executable,
        "benchmarks/benchmark_replay.py",
        "--durations",
        "2",
        "4",
        "--output-dir",
        str(output_dir),
    ]
    subprocess.run(cmd, check=True)

    csv_path = output_dir / "replay_benchmark.csv"
    md_path = output_dir / "replay_summary.md"

    assert csv_path.exists()
    assert md_path.exists()
    assert "throughput_eps" in csv_path.read_text(encoding="utf-8")
    assert "Replay Benchmark Summary" in md_path.read_text(encoding="utf-8")
