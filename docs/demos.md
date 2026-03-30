# Demo Scenarios

## 1. GNSS dropout

- Shows prediction-only behavior through GNSS-denied windows.
- Inspect covariance growth and degraded flag.

## 2. Out-of-order GNSS

- Sends delayed GNSS packets within and beyond reorder window.
- Verifies deterministic ordering and late-drop counters.

## 3. GNSS outlier rejection

- Injects synthetic GNSS outliers.
- Shows gate rejection with update diagnostics.
