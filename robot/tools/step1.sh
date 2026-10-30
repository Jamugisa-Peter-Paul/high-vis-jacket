echo "== power before"; vcgencmd get_throttled; vcgencmd measure_volts core
echo "== stopping masterpi"; sudo systemctl stop masterpi; sleep 2; systemctl is-active masterpi
echo "== battery"; cd ~/MasterPi && python3 -c "import sys; sys.path.append('/home/pi/MasterPi'); import HiwonderSDK.Board as B; print('battery mV:', B.getBattery())" 2>&1 | tail -1
echo "== cpu now"; top -bn1 | head -5 | tail -3
echo "== camera free?"; fuser /dev/video0 2>&1 || echo "no process using camera"
echo "== arm poses used by Hiwonder"; grep -rn "setPitchRangeMoving\|setPWMServoPulse(1\|setPWMServoPulse(6\|initMove" Functions/Running.py Functions/ColorTracking.py Functions/Avoidance.py MasterPi.py 2>/dev/null | head -25
