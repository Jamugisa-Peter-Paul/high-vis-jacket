"""Create Gazebo actor variants from Fuel's 'Male visitor' (CC-BY 4.0, Open Robotics):
  worker_vest   : shirt recoloured fluorescent yellow-green + two silver reflective bands (the target)
  visitor_plain : original purple shirt (distractor: person without a vest)
  visitor_orange: orange shirt, no reflective bands (hard distractor: hi-vis-like colour, not a vest)"""
import shutil
from pathlib import Path

import cv2
import numpy as np

PKG = Path(__file__).resolve().parents[1] / "ros2_ws" / "src" / "jacket_follower"
SRC = PKG / "models_src" / "Male_visitor"
OUT = PKG / "models"

tex = cv2.imread(str(SRC / "materials" / "textures" / "MaleVisitor.png"))
hsv = cv2.cvtColor(tex, cv2.COLOR_BGR2HSV)
shirt = cv2.inRange(hsv, (120, 60, 40), (160, 255, 255))                 # purple shirt pixels
shirt = cv2.morphologyEx(shirt, cv2.MORPH_CLOSE, np.ones((5, 5), np.uint8))


def recolour(hue, sat, val_gain):
    h = hsv.copy()
    m = shirt > 0
    h[..., 0][m] = hue
    h[..., 1][m] = sat
    h[..., 2][m] = np.clip(hsv[..., 2][m].astype(np.float32) * val_gain, 0, 255).astype(np.uint8)
    return cv2.cvtColor(h, cv2.COLOR_HSV2BGR)


def add_bands(img):
    """Two horizontal silver bands across each shirt piece (front and back of the vest)."""
    n, lab, st, _ = cv2.connectedComponentsWithStats(shirt)
    for i in range(1, n):
        x, y, w, h, a = st[i]
        if a < 20000:                     # skip the small sleeve-edge fragments
            continue
        for frac in (0.55, 0.72):
            y0, y1 = int(y + frac * h), int(y + frac * h + 0.045 * h)
            band = (lab[y0:y1, x:x + w] == i)
            img[y0:y1, x:x + w][band] = (200, 200, 200)
    return img


variants = {
    "worker_vest": add_bands(recolour(38, 235, 1.9)),     # OpenCV hue 38 ~ 76 deg: fluorescent yellow-green
    "visitor_plain": tex.copy(),
    "visitor_orange": recolour(12, 230, 1.8),
}
for name, img in variants.items():
    d = OUT / name
    if d.exists():
        shutil.rmtree(d)
    shutil.copytree(SRC, d)
    cv2.imwrite(str(d / "materials" / "textures" / "MaleVisitor.png"), img)
    (d / "model.config").write_text(
        f"<?xml version='1.0'?>\n<model>\n  <name>{name}</name>\n  <version>1.0</version>\n  <sdf version='1.7'>model.sdf</sdf>\n"
        "  <author><name>Open Robotics (original), recoloured for jacket_follower</name></author>\n"
        "  <description>Walking actor derived from Fuel 'Male visitor' (CC-BY 4.0).</description>\n</model>\n")
    small = cv2.resize(img, (256, 256))
    cv2.imwrite(str(Path(__file__).resolve().parents[1] / "results" / f"texture_{name}.png"), small)
print("created:", list(variants))
