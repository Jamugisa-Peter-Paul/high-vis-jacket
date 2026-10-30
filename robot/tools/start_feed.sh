#!/bin/bash
# stop older camera users (match the python process only)
for p in $(pgrep -f "python3 /home/pi/(live_feed|focus_assist).py"); do kill "$p"; done
sleep 0.5
setsid nohup python3 /home/pi/live_feed.py > /home/pi/live_feed.log 2>&1 < /dev/null &
sleep 4
if pgrep -f "python3 /home/pi/live_feed.py" > /dev/null; then echo "RUNNING, sharpness=$(cat /tmp/sharpness.txt 2>/dev/null)"; else echo "FAILED"; tail -5 /home/pi/live_feed.log; fi
