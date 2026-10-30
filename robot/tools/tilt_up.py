"""Tilt the camera up (servo 5) slowly so a standing person's vest is mid-frame."""
import sys, time
sys.path.append('/home/pi/MasterPi/')
import HiwonderSDK.Board as Board
Board.setPWMServoPulse(5, int(sys.argv[1]), 1500); time.sleep(1.7)
print('servo 5 ->', sys.argv[1])
