#!/bin/bash
# Open a scenario with the Gazebo window + the detector camera view (rqt_image_view).
#   bash open_sim.sh s1_normal        (or s2_speed, s3_challenge)
#   bash open_sim.sh s3_challenge acquire_conf:=0.40     (ablation: hysteresis off)
# Close with Ctrl+C in this terminal.
SCEN=${1:-s1_normal}
if [ "$(id -u)" != 0 ]; then
  echo "Run this as root: type 'exit', then start WSL with:  wsl -d rosjazzy -u root"; exit 1
fi
# draw with the NVIDIA GPU through WSL's D3D12 bridge (default here is llvmpipe = software rendering on the CPU)
export GALLIUM_DRIVER=d3d12 MESA_D3D12_DEFAULT_ADAPTER_NAME=NVIDIA
source /opt/ros/jazzy/setup.bash
source /root/venv/bin/activate
cd /root/ros2_ws && colcon build --symlink-install > /tmp/build.log 2>&1 || { tail -20 /tmp/build.log; exit 1; }
source /root/ros2_ws/install/setup.bash
export PYTHONPATH=/root/venv/lib/python3.12/site-packages:$PYTHONPATH
mkdir -p /tmp/sim
ros2 launch jacket_follower sim.launch.py scenario:=$SCEN gui:=true out_csv:=/tmp/sim/$SCEN.csv "${@:2}"
