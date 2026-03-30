# EKF vs UKF Comparison

- generated_utc: `2026-03-30T12:30:05+00:00`
- python: `3.12.5`
- platform: `Windows-11-10.0.26200-SP0`

| Scenario | Filter | RMSE pos (m) | RMSE vel (m/s) | ANIS | ANEES | Throughput (events/s) | Accepted | Rejected | Late dropped |
| :--- | :--- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| nominal | ekf | 0.770 | 0.380 | 4.251 | 4.193 | 2010.6 | 300 | 1 | 0 |
| nominal | ukf | 0.770 | 0.380 | 4.251 | 4.193 | 1640.5 | 300 | 1 | 0 |
| dropout | ekf | 7.740 | 1.292 | 4.339 | 2.511 | 2047.1 | 198 | 1 | 0 |
| dropout | ukf | 7.740 | 1.292 | 4.339 | 2.511 | 1703.1 | 198 | 1 | 0 |
| outlier | ekf | 0.747 | 0.381 | 4.256 | 3.922 | 2007.4 | 296 | 5 | 0 |
| outlier | ukf | 0.747 | 0.381 | 4.256 | 3.922 | 1618.0 | 296 | 5 | 0 |

## Takeaways
- `nominal`: best position RMSE is **tie** (difference ~0.0%), while **ekf** is faster (difference ~18.4%).
- `dropout`: best position RMSE is **tie** (difference ~0.0%), while **ekf** is faster (difference ~16.8%).
- `outlier`: best position RMSE is **tie** (difference ~0.0%), while **ekf** is faster (difference ~19.4%).
