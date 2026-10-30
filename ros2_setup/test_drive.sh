#!/bin/bash
# Check the simulated chassis: command pure rotation / forward / strafe and print ground-truth odometry.
source /opt/ros/jazzy/setup.bash
source /root/ros2_ws/install/setup.bash
PKG=/root/ros2_ws/install/jacket_follower/share/jacket_follower
export GZ_SIM_RESOURCE_PATH=$PKG/models
timeout 60 gz sim -s -r --headless-rendering $PKG/worlds/s1_normal.sdf > /dev/null 2>&1 &
sleep 6
odom() { gz topic -e -n 1 -t /model/masterpi/odometry | tr '\n' ' ' | grep -oE 'position \{[^}]*\}|orientation \{[^}]*\}' | tr -s ' '; echo; }
cmd() { echo "== $1: $2"; gz topic -t /cmd_vel -m gz.msgs.Twist -p "$2" ; sleep $3; odom; }
echo "== start"; odom
cmd rotate "angular: {z: 0.5}" 4
cmd stop "" 1
cmd forward "linear: {x: 0.2}" 3
cmd strafe_left "linear: {y: 0.2}" 3
cmd stop "" 1
pkill -f "gz sim"; wait 2>/dev/null
