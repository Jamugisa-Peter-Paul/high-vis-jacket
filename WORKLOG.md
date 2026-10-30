# Work log: Safety-Jacket Follower (Intelligent Systems & Robotics project)

Use this to write the individual contribution statement. Add the name of whoever did/led each item.

| Date | Work | Done by |
|---|---|---|
| 2026-10-16 | Robot bring-up: Wi-Fi link, power diagnosis, camera focus, arm camera pose calibrated by image matching (`follow_pose.json`) | |
| 2026-10-16 | Robot-camera data session 1 recorded (506 frames, 449 usable) | |
| 2026-10-16 | Labelling: original model + Grounding DINO for missed frames + visual check | |
| 2026-10-16 | Fine-tune v1 (robot frames only): found false alarms doubled -> lesson: negatives needed | |
| 2026-10-16 | Independent test sets: robot hard block (DINO-labelled), public HB1204 + Vincent (human-labelled, CC BY 4.0) | |
| 2026-10-16 | Fine-tune v2 (robot + original + public vests + public negatives): robot mAP50 0.824 -> 0.925, frames found 69% -> 98% | |
| 2026-10-16 | ROS 2 Jazzy + Gazebo Harmonic installed in WSL2 (Ubuntu 24.04) | |
| 2026-10-16 | ROS 2 package `jacket_follower`: detector, follower (state machine + fail-safes), metrics, MasterPi bridge; launch files | |
| 2026-10-16 | Gazebo: MasterPi mecanum model with camera + sonar; vest worker and distractor actors; 3 scenario worlds | |
| 2026-10-17 | Gazebo people rebuilt as VelocityControl models (actors don't animate in headless camera sensors); scenario node drives them | |
| 2026-10-17 | Sim bugs fixed: mecanum wheel friction (robot could not turn in place), shared-texture caching (distractors rendered in the vest), mesh facing | |
| 2026-10-17 | Follower v2: distance in metres from box width/height (+ sonar when centred), PD on gap -> speed matching; sim-clock timing | |
| 2026-10-17 | Found v2 detector scores an orange shirt 0.54-0.60 (occasionally >0.70) -> acquisition hysteresis (0.70 to lock on, 0.40 to keep) + bearing gate + keep turning while confirming | |
| 2026-10-17 | Ground-truth metrics from Gazebo odometry; `scripts/analyze_sim.py` (following %, wrong-target time, gap, min distance, speed matching, recovery) | |
| 2026-10-17 | Final sim runs S1/S2/S3 + S3 ablation without hysteresis (robot follows the wrong person) | |
| 2026-10-17 | Gazebo GUI made usable in WSL (NVIDIA rendering via D3D12; was CPU llvmpipe), `open_sim.sh` | |
| 2026-10-17 | Real robot deployment: `masterpi_server.py` on the Pi + ROS bridge; dry run: 8 fps camera, 20 ms detection, 10 ms command round trip; vest detected at 0.83 | |
| 2026-10-17 | Found + fixed unsafe motor scaling (would have sent 100 % duty); measured motor dead zone (~28-32 %), turn direction, camera FOV (~71 deg) | |
| 2026-10-17 | Motor model: affine duty + battery-voltage compensation; stop-and-look search (continuous spin blurred frames) | |
| 2026-10-17 | Live follow run 2: robot searched, found the vest (0.84), FOLLOW ~8 s; then overshot (fast spin on fresh battery). Run 3: robot browned out (battery 8.0 -> 6.3 V in 10 min) | |
| 2026-10-29 | Live run 5 (lab): robot searched, found the vest and followed for a few seconds; camera only 1.5 fps in dim light (fix: 320x240 MJPG, 2 s watchdog, slower stop-and-look search) | |
| 2026-10-29 | Safety incident: battery brown-out rebooted the Pi mid-turn; the motor board kept the last speed and the robot spun until motors were zeroed remotely. Fix: `motors_off_at_boot.service` zeroes all motors at every boot (watchdog lives on the Pi, so it cannot cover a Pi reboot) | |

## Deadlines
- 2026-10-22: progress presentation (problem, dataset, detector progress, ROS 2 architecture, Gazebo setup, plan)
- 2026-10-29: final presentation + ALL deliverables
