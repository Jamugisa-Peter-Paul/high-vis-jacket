"""Find PWM servo pulses that reproduce a reference camera view.
Moves ONLY the arm (servos 3-6). Compares each frame with the reference using ORB features + RANSAC
on the static background, learns how each servo shifts the image, and iterates towards zero shift."""
import io
import json
import sys
import time
from pathlib import Path

import cv2
import numpy as np
import paramiko

HERE = Path(__file__).parent
REF = cv2.imread(str(HERE / "ref_pose.jpg"), cv2.IMREAD_GRAYSCALE)
CROP = 430                                    # ignore the gripper fingertips at the bottom

ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect("192.168.149.1", username="pi", password="raspberry", timeout=8, look_for_keys=False, allow_agent=False)
sftp = ssh.open_sftp()


def run(cmd):
    _, out, err = ssh.exec_command(cmd, timeout=60)
    return out.read().decode(errors="replace") + err.read().decode(errors="replace")


def pose_and_snap(p):
    p = [int(max(500, min(2500, v))) for v in p]
    run("cd /home/pi/MasterPi && sudo python3 /home/pi/arm_servos.py %d %d %d %d >/dev/null 2>&1" % tuple(p))
    run("python3 /home/pi/cam_snap.py /home/pi/cal.jpg >/dev/null 2>&1")
    buf = io.BytesIO()
    sftp.getfo("/home/pi/cal.jpg", buf)
    img = cv2.imdecode(np.frombuffer(buf.getvalue(), np.uint8), cv2.IMREAD_GRAYSCALE)
    return p, img


orb = cv2.ORB_create(3000)
kr, dr = orb.detectAndCompute(REF[:CROP], None)
bf = cv2.BFMatcher(cv2.NORM_HAMMING, crossCheck=True)


def shift(img):
    """Median (dx, dy) in pixels that maps the current frame onto the reference (RANSAC inliers only)."""
    k, d = orb.detectAndCompute(img[:CROP], None)
    if d is None or len(k) < 20:
        return None
    m = sorted(bf.match(d, dr), key=lambda x: x.distance)[:400]
    if len(m) < 20:
        return None
    a = np.float32([k[x.queryIdx].pt for x in m])
    b = np.float32([kr[x.trainIdx].pt for x in m])
    H, inl = cv2.estimateAffinePartial2D(a, b, method=cv2.RANSAC, ransacReprojThreshold=4)
    if H is None or inl.sum() < 15:
        return None
    d = (b - a)[inl.ravel() == 1]
    return float(np.median(d[:, 0])), float(np.median(d[:, 1])), int(inl.sum())


log = []
p = [751, 2484, 734, 1500]
p, img = pose_and_snap(p)
s0 = shift(img)
print("start", p, "shift", s0)
log.append((p, s0))

# learn each tilt servo's effect on vertical shift, and base servo on horizontal shift
J = {}
for idx, step in ((0, 80), (1, -80), (2, 80), (3, 80)):
    q = list(p)
    q[idx] += step
    q, im = pose_and_snap(q)
    sq = shift(im)
    print("probe servo", idx + 3, q, "shift", sq)
    log.append((q, sq))
    if s0 and sq:
        J[idx] = ((sq[0] - s0[0]) / step, (sq[1] - s0[1]) / step)
    pose_and_snap(p)
print("sensitivity px/pulse (dx, dy):", {k + 3: (round(v[0], 3), round(v[1], 3)) for k, v in J.items()})

tilt = max((i for i in J if i < 3), key=lambda i: abs(J[i][1]), default=None)
if tilt is None or abs(J[tilt][1]) < 0.02 or s0 is None:
    print("no usable tilt servo found; stopping")
    sys.exit(1)
print("using servo", tilt + 3, "for tilt and servo 6 for pan")

cur, sc = p, s0
for it in range(8):
    dx, dy, n = sc
    if abs(dy) < 6 and abs(dx) < 8:
        break
    q = list(cur)
    q[tilt] += -dy / J[tilt][1] * 0.8
    if 3 in J and abs(J[3][0]) > 0.02:
        q[3] += -dx / J[3][0] * 0.8
    q, im = pose_and_snap(q)
    s = shift(im)
    print("iter", it, q, "shift", s)
    log.append((q, s))
    if s is None:
        break
    cur, sc = q, s

cv2.imwrite(str(HERE / "cal_final.jpg"), im)
json.dump({"pose": cur, "shift": sc, "log": log}, open(HERE / "cal_result.json", "w"), indent=1)
print("FINAL pose", cur, "residual shift", sc)
