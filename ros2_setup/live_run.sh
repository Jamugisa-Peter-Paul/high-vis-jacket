#!/bin/bash
# Live follow run on the real robot with MOTION ENABLED, recorded: video + probe stats + launch log.
#   bash live_run.sh run4 150          (output folder name under results/real, duration in seconds)
#   bash live_run.sh demo1 60 dry      (wheels off: detection + follower decisions only)
P=/mnt/d/mscs/intelligent_systems_and_robotics/jacket_follower
NAME=${1:-run}; DUR=${2:-60}
OUT=$P/results/real/$NAME; mkdir -p $OUT
sed -i 's/\r$//' $P/ros2_setup/open_real.sh $P/ros2_setup/probe_real.py $P/ros2_setup/record_debug.py
bash $P/ros2_setup/open_real.sh ${3:-motion} > $OUT/launch.log 2>&1 &
sleep 12
source /opt/ros/jazzy/setup.bash; source /root/venv/bin/activate
echo "RUNNING - stand in front of the robot now"
python3 $P/ros2_setup/record_debug.py $OUT/debug.mp4 $DUR > $OUT/record.log 2>&1 &
python3 $P/ros2_setup/probe_real.py $DUR > $OUT/probe.txt
pkill -INT -f "ros2 launch jacket_follower"; sleep 4; pkill -9 -f "lib/jacket_follower/"; pkill -9 -f rqt_image_view
cat $OUT/probe.txt
echo "== transitions"; grep -E " -> |motion" $OUT/launch.log | sed 's/.*\] //'
