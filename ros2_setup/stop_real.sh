#!/bin/bash
# Stop every follower process on the laptop (the robot itself stops within 0.5 s once commands stop).
for pat in "ros2 launch jacket_follower" "lib/jacket_follower/" "rqt_image_view" "probe_real.py" "record_debug.py" "live_run.sh"; do
  for p in $(pgrep -f "$pat"); do [ "$p" != "$$" ] && kill -9 "$p" 2>/dev/null; done
done
sleep 1
echo "still running: $(pgrep -fc 'lib/jacket_follower/')"
