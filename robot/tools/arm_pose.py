"""Move the arm to (x, y, z) cm with a target camera pitch; prints what the IK solver reached. Servos only.
Usage: sudo python3 arm_pose.py y z pitch"""
import sys
sys.path.append('/home/pi/MasterPi/')
import time
from ArmIK.ArmMoveIK import ArmIK

y, z, pitch = (float(v) for v in sys.argv[1:4])
res = ArmIK().setPitchRangeMoving((0, y, z), pitch, -90, 90, 1000)
print("target y=%g z=%g pitch=%g ->" % (y, z, pitch), res if res is False else "servos %s, reached pitch %s" % (res[0], res[1]))
time.sleep(1.3)
