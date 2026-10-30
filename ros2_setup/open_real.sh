#!/bin/bash
# Run the follower on the REAL MasterPi (robot must be running masterpi_server.py; laptop on its Wi-Fi).
#   bash open_real.sh            dry run: everything runs, wheels never move
#   bash open_real.sh motion     wheels enabled  (robot on the floor, clear space, person ready)
# Close with Ctrl+C: the laptop sends a stop, and the robot also stops by itself within 0.5 s.
if [ "$(id -u)" != 0 ]; then
  echo "Run this as root: type 'exit', then start WSL with:  wsl -d rosjazzy -u root"; exit 1
fi
MOTION=false; [ "$1" = "motion" ] && MOTION=true
export GALLIUM_DRIVER=d3d12 MESA_D3D12_DEFAULT_ADAPTER_NAME=NVIDIA
source /opt/ros/jazzy/setup.bash
source /root/venv/bin/activate
cd /root/ros2_ws && colcon build --symlink-install > /tmp/build.log 2>&1 || { tail -20 /tmp/build.log; exit 1; }
source /root/ros2_ws/install/setup.bash
export PYTHONPATH=/root/venv/lib/python3.12/site-packages:$PYTHONPATH
ros2 launch jacket_follower real.launch.py enable_motion:=$MOTION "${@:2}"
