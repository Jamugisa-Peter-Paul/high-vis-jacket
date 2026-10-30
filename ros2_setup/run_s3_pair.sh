#!/bin/bash
# Scenario 3 twice: with acquisition hysteresis (default) and without it (ablation).
cd /mnt/d/mscs/intelligent_systems_and_robotics/jacket_follower
sed -i 's/\r$//' ros2_setup/*.sh ros2_setup/*.py
show() { awk -F, 'NR==1 || (NR-2)%30==0' results/sim/$1/run.csv | column -t -s, | cut -c1-175; }
echo "######## s3 WITH hysteresis";    bash ros2_setup/run_scenario.sh s3_challenge 125 | grep -v -e Lazy -e 'process has died'; show s3_challenge
echo "######## s3 WITHOUT hysteresis"; bash ros2_setup/run_scenario.sh s3_challenge 125 no_hysteresis acquire_conf:=0.40 | grep -v -e Lazy -e 'process has died'; show s3_challenge_no_hysteresis
