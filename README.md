# Safety-Jacket Follower Robot

A robot that finds the person wearing a hi-vis safety jacket and follows them, keeping a gap of about 1.5 metres and speeding up when they speed up. Final project for Intelligent Systems and Robotics, Uganda Christian University, by Jamugisa Peter Paul and Ayebare Moses.

The system combines a fine-tuned YOLOv8n (You Only Look Once version 8, nano size) detector, ROS 2 (Robot Operating System 2) Jazzy, Gazebo Harmonic simulation and a Hiwonder MasterPi mecanum robot.

## Results

- **Detector:** on the robot's camera, mAP50 (mean Average Precision at 50% Intersection over Union) rose from 0.82 to 0.93, and the jacket is found in 98% of frames, up from 69%.
- **Simulation:** the robot followed the worker in all three scenarios. Without our lock-on rule it followed the wrong person for 11 seconds.
- **Real robot:** the full pipeline runs and the robot detects and locks on to the jacket. Steady following was not achieved because of battery, camera and motor limits.

## What is where

| Folder | Contents |
|---|---|
| `report_latex/` | Final report (`main.pdf`) and its LaTeX source |
| `presentation/` | Final slides and the script that builds them |
| `docs/` | User manual, contribution statement and dataset documentation |
| `models/` | Trained weights; `jacket_finetuned_v2.pt` is the final model |
| `ros2_ws/src/jacket_follower/` | ROS 2 (Robot Operating System 2) package: nodes, launch files, configs, Gazebo worlds and models |
| `ros2_setup/` | Install and run scripts for Ubuntu 24.04 |
| `robot/` | Code that runs on the MasterPi, and calibration tools |
| `scripts/` | Labelling, dataset building, training, evaluation and analysis |
| `results/` | Detector results, simulation results and robot videos |

To run it, see `docs/user_manual.pdf`. The dataset (about 890 MB) is not included; see `docs/dataset_documentation.pdf`.
