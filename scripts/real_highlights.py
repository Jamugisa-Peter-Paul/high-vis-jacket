"""Cut the moments where the real robot detects / follows the vest into one titled video for the demo.
   py scripts/real_highlights.py   -> results/real/highlights.mp4"""
from pathlib import Path

import cv2
import numpy as np

R = Path(__file__).resolve().parents[1] / "results" / "real"
CLIPS = [  # (run, start s, end s, caption) - windows where the debug video shows a detection box
    ("run2", 4.0, 8.5, "Run 2 (home): robot turned to find the vest (0.84) -> FOLLOW"),
    ("run5", 7.5, 13.0, "Run 5 (lab): search -> vest found -> FOLLOW / re-acquire"),
    ("run6", 0.0, 2.5, "Run 6 (lab): vest on a chair detected (0.72) -> FOLLOW"),
]
W, H, FPS = 640, 480, 10
out = cv2.VideoWriter(str(R / "highlights.mp4"), cv2.VideoWriter_fourcc(*"mp4v"), FPS, (W, H))


def card(text, secs=2):
    img = np.zeros((H, W, 3), np.uint8)
    for i, line in enumerate(text.split("\n")):
        cv2.putText(img, line, (30, 200 + 40 * i), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (255, 255, 255), 2)
    for _ in range(secs * FPS):
        out.write(img)


card("Safety-jacket follower on the\nHiwonder MasterPi (real robot)\nrobot camera view + follower state", 3)
for run, a, b, cap in CLIPS:
    v = cv2.VideoCapture(str(R / run / "debug.mp4"))
    fps = v.get(cv2.CAP_PROP_FPS) or FPS
    v.set(cv2.CAP_PROP_POS_FRAMES, int(a * fps))
    card(cap.replace(": ", ":\n", 1), 2)
    for _ in range(int((b - a) * fps)):
        ok, f = v.read()
        if not ok:
            break
        f = cv2.resize(f, (W, H))
        cv2.rectangle(f, (0, H - 34), (W, H), (0, 0, 0), -1)
        cv2.putText(f, cap, (8, H - 11), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 1)
        out.write(f)
out.release()
print("written", R / "highlights.mp4")
