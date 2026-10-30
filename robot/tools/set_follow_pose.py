"""Move the arm to the calibrated follow pose stored in /home/pi/follow_pose.json. Servos only."""
import json
import sys
sys.path.append('/home/pi/MasterPi/')
import time
import HiwonderSDK.Board as Board

pose = json.load(open('/home/pi/follow_pose.json'))['servo_pulses']
for sid in ('6', '5', '4', '3'):
    Board.setPWMServoPulse(int(sid), int(pose[sid]), 1000)
time.sleep(1.2)
print('follow pose set:', pose)
