cd ~/MasterPi
for i in 1 2 3; do vcgencmd get_throttled; sleep 2; done
sudo python3 -c "import sys; sys.path.append('/home/pi/MasterPi'); import HiwonderSDK.Board as B; import time; v=[B.getBattery() for _ in range(3)]; print('battery mV:', v)" 2>&1 | tail -1
dmesg | grep -i -E "voltage|undervolt" | tail -3
