#!/bin/bash
source /opt/ros/jazzy/setup.bash
source /root/ros2_ws/install/setup.bash
PKG=/root/ros2_ws/install/jacket_follower/share/jacket_follower
export GZ_SIM_RESOURCE_PATH=$PKG/models
timeout 40 gz sim -s -r --headless-rendering $PKG/worlds/s1_normal.sdf > /dev/null 2>&1 &
sleep 8
timeout 30 ros2 run ros_gz_bridge parameter_bridge "/world/hall/dynamic_pose/info@tf2_msgs/msg/TFMessage[gz.msgs.Pose_V" > /dev/null 2>&1 &
sleep 4
echo "== ROS frame names"; timeout 8 ros2 topic echo --once /world/hall/dynamic_pose/info 2>/dev/null | grep -E "frame_id" | sort | uniq | head -20
echo "== gz names"; timeout 5 gz topic -e -n 1 -t /world/hall/dynamic_pose/info | grep name | sort | uniq
pkill -f "gz sim"; pkill -f parameter_bridge; wait 2>/dev/null
