sudo systemctl stop masterpi; sleep 1; echo "masterpi: $(systemctl is-active masterpi)"
cd ~/MasterPi
sudo python3 -c "import sys; sys.path.append('/home/pi/MasterPi'); import HiwonderSDK.Board as B; print('battery mV:', [B.getBattery() for _ in range(3)])" 2>&1 | tail -1
vcgencmd get_throttled
echo "== ArmIK signature"; grep -n "def setPitchRangeMoving" -A 12 ArmIK/ArmMoveIK.py | head -16
echo "== servo1 in ColorTracking"; grep -n "^servo1\|servo1 =" Functions/Avoidance.py Functions/ColorTracking.py | head
