"""Set arm PWM servos directly. Usage: sudo python3 arm_servos.py s3 s4 s5 [s6]  (pulse widths, 500-2500).
Servo 3 = wrist (camera tilt), 4 = elbow, 5 = shoulder, 6 = base rotation. Servos only."""
import sys
sys.path.append('/home/pi/MasterPi/')
import time
import HiwonderSDK.Board as Board

pulses = [int(v) for v in sys.argv[1:]]
ids = [3, 4, 5, 6][:len(pulses)]
for sid, p in zip(ids, pulses):
    p = max(500, min(2500, p))
    Board.setPWMServoPulse(sid, p, 800)
    print("servo %d -> %d" % (sid, p))
time.sleep(1.0)
