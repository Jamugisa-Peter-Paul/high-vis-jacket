#!/bin/bash
# (Re)start the follower server on the robot, detached from the SSH session.
for p in $(pgrep -f "python3 /home/pi/masterpi_server.py"); do sudo kill $p; done
sleep 1
sudo setsid nohup python3 /home/pi/masterpi_server.py > /tmp/mps.log 2>&1 < /dev/null &
sleep 7
cat /tmp/mps.log
pgrep -af "python3 /home/pi/masterpi_server.py"
