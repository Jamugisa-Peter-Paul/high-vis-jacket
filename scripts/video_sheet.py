"""Contact sheet of a scenario debug video: video_sheet.py <debug.mp4> <out.jpg> [t1 t2 ...] (seconds into the video)."""
import sys

import cv2
import numpy as np

src, out = sys.argv[1], sys.argv[2]
cap = cv2.VideoCapture(src)
fps = cap.get(cv2.CAP_PROP_FPS) or 10
n = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
times = [float(t) for t in sys.argv[3:]] or list(np.linspace(0, n / fps - 0.5, 12))
tiles = []
for t in times:
    cap.set(cv2.CAP_PROP_POS_FRAMES, int(t * fps))
    ok, f = cap.read()
    if not ok:
        continue
    f = cv2.resize(f, (480, int(480 * f.shape[0] / f.shape[1])))
    cv2.putText(f, f"video t={t:.0f}s", (8, f.shape[0] - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 2)
    tiles.append(f)
while len(tiles) % 4:
    tiles.append(np.zeros_like(tiles[0]))
rows = [np.hstack(tiles[i:i + 4]) for i in range(0, len(tiles), 4)]
cv2.imwrite(out, np.vstack(rows))
print(f"{n} frames @ {fps:.1f} fps -> {out}")
