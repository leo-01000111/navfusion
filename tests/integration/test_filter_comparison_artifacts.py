from __future__ import annotations

import subprocess
import sys
from pathlib import Path


def test_compare_filters_script_writes_artifacts(tmp_path: Path) -> None:
    output_dir = tmp_path / "artifacts"
    cmd = [
        sys.executable,
        "benchmarks/compare_filters.py",
        "--scenarios",
        "nominal",
        "--duration",
        "8",
        "--output-dir",
        str(output_dir),
    ]
    subprocess.run(cmd, check=True)

    csv_path = output_dir / "filter_comparison.csv"
    md_path = output_dir / "filter_comparison.md"

    assert csv_path.exists()
    assert md_path.exists()

    csv_text = csv_path.read_text(encoding="utf-8")
    md_text = md_path.read_text(encoding="utf-8")

    assert "rmse_position_m" in csv_text
    assert "anis_mean" in csv_text
    assert "ekf" in csv_text
    assert "ukf" in csv_text
    assert "EKF vs UKF Comparison" in md_text
    assert "Takeaways" in md_text
