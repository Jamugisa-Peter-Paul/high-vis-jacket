#!/bin/bash
# Final simulation runs used in the report: the three scenarios + the scenario-3 ablation.
cd /mnt/d/mscs/intelligent_systems_and_robotics/jacket_follower
sed -i 's/\r$//' ros2_setup/*.sh ros2_setup/*.py
for s in s1_normal s2_speed s3_challenge; do echo "######## $s"; bash ros2_setup/run_scenario.sh $s 125 | grep -v -e Lazy -e 'process has died'; done
echo "######## s3_challenge_no_hysteresis"; bash ros2_setup/run_scenario.sh s3_challenge 125 no_hysteresis acquire_conf:=0.40 | grep -v -e Lazy -e 'process has died'
echo FINISHED
