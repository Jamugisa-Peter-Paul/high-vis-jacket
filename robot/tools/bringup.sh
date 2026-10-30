#!/bin/bash
# After every robot power-up: pause Hiwonder's app, report health and cameras.
sudo systemctl stop masterpi
echo "uptime: $(uptime -p) | masterpi: $(systemctl is-active masterpi) | $(vcgencmd get_throttled)"
cd /home/pi/MasterPi
sudo python3 -c "import sys; sys.path.append('/home/pi/MasterPi'); import HiwonderSDK.Board as B; print('battery mV:', [B.getBattery() for _ in range(3)])" 2>&1 | tail -1
echo "cameras: $(ls /dev/video[0-3] 2>/dev/null | tr '\n' ' ')"
