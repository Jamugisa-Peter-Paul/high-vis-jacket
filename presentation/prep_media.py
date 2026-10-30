"""Crops and video poster frames for the final deck -> presentation/media/."""
from pathlib import Path

import cv2

P = Path(__file__).resolve().parents[1]
M = P / "presentation" / "media"
M.mkdir(exist_ok=True)


def poster(video, t, out):
    v = cv2.VideoCapture(str(P / video))
    v.set(cv2.CAP_PROP_POS_FRAMES, int(t * (v.get(cv2.CAP_PROP_FPS) or 10)))
    ok, f = v.read()
    assert ok, video
    cv2.imwrite(str(M / out), f)
    print(out, f.shape)


poster("results/real/following.mp4", 12, "poster_following.jpg")
poster("results/real/highlights.mp4", 8.6, "poster_highlights.jpg")
poster("results/real/search.mp4", 13, "poster_search.jpg")
poster("results/sim/s3_challenge/debug.mp4", 24, "poster_sim_s3.jpg")
review = cv2.imread(str(P / "results/robot_test_review/review_00.jpg"))
cv2.imwrite(str(M / "robot_labels_crop.jpg"), review[0:480, 0:960])
lab = cv2.imread(str(P / "results/real/photos/16.jpg"))
cv2.imwrite(str(M / "robot_lab.jpg"), lab)
print("done")
