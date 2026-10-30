"""Save robot-camera frames from Gazebo every 2 s and run both detectors on them (robot stays still)."""
import sys
import time
from pathlib import Path

import cv2
import numpy as np
import rclpy
from cv_bridge import CvBridge
from rclpy.node import Node
from rclpy.qos import qos_profile_sensor_data
from sensor_msgs.msg import Image
from ultralytics import YOLO

OUT = Path(sys.argv[1] if len(sys.argv) > 1 else "/mnt/d/mscs/intelligent_systems_and_robotics/jacket_follower/results/sim_peek")
OUT.mkdir(parents=True, exist_ok=True)
DUR = float(sys.argv[2]) if len(sys.argv) > 2 else 30


class Peek(Node):
    def __init__(self):
        super().__init__("sim_peek")
        self.b = CvBridge()
        self.last, self.frames = 0.0, []
        self.create_subscription(Image, "/camera/image_raw", self.cb, qos_profile_sensor_data)

    def cb(self, m):
        if time.time() - self.last >= 2.0:
            self.last = time.time()
            self.frames.append(self.b.imgmsg_to_cv2(m, "bgr8"))


rclpy.init()
n = Peek()
t0 = time.time()
while time.time() - t0 < DUR:
    rclpy.spin_once(n, timeout_sec=0.1)
print("frames:", len(n.frames))
models = {"v2": YOLO("/root/jacket_follower/models/jacket_finetuned_v2.pt"),
          "orig": YOLO("/root/jacket_follower/models/original_best_jacket.pt")}
tiles = []
for i, f in enumerate(n.frames):
    cv2.imwrite(str(OUT / f"sim_{i:02d}.jpg"), f)
    row = []
    for name, m in models.items():
        r = m.predict(f, imgsz=320, conf=0.25, verbose=False)[0]
        im = r.plot()
        cv2.putText(im, f"{name}: {len(r.boxes)} det", (8, 470), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 255, 255), 2)
        row.append(cv2.resize(im, (320, 240)))
        if name == "v2":
            print(f"frame {i}: v2 {[round(float(c), 2) for c in r.boxes.conf]}")
    tiles.append(np.hstack(row))
if tiles:
    cv2.imwrite(str(OUT / "sheet.jpg"), np.vstack(tiles[:8]))
rclpy.shutdown()
