# Consistency Metrics

`navfusion` provides statistical consistency checks to catch silent estimator regressions.

## Metrics

- `NIS(gnss)`: innovation consistency for accepted GNSS updates.
- `NEES(pos+vel)`: state consistency for position and velocity against truth.

## API

```python
from navfusion.analysis import nis_report, nees_position_velocity_report

nis = nis_report(result)
nees = nees_position_velocity_report(result, truth)
```

Each report includes:

- sample count
- average metric value
- 95% confidence interval for the expected average
- boolean `within_95_bounds`

## CI policy

Integration tests enforce explicit upper bounds for ANIS/ANEES in a deterministic nominal scenario.
This prevents accidental tuning drift or covariance regressions from merging undetected.
