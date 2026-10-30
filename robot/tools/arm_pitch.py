"""Set the arm's camera pitch (degrees; 0 = level, positive = up) at Hiwonder's forward pose. Servos only."""
import sys
sys.path.append('/home/pi/MasterPi/')
import time
from ArmIK.ArmMoveIK import ArmIK

pitch = float(sys.argv[1]) if len(sys.argv) > 1 else 0.0
res = ArmIK().setPitchRangeMoving((0, 6, 18), pitch, -90, 90, 1000)
print("pitch", pitch, "->", res)
time.sleep(1.2)
