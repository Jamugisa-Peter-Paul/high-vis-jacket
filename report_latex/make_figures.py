"""Figures for the final report -> report_latex/figures/."""
import shutil
from pathlib import Path

import cv2
import numpy as np

P = Path(__file__).resolve().parents[1]
F = P / "report_latex" / "figures"
F.mkdir(exist_ok=True)
M = P / "presentation" / "media"


def frame(video, t):
    v = cv2.VideoCapture(str(P / video))
    v.set(cv2.CAP_PROP_POS_FRAMES, int(t * (v.get(cv2.CAP_PROP_FPS) or 10)))
    ok, f = v.read()
    assert ok, (video, t)
    return f


# dataset: robot-camera frames with checked labels
shutil.copy(M / "robot_labels_crop.jpg", F / "robot_labels.jpg")
# Gazebo: robot camera in scenario 3 + scenario-2 ground-truth plot
shutil.copy(M / "poster_sim_s3.jpg", F / "sim_s3_view.jpg")
shutil.copy(P / "results/sim/s2_speed/analysis.png", F / "sim_s2_analysis.png")
shutil.copy(P / "results/sim/s3_challenge/analysis.png", F / "sim_s3_analysis.png")
# real robot: lab photo + robot-view strip (vest detected -> FOLLOW) from three runs
lab = cv2.imread(str(P / "results/real/photos/16.jpg"))
cv2.imwrite(str(F / "robot_lab.jpg"), cv2.resize(lab, (800, int(800 * lab.shape[0] / lab.shape[1]))))
tiles = []
for video, t, label in (("results/real/run2/debug.mp4", 6.0, "Run 2 (home)"),
                        ("results/real/run5/debug.mp4", 9.5, "Run 5 (lab)"),
                        ("results/real/run6/debug.mp4", 1.0, "Run 6 (lab, vest on chair)")):
    f = cv2.resize(frame(video, t), (480, 360))
    cv2.rectangle(f, (0, 330), (480, 360), (0, 0, 0), -1)
    cv2.putText(f, label, (8, 352), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 1, cv2.LINE_AA)
    tiles.append(f)
strip = np.hstack([np.pad(t, ((0, 0), (0, 6), (0, 0)), constant_values=255) for t in tiles])[:, :-6]
cv2.imwrite(str(F / "real_follow_strip.jpg"), strip)
shutil.copy(Path(r"D:\mscs\intelligent_systems_and_robotics\birds-cnn\report_latex\UCULOGO (1).png"), P / "report_latex" / "UCULOGO.png")
print("figures:", sorted(p.name for p in F.iterdir()))
