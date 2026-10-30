"""Run the ORIGINAL jacket model on robot-camera frames: detection rate, confidence, and an example sheet.
This is the 'before fine-tuning' baseline."""
from pathlib import Path

import cv2
import numpy as np
from ultralytics import YOLO

ROOT = Path(__file__).resolve().parents[1]
MODEL = ROOT / "models" / "original_best_jacket.pt"
FRAMES = sorted((ROOT / "data" / "raw" / "session1_lab").glob("*.jpg"))
OUT = ROOT / "results" / "baseline"
OUT.mkdir(parents=True, exist_ok=True)

model = YOLO(str(MODEL))
print("classes:", model.names)
for imgsz in (640, 320):
    found, confs = 0, []
    for f in FRAMES:
        r = model.predict(str(f), imgsz=imgsz, conf=0.25, verbose=False)[0]
        if len(r.boxes):
            found += 1
            confs.append(float(r.boxes.conf.max()))
    print(f"imgsz={imgsz}: jacket found in {found}/{len(FRAMES)} frames ({found / len(FRAMES):.1%}), "
          f"median confidence {np.median(confs) if confs else 0:.2f}")

# example sheet at the deployment size (320)
pick = FRAMES[::max(1, len(FRAMES) // 12)][:12]
tiles = []
for f in pick:
    r = model.predict(str(f), imgsz=320, conf=0.25, verbose=False)[0]
    im = r.plot(line_width=2)
    tiles.append(cv2.resize(im, (320, 240)))
rows = [np.hstack(tiles[i:i + 4]) for i in range(0, 12, 4)]
cv2.imwrite(str(OUT / "baseline_examples_320.jpg"), np.vstack(rows))
print("saved", OUT / "baseline_examples_320.jpg")
