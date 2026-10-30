#!/bin/bash
# Run the given scenarios one after another and print a 2-second sampled table of each CSV.
#   bash run_all.sh s1_normal s2_speed s3_challenge
cd /mnt/d/mscs/intelligent_systems_and_robotics/jacket_follower
for s in "$@"; do
  echo "######## $s"
  bash ros2_setup/run_scenario.sh $s ${DUR:-75} | grep -v -e Lazy -e 'process has died'
  awk -F, 'NR==1 || (NR-2)%20==0' results/sim/$s/run.csv | column -t -s,
done
