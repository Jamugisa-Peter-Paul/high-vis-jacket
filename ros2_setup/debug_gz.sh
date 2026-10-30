#!/bin/bash
source /opt/ros/jazzy/setup.bash
PKG=/root/ros2_ws/install/jacket_follower/share/jacket_follower
export GZ_SIM_RESOURCE_PATH=$PKG/models
timeout 30 gz sim -s -r --headless-rendering -v 4 $PKG/worlds/${1:-s1_normal}.sdf > /tmp/gz_dbg.log 2>&1
echo "exit=$?"
grep -iE "error|warn|segment|fault|worker|mesh|dae|velocity" /tmp/gz_dbg.log | grep -v "Insufficient" | head -25
echo "== tail"; tail -15 /tmp/gz_dbg.log
