"""Grab one frame from each camera (/dev/video0 and /dev/video2) with a sharpness score."""
import cv2

for idx in (0, 2):
    cap = cv2.VideoCapture(idx)
    cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
    ok, frame = False, None
    for _ in range(15):
        ok, frame = cap.read()
    cap.release()
    if not ok:
        print("video%d: read failed" % idx)
        continue
    sharp = cv2.Laplacian(cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY), cv2.CV_64F).var()
    path = "/home/pi/cam%d.jpg" % idx
    print("video%d: sharpness=%.0f saved=%s" % (idx, sharp, cv2.imwrite(path, frame)))
