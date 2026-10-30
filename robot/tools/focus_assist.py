"""Focus helper: logs image sharpness for N seconds and keeps the sharpest frame. No motors or servos."""
import sys
import time
import cv2

secs = float(sys.argv[1]) if len(sys.argv) > 1 else 90
cap = cv2.VideoCapture(0)
cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
best, best_frame, t0, last = -1, None, time.time(), 0
with open('/home/pi/focus_log.txt', 'w') as log:
    while time.time() - t0 < secs:
        ok, frame = cap.read()
        if not ok:
            continue
        s = cv2.Laplacian(cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY), cv2.CV_64F).var()
        if s > best:
            best, best_frame = s, frame.copy()
        if time.time() - last >= 0.5:
            last = time.time()
            log.write("%5.1fs  sharpness=%6.0f  best=%6.0f\n" % (last - t0, s, best))
            log.flush()
            ok_w = cv2.imwrite('/home/pi/focus_latest.jpg', frame)
cap.release()
if best_frame is not None and cv2.imwrite('/home/pi/focus_best.jpg', best_frame):
    print("best sharpness %.0f saved to focus_best.jpg" % best)
else:
    print("no frame saved")
