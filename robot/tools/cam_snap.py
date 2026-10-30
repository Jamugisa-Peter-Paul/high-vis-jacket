"""Grab one camera frame on the robot (no motors, no servos). Usage: python3 cam_snap.py [out.jpg]"""
import sys
import cv2

out = sys.argv[1] if len(sys.argv) > 1 else '/home/pi/follow_view.jpg'
cap = cv2.VideoCapture(0)
cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
ok, frame = False, None
for _ in range(15):          # let auto-exposure settle
    ok, frame = cap.read()
cap.release()
if ok:
    cv2.imwrite(out, frame)
    sharp = cv2.Laplacian(cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY), cv2.CV_64F).var()
    print("saved", out, frame.shape, "sharpness=%.0f" % sharp)
else:
    print("camera read failed")
