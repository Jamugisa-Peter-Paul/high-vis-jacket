# Gazebo scenario results

| Run | Following % | Wrong-target s | Gap walking (m) | Min dist (m) | Losses | Longest loss (s) | Final | Ends following the worker | Speed match worker→robot (m/s) | Est. bias ± sd (m) | Infer ms |
|---|---|---|---|---|---|---|---|---|---|---|---|
| S1 normal walk + two 90° turns | 95.9 | 0.0 | 2.07 ± 0.28 | 1.17 | 1 | 4.2 | FOLLOW @ 1.75 m | yes | 0.30→0.19 | 0.29 ± 0.1 | 17.1 |
| S2 speed changes (0.15 → 0.35 → 0.60 m/s) | 100.0 | 0.0 | 2.27 ± 0.42 | 1.82 | 0 | 0.0 | FOLLOW @ 1.82 m | yes | 0.15→0.13, 0.20→0.07, 0.35→0.32, 0.60→0.35 | 0.36 ± 0.07 | 16.8 |
| S3 occlusion + sprint + orange distractor | 69.9 | 0.0 | 2.26 ± 0.12 | 1.93 | 2 | 27.0 | FOLLOW @ 1.93 m | yes | 0.30→0.26, 0.80→0.24 | 0.45 ± 0.1 | 16.7 |
| S3 ablation: no acquisition hysteresis | 38.7 | 11.2 | 2.26 ± 0.12 | 1.95 | 26 | 11.3 | FOLLOW @ 3.69 m | **no** | 0.30→0.26, 0.80→0.25 | 0.52 ± 0.47 | 16.4 |
