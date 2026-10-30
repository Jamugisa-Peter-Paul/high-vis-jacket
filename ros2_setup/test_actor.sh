#!/bin/bash
source /opt/ros/jazzy/setup.bash
PKG=/mnt/d/mscs/intelligent_systems_and_robotics/jacket_follower/ros2_ws/src/jacket_follower
export GZ_SIM_RESOURCE_PATH=$PKG/models
timeout 60 gz sim -s -r --headless-rendering -v 3 $PKG/worlds/s1_normal.sdf > /tmp/gz_actor.log 2>&1 &
sleep 18
echo "== dynamic_pose names"; timeout 8 gz topic -e -n 1 -t /world/hall/dynamic_pose/info | grep name | sort | uniq | head
echo "== pose/info names"; timeout 8 gz topic -e -n 1 -t /world/hall/pose/info | grep name | sort | uniq | head -30
echo "== model list"; gz model --list 2>/dev/null | head -20
echo "== actor-related log"; grep -iE "actor|skin|walk|dae|mesh|warn" /tmp/gz_actor.log | head -10
pkill -f "gz sim"; wait 2>/dev/null
