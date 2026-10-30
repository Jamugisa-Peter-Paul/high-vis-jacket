"""Second-opinion labels with Grounding DINO for frames the original YOLO model missed.
Replaces their colour-fallback labels and saves a review sheet."""
import json
import sys
from pathlib import Path

import cv2
import numpy as np
import torch
from PIL import Image
from ultralytics import YOLO
from transformers import AutoModelForZeroShotObjectDetection, AutoProcessor

ROOT = Path(__file__).resolve().parents[1]
session = sys.argv[1] if len(sys.argv) > 1 else "session1_lab"
D = ROOT / "data" / "labelled" / session
REVIEW = ROOT / "results" / "autolabel" / session
CROP_Y = 430
PROMPT = "a high visibility safety vest."
BOX_T, TEXT_T = 0.30, 0.25

dev = "cuda" if torch.cuda.is_available() else "cpu"
mid = "IDEA-Research/grounding-dino-base"
proc = AutoProcessor.from_pretrained(mid)
dino = AutoModelForZeroShotObjectDetection.from_pretrained(mid).to(dev).eval()
yolo = YOLO(str(ROOT / "models" / "original_best_jacket.pt"))

missed = []
for img_path in sorted((D / "images").glob("*.jpg")):
    r = yolo.predict(str(img_path), imgsz=320, conf=0.25, agnostic_nms=True, verbose=False)[0]
    if len(r.boxes) == 0:
        missed.append(img_path)
print(f"{len(missed)} frames missed by the original model")

stats, tiles = {"dino": 0, "empty": 0}, []
for img_path in missed:
    pil = Image.open(img_path).convert("RGB")
    W, H = pil.size
    inputs = proc(images=pil, text=PROMPT, return_tensors="pt").to(dev)
    with torch.no_grad():
        out = dino(**inputs)
    res = proc.post_process_grounded_object_detection(out, inputs.input_ids, threshold=BOX_T,
                                                      text_threshold=TEXT_T, target_sizes=[(H, W)])[0]
    boxes = []
    for (x1, y1, x2, y2), s in zip(res["boxes"].tolist(), res["scores"].tolist()):
        if y1 >= CROP_Y or (x2 - x1) * (y2 - y1) > 0.6 * W * H:     # gripper or whole-frame boxes
            continue
        boxes.append((x1, y1, x2, y2, s))
    # 1) the box must actually contain hi-vis colour (rejects the red chair, empty background)
    bgr = cv2.imread(str(img_path))
    hv = cv2.inRange(cv2.cvtColor(bgr, cv2.COLOR_BGR2HSV), (30, 45, 80), (70, 255, 255))
    def hivis_frac(b):
        x1, y1, x2, y2 = (int(round(v)) for v in b[:4])
        roi = hv[max(0, y1):y2, max(0, x1):x2]
        return float((roi > 0).mean()) if roi.size else 0.0
    boxes = [b for b in boxes if hivis_frac(b) >= 0.08]
    # 2) if one box contains another, it is the whole-person box: keep the inner (vest) box
    def contains(a, b):
        return a[0] <= b[0] + 4 and a[1] <= b[1] + 4 and a[2] >= b[2] - 4 and a[3] >= b[3] - 4
    boxes = [a for a in boxes if not any(a is not b and contains(a, b) for b in boxes)]
    # 3) jacket cut off at the frame edge (very close person): fall back to the hi-vis blob
    if not boxes:
        n, _, st, _ = cv2.connectedComponentsWithStats(cv2.morphologyEx(hv[:CROP_Y], cv2.MORPH_CLOSE, np.ones((9, 9), np.uint8)))
        if n > 1:
            i = 1 + int(np.argmax(st[1:, cv2.CC_STAT_AREA]))
            x, y, w, h, a = st[i]
            if a > 1500:
                boxes = [(x, y, x + w, y + h, 0.0)]
    boxes.sort(key=lambda b: -b[4])
    boxes = boxes[:1]
    stats["dino" if boxes else "empty"] += 1
    with open(D / "labels" / (img_path.stem + ".txt"), "w") as fh:
        for x1, y1, x2, y2, _ in boxes:
            fh.write("0 %.6f %.6f %.6f %.6f\n" % ((x1 + x2) / 2 / W, (y1 + y2) / 2 / H, (x2 - x1) / W, (y2 - y1) / H))
    vis = cv2.imread(str(img_path))
    for x1, y1, x2, y2, s in boxes:
        cv2.rectangle(vis, (int(x1), int(y1)), (int(x2), int(y2)), (0, 0, 255), 3)
        cv2.putText(vis, "%.2f" % s, (int(x1), int(y1) - 6), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 0, 255), 2)
    cv2.putText(vis, img_path.stem[-5:], (8, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.9, (0, 255, 255), 2)
    tiles.append(cv2.resize(vis, (320, 240)))

print(session, stats)
for p in REVIEW.glob("*.jpg"):
    p.unlink()
for k in range(0, len(tiles), 16):
    page = tiles[k:k + 16] + [np.zeros((240, 320, 3), np.uint8)] * (16 - len(tiles[k:k + 16]))
    cv2.imwrite(str(REVIEW / ("dino_%02d.jpg" % (k // 16))), np.vstack([np.hstack(page[i:i + 4]) for i in range(0, 16, 4)]))
json.dump({"missed": [p.name for p in missed], "stats": stats}, open(REVIEW / "dino_summary.json", "w"), indent=1)
