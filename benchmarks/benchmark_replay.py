"""Replay throughput benchmark with CSV and Markdown artifacts."""

from __future__ import annotations

import argparse
import platform
import sys
import time
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path

from navfusion.api import run_replay
from navfusion.config import FilterType, FusionConfig
from navfusion.simulation import generate_imu_gnss_scenario


@dataclass(frozen=True)
class BenchmarkRow:
    filter_type: str
    duration_s: float
    total_events: int
    elapsed_s: float
    throughput_eps: float
    accepted_updates: int
    rejected_updates: int
    late_dropped_events: int
    final_covariance_trace: float


def run_benchmark(durations: list[float], filter_types: list[FilterType]) -> list[BenchmarkRow]:
    rows: list[BenchmarkRow] = []
    for filter_type in filter_types:
        for duration in durations:
            events, _truth = generate_imu_gnss_scenario(duration_s=duration)
            start = time.perf_counter()
            result = run_replay(events, config=FusionConfig(filter_type=filter_type))
            elapsed = time.perf_counter() - start
            eps = result.summary.total_events / elapsed if elapsed > 0.0 else 0.0
            rows.append(
                BenchmarkRow(
                    filter_type=filter_type,
                    duration_s=duration,
                    total_events=result.summary.total_events,
                    elapsed_s=elapsed,
                    throughput_eps=eps,
                    accepted_updates=result.summary.accepted_updates,
                    rejected_updates=result.summary.rejected_updates,
                    late_dropped_events=result.summary.late_dropped_events,
                    final_covariance_trace=result.summary.final_covariance_trace,
                )
            )
    return rows


def write_csv(rows: list[BenchmarkRow], output_path: Path) -> None:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    header = (
        "filter_type,duration_s,total_events,elapsed_s,throughput_eps,accepted_updates,"
        "rejected_updates,late_dropped_events,final_covariance_trace"
    )
    lines = [header]
    for row in rows:
        lines.append(
            f"{row.filter_type},{row.duration_s:.3f},{row.total_events},{row.elapsed_s:.6f},"
            f"{row.throughput_eps:.3f},{row.accepted_updates},{row.rejected_updates},"
            f"{row.late_dropped_events},{row.final_covariance_trace:.9f}"
        )
    output_path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def write_markdown(rows: list[BenchmarkRow], output_path: Path) -> None:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    now_iso = datetime.now(UTC).replace(microsecond=0).isoformat()

    lines = [
        "# Replay Benchmark Summary",
        "",
        f"- generated_utc: `{now_iso}`",
        f"- python: `{sys.version.split()[0]}`",
        f"- platform: `{platform.platform()}`",
        "",
        (
            "| Filter | Duration (s) | Events | Elapsed (s) | Throughput (events/s) | "
            "Accepted | Rejected | Late Dropped | Final trace(P) |"
        ),
        "| :--- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |",
    ]

    for row in rows:
        prefix = (
            f"| {row.filter_type} | {row.duration_s:.1f} | "
            f"{row.total_events} | {row.elapsed_s:.3f} |"
        )
        lines.append(
            prefix
            + " "
            f"{row.throughput_eps:.1f} | {row.accepted_updates} | {row.rejected_updates} | "
            f"{row.late_dropped_events} | {row.final_covariance_trace:.6f} |"
        )

    output_path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser(description="Run replay benchmark and export artifacts")
    parser.add_argument(
        "--durations",
        nargs="+",
        type=float,
        default=[30.0, 120.0, 300.0],
        help="Scenario durations in seconds",
    )
    parser.add_argument(
        "--filter-types",
        nargs="+",
        choices=["ekf", "ukf"],
        default=["ekf", "ukf"],
        help="Filter backends to benchmark",
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=Path("benchmarks") / "artifacts",
        help="Directory to write benchmark artifacts",
    )
    args = parser.parse_args()

    rows = run_benchmark(args.durations, filter_types=args.filter_types)

    csv_path = args.output_dir / "replay_benchmark.csv"
    md_path = args.output_dir / "replay_summary.md"

    write_csv(rows, csv_path)
    write_markdown(rows, md_path)

    for row in rows:
        print(
            f"filter={row.filter_type:3s} duration={row.duration_s:6.1f}s "
            f"events={row.total_events:6d} elapsed={row.elapsed_s:7.3f}s "
            f"throughput={row.throughput_eps:9.1f} events/s"
        )
    print(f"wrote: {csv_path}")
    print(f"wrote: {md_path}")


if __name__ == "__main__":
    main()
