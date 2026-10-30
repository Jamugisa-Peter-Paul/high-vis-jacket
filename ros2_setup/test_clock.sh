#!/bin/bash
source /opt/ros/jazzy/setup.bash
PKG=/root/ros2_ws/install/jacket_follower/share/jacket_follower
export GZ_SIM_RESOURCE_PATH=$PKG/models
timeout 40 gz sim -s -r --headless-rendering -v 4 $PKG/worlds/s1_normal.sdf > /tmp/gz_clock.log 2>&1 &
sleep 12
echo "== stats"; timeout 5 gz topic -e -n 1 -t /stats | grep -E "real_time_factor|sim_time" -A2 | head -8
sleep 8
echo "== stats later"; timeout 5 gz topic -e -n 1 -t /stats | grep -E "sec:" | head -2
echo "== actor log"; grep -iE "actor|trajector|animation|skin" /tmp/gz_clock.log | head -15
pkill -f "gz sim"; wait 2>/dev/null
