# Demos

Generate all demo assets:

```bash
python examples/generate_demo_assets.py
```

## 1. GNSS dropout

- Shows prediction-only behavior through GNSS-denied windows.
- Inspect covariance growth and degraded flag.

![Dropout trajectory](assets/dropout_trajectory.png)
![Dropout covariance](assets/dropout_covariance_trace.png)

## 2. Out-of-order GNSS

- Sends delayed GNSS packets within and beyond reorder window.
- Verifies deterministic ordering and late-drop counters.

![Out-of-order innovation](assets/out_of_order_innovation.png)

## 3. GNSS outlier rejection

- Injects synthetic GNSS outliers.
- Shows gate rejection with update diagnostics.

![Outlier innovation](assets/outlier_innovation.png)

## Scenario summary

See generated summary: `docs/assets/demo_summary.md`.
