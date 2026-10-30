#!/bin/bash
d=/mnt/d/mscs/intelligent_systems_and_robotics/jacket_follower/results/sim/${1:-s1_normal}
ls -la $d
echo "== csv rows: $(wc -l < $d/run.csv 2>/dev/null)"
echo "== states"; cut -d, -f10 $d/run.csv 2>/dev/null | sort | uniq -c
echo "== transitions"; grep -E " -> " $d/launch.log 2>/dev/null | sed 's/.*\] //' | head -20
echo "== errors"; grep -iE "error|traceback|exception" $d/launch.log 2>/dev/null | head -8
echo "== recorder"; cat $d/record.log 2>/dev/null
