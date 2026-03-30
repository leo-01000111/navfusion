"""Generate demo plots and summary artifacts for docs/README."""

from __future__ import annotations

from collections import Counter
from pathlib import Path

import matplotlib

matplotlib.use("Agg")

from navfusion.analysis import nees_position_velocity_report, nis_report
from navfusion.api import run_replay
from navfusion.config import EngineConfig, FusionConfig, GateConfig
from navfusion.simulation import generate_imu_gnss_scenario
from navfusion.viz import plot_covariance_trace, plot_innovation_mahalanobis, plot_trajectory_3d


def _make_out_of_order(events):
    shifted = list(events)
    gnss_indices = [idx for idx, event in enumerate(shifted) if event.sensor_type == "gnss"]
    if len(gnss_indices) < 6:
        return shifted

    idx = gnss_indices[3]
    event = shifted.pop(idx)
    shifted.insert(min(len(shifted), idx + 120), event)

    idx2 = gnss_indices[5]
    event2 = shifted.pop(idx2)
    shifted.insert(min(len(shifted), idx2 + 600), event2)
    return shifted


def _save_fig(fig, path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(path, dpi=160, bbox_inches="tight")
    fig.clf()


def generate_assets(output_dir: Path) -> None:
    output_dir.mkdir(parents=True, exist_ok=True)

    dropout_events, dropout_truth = generate_imu_gnss_scenario(
        duration_s=90.0,
        dropout_windows_s=[(20.0, 35.0), (55.0, 70.0)],
        seed=13,
    )
    dropout_result = run_replay(dropout_events)

    fig, _ = plot_trajectory_3d(dropout_result)
    _save_fig(fig, output_dir / "dropout_trajectory.png")
    fig2, _ = plot_covariance_trace(dropout_result)
    _save_fig(fig2, output_dir / "dropout_covariance_trace.png")

    ooo_events, _ = generate_imu_gnss_scenario(duration_s=45.0, seed=17)
    ooo_events = _make_out_of_order(ooo_events)
    ooo_cfg = FusionConfig(engine=EngineConfig(reorder_window_ns=300_000_000, degrade_after_s=2.0))
    ooo_result = run_replay(ooo_events, config=ooo_cfg)

    fig3, _ = plot_innovation_mahalanobis(ooo_result, threshold=16.812)
    _save_fig(fig3, output_dir / "out_of_order_innovation.png")

    outlier_events, outlier_truth = generate_imu_gnss_scenario(
        duration_s=60.0,
        gnss_outlier_times_s=[12.0, 24.0, 37.0, 48.0],
        seed=29,
    )
    outlier_cfg = FusionConfig(gate=GateConfig(enabled=True, threshold=16.812))
    outlier_result = run_replay(outlier_events, config=outlier_cfg)

    fig4, _ = plot_innovation_mahalanobis(outlier_result, threshold=16.812)
    _save_fig(fig4, output_dir / "outlier_innovation.png")

    nis = nis_report(outlier_result)
    nees = nees_position_velocity_report(dropout_result, dropout_truth)
    reasons = Counter(update.reason for update in outlier_result.update_history)

    summary_lines = [
        "# Demo Artifact Summary",
        "",
        "## Outlier scenario",
        f"- accepted_updates: {outlier_result.summary.accepted_updates}",
        f"- rejected_updates: {outlier_result.summary.rejected_updates}",
        f"- update_reasons: {dict(reasons)}",
        f"- ANIS: {nis.mean_value:.3f} (95% bounds [{nis.lower_95:.3f}, {nis.upper_95:.3f}])",
        "",
        "## Dropout scenario",
        f"- ANEES(pos+vel): {nees.mean_value:.3f} "
        f"(95% bounds [{nees.lower_95:.3f}, {nees.upper_95:.3f}])",
        f"- degraded_any: {any(state.degraded for state in dropout_result.state_history)}",
        "",
        "## Out-of-order scenario",
        f"- late_dropped_events: {ooo_result.summary.late_dropped_events}",
        f"- total_events: {ooo_result.summary.total_events}",
    ]

    (output_dir / "demo_summary.md").write_text("\n".join(summary_lines) + "\n", encoding="utf-8")


def main() -> None:
    generate_assets(Path("docs") / "assets")
    print("wrote demo artifacts to docs/assets")


if __name__ == "__main__":
    main()
