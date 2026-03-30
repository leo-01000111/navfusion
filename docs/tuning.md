# Tuning

## Process noise

Tune in `ProcessNoiseConfig`:

- `accel_noise_std_mps2`
- `gyro_noise_std_rps`
- `accel_bias_rw_std_mps2`
- `gyro_bias_rw_std_rps`

## GNSS noise

Tune in `GnssNoiseConfig`:

- `position_std_m`
- `velocity_std_mps`

## Gating

Configure in `GateConfig`:

- `enabled`
- `threshold` (chi-square threshold for measurement dimension)

## Async behavior

Configure in `EngineConfig`:

- `reorder_window_ns`
- `degrade_after_s`
