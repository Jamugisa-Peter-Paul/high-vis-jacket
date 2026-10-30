#!/bin/bash
# Run one scenario headless for N seconds, record the CSV + a debug-image video, then stop everything.
#   bash run_scenario.sh s1_normal 70 [tag] [extra launch args]
#   bash run_scenario.sh s3_challenge 90 no_hysteresis acquire_conf:=0.40
SCEN=${1:-s1_normal}
DUR=${2:-70}
TAG=${3:+_$3}
PROJ=/mnt/d/mscs/intelligent_systems_and_robotics/jacket_follower
OUT=$PROJ/results/sim/$SCEN$TAG
mkdir -p $OUT
source /opt/ros/jazzy/setup.bash
source /root/venv/bin/activate
cd /root/ros2_ws && colcon build --symlink-install > /tmp/build.log 2>&1 || { tail -20 /tmp/build.log; exit 1; }
source /root/ros2_ws/install/setup.bash
export PYTHONPATH=/root/venv/lib/python3.12/site-packages:$PYTHONPATH

ros2 launch jacket_follower sim.launch.py scenario:=$SCEN gui:=false gz_extra:="-s --headless-rendering" \
     out_csv:=$OUT/run.csv ${@:4} > $OUT/launch.log 2>&1 &
LPID=$!
sleep 8
python3 $PROJ/ros2_setup/record_debug.py $OUT/debug.mp4 $((DUR - 10)) > $OUT/record.log 2>&1
kill -INT $LPID; sleep 3; pkill -f "gz sim"; pkill -f parameter_bridge; pkill -f "lib/jacket_follower/"; pkill -f "ros2 launch jacket_follower"; wait 2>/dev/null
echo "== states seen"; cut -d, -f11 $OUT/run.csv | sort | uniq -c
echo "== follower transitions"; grep -E " -> " $OUT/launch.log | sed 's/.*\] //' | head -20
echo "== errors"; grep -iE "error|traceback|exception" $OUT/launch.log | head -10
echo "== csv rows"; wc -l < $OUT/run.csv
