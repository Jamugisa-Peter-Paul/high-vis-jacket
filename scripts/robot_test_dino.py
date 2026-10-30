"""Independent robot-camera test set: frames after the training cut, labelled ONLY by Grounding DINO
(+ hi-vis colour sanity rules), never by either YOLO model. Saves review sheets for a human check."""
import shutil
from pathlib import Path

import cv2
import numpy as np
import torch
from PIL import Image
from transformers import AutoModelForZeroShotObjectDetection, AutoProcessor

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "data" / "raw" / "session1_lab"
OUT = ROOT / "data" / "robot_test" / "session1_mid"
REVIEW = ROOT / "results" / "robot_test_review"
FIRST, LAST = 230, 330           # hard middle block (walking, side views, occlusion); training excludes 220-340
CROP_Y = 430

for p in (OUT, REVIEW):
    if p.exists():
        shutil.rmtree(p)
(OUT / "images").mkdir(parents=True)
(OUT / "labels").mkdir(parents=True)
REVIEW.mkdir(parents=True)

dev = "cuda" if torch.cuda.is_available() else "cpu"
mid = "IDEA-Research/grounding-dino-base"
proc = AutoProcessor.from_pretrained(mid)
dino = AutoModelForZeroShotObjectDetection.from_pretrained(mid).to(dev).eval()


def contains(a, b):
    return a[0] <= b[0] + 4 and a[1] <= b[1] + 4 and a[2] >= b[2] - 4 and a[3] >= b[3] - 4


tiles, n_pos = [], 0
frames = [f for f in sorted(SRC.glob("*.jpg")) if FIRST <= int(f.stem.split("_")[-1]) <= LAST]
for f in frames:
    pil = Image.open(f).convert("RGB")
    W, H = pil.size
    inp = proc(images=pil, text="a high visibility safety vest.", return_tensors="pt").to(dev)
    with torch.no_grad():
        o = dino(**inp)
    r = proc.post_process_grounded_object_detection(o, inp.input_ids, threshold=0.30, text_threshold=0.25, target_sizes=[(H, W)])[0]
    bgr = cv2.imread(str(f))
    hv = cv2.inRange(cv2.cvtColor(bgr, cv2.COLOR_BGR2HSV), (30, 45, 80), (70, 255, 255))
    boxes = []
    for (x1, y1, x2, y2), s in zip(r["boxes"].tolist(), r["scores"].tolist()):
        if y1 >= CROP_Y or (x2 - x1) * (y2 - y1) > 0.6 * W * H:
            continue
        roi = hv[max(0, int(y1)):int(y2), max(0, int(x1)):int(x2)]
        if roi.size and (roi > 0).mean() >= 0.08:
            boxes.append((x1, y1, x2, y2, s))
    boxes = [a for a in boxes if not any(a is not b and contains(a, b) for b in boxes)]
    boxes = sorted(boxes, key=lambda b: -b[4])[:2]
    shutil.copy2(f, OUT / "images" / f.name)
    with open(OUT / "labels" / (f.stem + ".txt"), "w") as fh:
        for x1, y1, x2, y2, _ in boxes:
            fh.write("0 %.6f %.6f %.6f %.6f\n" % ((x1 + x2) / 2 / W, (y1 + y2) / 2 / H, (x2 - x1) / W, (y2 - y1) / H))
    n_pos += bool(boxes)
    vis = bgr.copy()
    for x1, y1, x2, y2, s in boxes:
        cv2.rectangle(vis, (int(x1), int(y1)), (int(x2), int(y2)), (0, 0, 255), 3)
    cv2.putText(vis, f.stem[-5:] + ("" if boxes else " EMPTY"), (8, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.9, (0, 255, 255), 2)
    tiles.append(cv2.resize(vis, (320, 240)))

for k in range(0, len(tiles), 20):
    page = tiles[k:k + 20] + [np.zeros((240, 320, 3), np.uint8)] * (20 - len(tiles[k:k + 20]))
    cv2.imwrite(str(REVIEW / ("review_%02d.jpg" % (k // 20))), np.vstack([np.hstack(page[i:i + 5]) for i in range(0, 20, 5)]))
(OUT / "data.yaml").write_text(f"path: {OUT.as_posix()}\ntrain: images\nval: images\nnames:\n  0: safety_jacket\n")
print(f"robot test: {len(frames)} frames, {n_pos} with a jacket box, {len(frames) - n_pos} empty")
