"""EKF vs UKF comparison benchmark (accuracy + consistency + throughput)."""

from __future__ import annotations

import argparse
import platform
import sys
import time
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path

from navfusion.analysis import summarize_filter_performance
from navfusion.api import run_replay
from navfusion.config import EngineConfig, FilterType, FusionConfig
from navfusion.core.events import MeasurementEvent
from navfusion.simulation import TruthSample, generate_imu_gnss_scenario


@dataclass(frozen=True)
class ScenarioConfig:
    name: str
    dropout_windows_s: list[tuple[float, float]]
    gnss_outlier_times_s: list[float]
    make_out_of_order: bool


@dataclass(frozen=True)
class ComparisonRow:
    scenario: str
    filter_type: str
    duration_s: float
    total_events: int
    elapsed_s: float
    throughput_eps: float
    rmse_position_m: float
    rmse_velocity_mps: float
    anis_mean: float
    anis_samples: int
    anees_mean: float
    anees_samples: int
    accepted_updates: int
    rejected_updates: int
    late_dropped_events: int


SCENARIOS: dict[str, ScenarioConfig] = {
    "nominal": ScenarioConfig(
        name="nominal",
        dropout_windows_s=[],
        gnss_outlier_times_s=[],
        make_out_of_order=False,
    ),
    "dropout": ScenarioConfig(
        name="dropout",
        dropout_windows_s=[(20.0, 35.0), (55.0, 70.0)],
        gnss_outlier_times_s=[],
        make_out_of_order=False,
    ),
    "outlier": ScenarioConfig(
        name="outlier",
        dropout_windows_s=[],
        gnss_outlier_times_s=[12.0, 24.0, 37.0, 48.0],
        make_out_of_order=False,
    ),
    "out_of_order": ScenarioConfig(
        name="out_of_order",
        dropout_windows_s=[],
        gnss_outlier_times_s=[],
        make_out_of_order=True,
    ),
}


def _inject_out_of_order(events: list[MeasurementEvent]) -> list[MeasurementEvent]:
    modified = list(events)
    gnss_idxs = [idx for idx, event in enumerate(modified) if event.sensor_type == "gnss"]
    if len(gnss_idxs) < 6:
        return modified

    moved = modified.pop(gnss_idxs[2])
    modified.insert(min(len(modified), gnss_idxs[2] + 60), moved)

    moved2 = modified.pop(gnss_idxs[5])
    modified.append(moved2)
    return modified


def _scenario_events_truth(
    scenario: ScenarioConfig,
    duration_s: float,
    seed: int,
) -> tuple[list[MeasurementEvent], list[TruthSample]]:
    events, truth = generate_imu_gnss_scenario(
        duration_s=duration_s,
        seed=seed,
        dropout_windows_s=scenario.dropout_windows_s,
        gnss_outlier_times_s=scenario.gnss_outlier_times_s,
    )
    if scenario.make_out_of_order:
        events = _inject_out_of_order(events)
    return events, truth


def run_comparison(
    scenarios: list[str],
    filter_types: list[FilterType],
    duration_s: float,
    seed: int,
) -> list[ComparisonRow]:
    rows: list[ComparisonRow] = []

    for scenario_name in scenarios:
        scenario = SCENARIOS[scenario_name]
        events, truth = _scenario_events_truth(scenario=scenario, duration_s=duration_s, seed=seed)

        for filter_type in filter_types:
            config = FusionConfig(filter_type=filter_type)
            if scenario.make_out_of_order:
                config = FusionConfig(
                    filter_type=filter_type,
                    engine=EngineConfig(reorder_window_ns=300_000_000, degrade_after_s=2.0),
                )

            start = time.perf_counter()
            result = run_replay(events, config=config)
            elapsed = time.perf_counter() - start

            perf = summarize_filter_performance(result, truth)
            eps = result.summary.total_events / elapsed if elapsed > 0.0 else 0.0

            rows.append(
                ComparisonRow(
                    scenario=scenario_name,
                    filter_type=filter_type,
                    duration_s=duration_s,
                    total_events=result.summary.total_events,
                    elapsed_s=elapsed,
                    throughput_eps=eps,
                    rmse_position_m=perf.rmse_position_m,
                    rmse_velocity_mps=perf.rmse_velocity_mps,
                    anis_mean=perf.anis_mean,
                    anis_samples=perf.anis_samples,
                    anees_mean=perf.anees_mean,
                    anees_samples=perf.anees_samples,
                    accepted_updates=result.summary.accepted_updates,
                    rejected_updates=result.summary.rejected_updates,
                    late_dropped_events=result.summary.late_dropped_events,
                )
            )

    return rows


def write_csv(rows: list[ComparisonRow], output_path: Path) -> None:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    header = (
        "scenario,filter_type,duration_s,total_events,elapsed_s,throughput_eps,rmse_position_m,"
        "rmse_velocity_mps,anis_mean,anis_samples,anees_mean,anees_samples,"
        "accepted_updates,rejected_updates,late_dropped_events"
    )
    lines = [header]

    for row in rows:
        lines.append(
            f"{row.scenario},{row.filter_type},{row.duration_s:.3f},{row.total_events},"
            f"{row.elapsed_s:.6f},{row.throughput_eps:.3f},{row.rmse_position_m:.6f},"
            f"{row.rmse_velocity_mps:.6f},{row.anis_mean:.6f},{row.anis_samples},"
            f"{row.anees_mean:.6f},{row.anees_samples},{row.accepted_updates},"
            f"{row.rejected_updates},{row.late_dropped_events}"
        )

    output_path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def write_markdown(rows: list[ComparisonRow], output_path: Path) -> None:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    now_iso = datetime.now(UTC).replace(microsecond=0).isoformat()

    lines = [
        "# EKF vs UKF Comparison",
        "",
        f"- generated_utc: `{now_iso}`",
        f"- python: `{sys.version.split()[0]}`",
        f"- platform: `{platform.platform()}`",
        "",
        (
            "| Scenario | Filter | RMSE pos (m) | RMSE vel (m/s) | ANIS | ANEES | "
            "Throughput (events/s) | Accepted | Rejected | Late dropped |"
        ),
        "| :--- | :--- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |",
    ]

    for row in rows:
        lines.append(
            f"| {row.scenario} | {row.filter_type} | {row.rmse_position_m:.3f} | "
            f"{row.rmse_velocity_mps:.3f} | {row.anis_mean:.3f} | {row.anees_mean:.3f} | "
            f"{row.throughput_eps:.1f} | {row.accepted_updates} | {row.rejected_updates} | "
            f"{row.late_dropped_events} |"
        )

    lines.extend(["", "## Takeaways"])
    lines.extend(_scenario_takeaways(rows))

    output_path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def _scenario_takeaways(rows: list[ComparisonRow]) -> list[str]:
    out: list[str] = []
    grouped: dict[str, list[ComparisonRow]] = {}
    for row in rows:
        grouped.setdefault(row.scenario, []).append(row)

    for scenario, scenario_rows in grouped.items():
        ekf = next((row for row in scenario_rows if row.filter_type == "ekf"), None)
        ukf = next((row for row in scenario_rows if row.filter_type == "ukf"), None)
        if ekf is None or ukf is None:
            continue

        speed_delta_pct = 100.0 * abs(ekf.throughput_eps - ukf.throughput_eps) / max(
            ekf.throughput_eps,
            ukf.throughput_eps,
            1e-9,
        )
        rmse_delta_pct = 100.0 * abs(ekf.rmse_position_m - ukf.rmse_position_m) / max(
            ekf.rmse_position_m,
            ukf.rmse_position_m,
            1e-9,
        )

        if rmse_delta_pct <= 0.5:
            rmse_label = "tie"
        else:
            rmse_label = "ekf" if ekf.rmse_position_m < ukf.rmse_position_m else "ukf"

        if speed_delta_pct <= 0.5:
            speed_label = "tie"
        else:
            speed_label = "ekf" if ekf.throughput_eps > ukf.throughput_eps else "ukf"

        out.append(
            f"- `{scenario}`: best position RMSE is **{rmse_label}** "
            f"(difference ~{rmse_delta_pct:.1f}%), while **{speed_label}** is faster "
            f"(difference ~{speed_delta_pct:.1f}%)."
        )
    return out


def main() -> None:
    parser = argparse.ArgumentParser(description="Run EKF-vs-UKF comparison and export artifacts")
    parser.add_argument(
        "--scenarios",
        nargs="+",
        choices=sorted(SCENARIOS.keys()),
        default=["nominal", "dropout", "outlier"],
        help="Scenario names to evaluate",
    )
    parser.add_argument(
        "--filter-types",
        nargs="+",
        choices=["ekf", "ukf"],
        default=["ekf", "ukf"],
        help="Filter backends to compare",
    )
    parser.add_argument(
        "--duration",
        type=float,
        default=60.0,
        help="Duration per scenario in seconds",
    )
    parser.add_argument("--seed", type=int, default=77, help="Synthetic scenario seed")
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=Path("benchmarks") / "artifacts",
        help="Directory to write artifacts",
    )
    args = parser.parse_args()

    rows = run_comparison(
        scenarios=args.scenarios,
        filter_types=args.filter_types,
        duration_s=args.duration,
        seed=args.seed,
    )

    csv_path = args.output_dir / "filter_comparison.csv"
    md_path = args.output_dir / "filter_comparison.md"

    write_csv(rows, csv_path)
    write_markdown(rows, md_path)

    for row in rows:
        print(
            f"scenario={row.scenario:12s} filter={row.filter_type:3s} "
            f"rmse_pos={row.rmse_position_m:7.3f} rmse_vel={row.rmse_velocity_mps:7.3f} "
            f"anis={row.anis_mean:7.3f} anees={row.anees_mean:7.3f} "
            f"throughput={row.throughput_eps:8.1f} eps"
        )

    print(f"wrote: {csv_path}")
    print(f"wrote: {md_path}")


if __name__ == "__main__":
    main()
