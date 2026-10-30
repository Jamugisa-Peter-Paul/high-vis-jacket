#!/bin/bash
# Headless smoke test: run a scenario world for a few seconds, list topics, grab camera info and one image size.
source /opt/ros/jazzy/setup.bash
PKG=/mnt/d/mscs/intelligent_systems_and_robotics/jacket_follower/ros2_ws/src/jacket_follower
export GZ_SIM_RESOURCE_PATH=$PKG/models
WORLD=${1:-s1_normal}
timeout 60 gz sim -s -r --headless-rendering $PKG/worlds/$WORLD.sdf > /tmp/gz_$WORLD.log 2>&1 &
sleep 20
echo "== topics"; gz topic -l | grep -E "camera|cmd_vel|odom|range|pose/info"
echo "== one camera msg (header only)"; timeout 10 gz topic -e -n 1 -t /camera/image_raw | grep -E "width|height|pixel_format" | head -3
echo "== actor / model poses"; timeout 10 gz topic -e -n 1 -t /world/hall/pose/info | grep -E 'name: "(masterpi|worker)"' -A 5 | grep -E "name|x:|y:"
echo "== gz log errors"; grep -iE "error|fail" /tmp/gz_$WORLD.log | head -10
pkill -f "gz sim" ; wait 2>/dev/null
echo TEST_DONE
