#!/bin/bash
source /opt/ros/jazzy/setup.bash
source /root/venv/bin/activate
source /root/ros2_ws/install/setup.bash
PKG=/root/ros2_ws/install/jacket_follower/share/jacket_follower
export GZ_SIM_RESOURCE_PATH=$PKG/models
WORLD=${1:-s1_normal}
timeout 80 gz sim -s -r --headless-rendering $PKG/worlds/$WORLD.sdf > /tmp/gz_peek.log 2>&1 &
sleep 6
timeout 70 ros2 run ros_gz_bridge parameter_bridge /camera/image_raw@sensor_msgs/msg/Image[gz.msgs.Image > /tmp/bridge.log 2>&1 &
sleep 2
python3 /mnt/d/mscs/intelligent_systems_and_robotics/jacket_follower/ros2_setup/sim_peek.py /mnt/d/mscs/intelligent_systems_and_robotics/jacket_follower/results/sim_peek_$WORLD 30 2>&1 | grep -vE "WARNING|Ultralytics"
pkill -f "gz sim"; pkill -f parameter_bridge; wait 2>/dev/null
