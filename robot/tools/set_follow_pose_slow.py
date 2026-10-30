"""Move the arm to the follow pose one servo at a time, slowly (low current: avoids battery brown-outs)."""
import json, sys, time
sys.path.append('/home/pi/MasterPi/')
import HiwonderSDK.Board as Board
pose = json.load(open('/home/pi/follow_pose.json'))['servo_pulses']
for sid in ('6', '5', '4', '3'):
    Board.setPWMServoPulse(int(sid), int(pose[sid]), 2000)
    time.sleep(2.2)
    print('servo', sid, '->', pose[sid], 'battery', Board.getBattery() / 1000, flush=True)
