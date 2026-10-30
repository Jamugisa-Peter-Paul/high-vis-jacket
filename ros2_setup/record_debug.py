"""Record /jacket/debug_image (camera + boxes) with the follower state overlaid into an mp4."""
import sys
import time

import cv2
import rclpy
from cv_bridge import CvBridge
from rclpy.node import Node
from sensor_msgs.msg import Image
from std_msgs.msg import String

out, dur = sys.argv[1], float(sys.argv[2])


class Rec(Node):
    def __init__(self):
        super().__init__("debug_recorder")
        self.b, self.state, self.writer, self.n = CvBridge(), "", None, 0
        self.create_subscription(String, "/follower/state", lambda m: setattr(self, "state", m.data), 10)
        self.create_subscription(Image, "/jacket/debug_image", self.cb, 5)

    def cb(self, m):
        f = self.b.imgmsg_to_cv2(m, "bgr8")
        cv2.putText(f, self.state, (f.shape[1] - 190, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.9,
                    (0, 200, 0) if self.state == "FOLLOW" else (0, 0, 255), 2)
        if self.writer is None:
            self.writer = cv2.VideoWriter(out, cv2.VideoWriter_fourcc(*"mp4v"), 10, (f.shape[1], f.shape[0]))
        self.writer.write(f)
        self.n += 1


rclpy.init()
r = Rec()
t0 = time.time()
while time.time() - t0 < dur:
    rclpy.spin_once(r, timeout_sec=0.1)
if r.writer:
    r.writer.release()
print("frames recorded:", r.n)
rclpy.shutdown()
