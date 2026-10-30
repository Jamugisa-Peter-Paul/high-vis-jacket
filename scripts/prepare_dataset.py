"""Build the fine-tuning dataset (single class: safety_jacket).
train = original phone photos (re-labelled by the original model) + robot session 1, frames 1..CUT
val   = robot session 1, frames after CUT+GAP (a later block in time, so no near-duplicate frames leak across).
A separate robot session recorded elsewhere becomes the final test set."""
import random
import shutil
from pathlib import Path

import cv2
from ultralytics import YOLO

ROOT = Path(__file__).resolve().parents[1]
ORIG = Path(r"D:\mscs\intelligent_systems_and_robotics\final_project_model\Reflector Jacket Data")
S1 = ROOT / "data" / "labelled" / "session1_lab"
OUT = ROOT / "data" / "finetune"
CUT, GAP = 340, 10

if OUT.exists():
    shutil.rmtree(OUT)
for sp in ("train", "val"):
    (OUT / sp / "images").mkdir(parents=True)
    (OUT / sp / "labels").mkdir(parents=True)

# 1) robot frames, split by time
frames = sorted((S1 / "images").glob("*.jpg"))
n_tr = n_va = 0
for f in frames:
    idx = int(f.stem.split("_")[-1])
    sp = "train" if idx <= CUT else ("val" if idx > CUT + GAP else None)
    if sp is None:
        continue
    shutil.copy2(f, OUT / sp / "images" / f.name)
    shutil.copy2(S1 / "labels" / (f.stem + ".txt"), OUT / sp / "labels" / (f.stem + ".txt"))
    n_tr += sp == "train"
    n_va += sp == "val"

# 2) original phone photos: downscale, re-label with the original model (classes merged), train split only
model = YOLO(str(ROOT / "models" / "original_best_jacket.pt"))
kept = skipped = 0
for f in sorted(ORIG.glob("*.jpg")):
    img = cv2.imread(str(f))
    if img is None:
        skipped += 1
        continue
    s = 1280 / max(img.shape[:2])
    img = cv2.resize(img, None, fx=s, fy=s, interpolation=cv2.INTER_AREA) if s < 1 else img
    H, W = img.shape[:2]
    r = model.predict(img, imgsz=640, conf=0.35, agnostic_nms=True, iou=0.5, verbose=False)[0]
    if len(r.boxes) == 0:
        skipped += 1
        continue
    name = "orig_" + f.stem.replace("(", "_").replace(")", "")
    cv2.imwrite(str(OUT / "train" / "images" / (name + ".jpg")), img, [cv2.IMWRITE_JPEG_QUALITY, 92])
    with open(OUT / "train" / "labels" / (name + ".txt"), "w") as fh:
        for x1, y1, x2, y2 in r.boxes.xyxy.cpu().numpy():
            fh.write("0 %.6f %.6f %.6f %.6f\n" % ((x1 + x2) / 2 / W, (y1 + y2) / 2 / H, (x2 - x1) / W, (y2 - y1) / H))
    kept += 1

(OUT / "data.yaml").write_text(
    f"path: {OUT.as_posix()}\ntrain: train/images\nval: val/images\nnames:\n  0: safety_jacket\n")
print(f"robot frames: train {n_tr}, val {n_va} | original photos kept {kept}, skipped {skipped}")
