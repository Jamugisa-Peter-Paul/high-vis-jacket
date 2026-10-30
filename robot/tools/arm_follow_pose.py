"""Move the MasterPi arm to the forward-looking camera pose used by Hiwonder's Avoidance mode, then grab one camera frame."""
import sys
import time
sys.path.append('/home/pi/MasterPi/')
import cv2
import HiwonderSDK.Board as Board
from ArmIK.ArmMoveIK import ArmIK

pitch = float(sys.argv[1]) if len(sys.argv) > 1 else 0.0   # 0 = camera level; positive tilts it up
AK = ArmIK()
Board.setPWMServoPulse(1, 1500, 800)                        # gripper neutral
res = AK.setPitchRangeMoving((0, 6, 18), pitch, -90, 90, 1500)
print("IK result:", res)
time.sleep(2.0)

cap = cv2.VideoCapture(0)
cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
for _ in range(10):                                         # let auto-exposure settle
    ok, frame = cap.read()
cap.release()
if ok:
    cv2.imwrite('/home/pi/follow_view.jpg', frame)
    print("frame saved", frame.shape)
else:
    print("camera read failed")
