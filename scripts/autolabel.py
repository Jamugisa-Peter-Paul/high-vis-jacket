"""Draft YOLO labels (single class 'safety_jacket') for robot-camera frames.
1) original model (class-agnostic NMS, both old classes merged)  2) hi-vis colour fallback for frames it missed.
Writes labels next to a copy of the images and saves review sheets of the fallback boxes."""
import shutil
import sys
from pathlib import Path

import cv2
import numpy as np
from ultralytics import YOLO

ROOT = Path(__file__).resolve().parents[1]
session = sys.argv[1] if len(sys.argv) > 1 else "session1_lab"
SRC = ROOT / "data" / "raw" / session
DST = ROOT / "data" / "labelled" / session
(DST / "images").mkdir(parents=True, exist_ok=True)
(DST / "labels").mkdir(parents=True, exist_ok=True)
REVIEW = ROOT / "results" / "autolabel" / session
REVIEW.mkdir(parents=True, exist_ok=True)
CROP_Y = 430                       # gripper fingertips below this row are ignored

model = YOLO(str(ROOT / "models" / "original_best_jacket.pt"))


def colour_box(img):
    """Largest fluorescent yellow-green blob above the gripper, or None."""
    hsv = cv2.cvtColor(img, cv2.COLOR_BGR2HSV)
    # range measured from the jacket pixels inside the original model's boxes (median hue 49)
    mask = cv2.inRange(hsv, (36, 80, 120), (62, 255, 255))
    mask[CROP_Y:] = 0
    mask = cv2.morphologyEx(mask, cv2.MORPH_OPEN, np.ones((3, 3), np.uint8))
    mask = cv2.morphologyEx(mask, cv2.MORPH_CLOSE, np.ones((9, 9), np.uint8))
    n, _, stats, _ = cv2.connectedComponentsWithStats(mask)
    if n < 2:
        return None
    i = 1 + int(np.argmax(stats[1:, cv2.CC_STAT_AREA]))
    x, y, w, h, area = stats[i]
    if area < 250:
        return None
    return float(x), float(y), float(x + w), float(y + h)


counts = {"model": 0, "colour": 0, "empty": 0}
fallback = []
for f in sorted(SRC.glob("*.jpg")):
    img = cv2.imread(str(f))
    H, W = img.shape[:2]
    r = model.predict(img, imgsz=320, conf=0.25, agnostic_nms=True, iou=0.5, verbose=False)[0]
    boxes = [tuple(map(float, b)) for b in r.boxes.xyxy.cpu().numpy()] if len(r.boxes) else []
    src = "model"
    if not boxes:
        cb = colour_box(img)
        boxes, src = ([cb], "colour") if cb else ([], "empty")
    counts[src] += 1
    shutil.copy2(f, DST / "images" / f.name)
    with open(DST / "labels" / (f.stem + ".txt"), "w") as fh:
        for x1, y1, x2, y2 in boxes:
            fh.write("0 %.6f %.6f %.6f %.6f\n" % ((x1 + x2) / 2 / W, (y1 + y2) / 2 / H, (x2 - x1) / W, (y2 - y1) / H))
    if src != "model":
        vis = img.copy()
        for x1, y1, x2, y2 in boxes:
            cv2.rectangle(vis, (int(x1), int(y1)), (int(x2), int(y2)), (0, 0, 255), 3)
        cv2.putText(vis, "%s %s" % (f.stem[-5:], src), (8, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.9, (0, 0, 255), 2)
        fallback.append(cv2.resize(vis, (320, 240)))

print(session, counts)
for k in range(0, len(fallback), 16):
    page = fallback[k:k + 16]
    page += [np.zeros_like(page[0])] * (16 - len(page))
    sheet = np.vstack([np.hstack(page[i:i + 4]) for i in range(0, 16, 4)])
    cv2.imwrite(str(REVIEW / ("fallback_%02d.jpg" % (k // 16))), sheet)
print("review sheets:", sorted(p.name for p in REVIEW.glob("fallback_*.jpg")))
