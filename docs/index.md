# navfusion

`navfusion` is a real-time-first package for 3D IMU+GNSS sensor fusion.

## Design goals

- Production-style architecture instead of a single script
- Deterministic event processing under asynchronous sensor timing
- Extensible model/filter interfaces without heavyweight framework coupling
- Portfolio-ready demos with measurable behavior under failures

## MVP features

- Error-state EKF and UKF backends (quaternion attitude)
- IMU propagation + GNSS position/velocity updates
- Bounded out-of-order event handling
- Innovation gating and update diagnostics
- Replay and stream-friendly APIs
- NIS/NEES consistency checks
