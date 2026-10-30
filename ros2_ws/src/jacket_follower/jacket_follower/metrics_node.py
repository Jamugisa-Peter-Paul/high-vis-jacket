"""Scenario recorder (simulation): logs ground truth + robot behaviour to CSV at 10 Hz.

Columns: t (sim seconds), robot x/y/yaw, worker x/y, true distance robot->worker, distance estimated by the follower,
         worker speed, robot speed, follower state, #detections, largest box w/h (px), cmd_vel, inference ms.
Ground truth comes from Gazebo's OdometryPublisher on each model (world-frame pose),
bridged to /model/<name>/odometry as nav_msgs/Odometry.
"""
import csv
import math
import os

import rclpy
from geometry_msgs.msg import Twist
from nav_msgs.msg import Odometry
from rclpy.node import Node
from std_msgs.msg import Float32, String
from vision_msgs.msg import Detection2DArray


def yaw_of(q):
    return math.atan2(2 * (q.w * q.z + q.x * q.y), 1 - 2 * (q.y * q.y + q.z * q.z))


class Metrics(Node):
    def __init__(self):
        super().__init__("scenario_metrics")
        self.declare_parameter("out_csv", "/tmp/scenario.csv")
        self.declare_parameter("robot_name", "masterpi")
        self.declare_parameter("target_name", "worker")
        self.out = self.get_parameter("out_csv").value
        robot = self.get_parameter("robot_name").value
        target = self.get_parameter("target_name").value
        os.makedirs(os.path.dirname(self.out) or ".", exist_ok=True)
        self.f = open(self.out, "w", newline="")
        self.w = csv.writer(self.f)
        self.w.writerow(["t", "robot_x", "robot_y", "robot_yaw", "worker_x", "worker_y", "distance", "est_distance",
                         "worker_speed", "robot_speed", "state", "n_det", "box_w", "box_h", "cmd_v", "cmd_w", "infer_ms"])
        self.odom = {}
        self.state, self.n_det, self.cmd, self.ms, self.est = "", 0, (0.0, 0.0), float("nan"), float("nan")
        self.box = (float("nan"),) * 2
        self.create_subscription(Odometry, f"/model/{robot}/odometry", lambda m: self.odom.__setitem__("robot", m), 10)
        self.create_subscription(Odometry, f"/model/{target}/odometry", lambda m: self.odom.__setitem__("target", m), 10)
        self.create_subscription(String, "/follower/state", lambda m: setattr(self, "state", m.data), 10)
        self.create_subscription(Float32, "/follower/distance", lambda m: setattr(self, "est", m.data), 10)
        self.create_subscription(Detection2DArray, "/jacket/detections", self.on_det, 10)
        self.create_subscription(Twist, "/cmd_vel", lambda m: setattr(self, "cmd", (m.linear.x, m.angular.z)), 10)
        self.create_subscription(Float32, "/jacket/inference_ms", lambda m: setattr(self, "ms", m.data), 10)
        self.t0 = None
        self.create_timer(0.1, self.tick)
        self.get_logger().info(f"logging to {self.out}")

    def on_det(self, m):
        self.n_det = len(m.detections)
        big = max(m.detections, key=lambda d: d.bbox.size_x, default=None)
        self.box = (big.bbox.size_x, big.bbox.size_y) if big else (float("nan"),) * 2

    @staticmethod
    def unpack(m):
        p, tw = m.pose.pose, m.twist.twist.linear
        return p.position.x, p.position.y, yaw_of(p.orientation), math.hypot(tw.x, tw.y)

    def tick(self):
        if "robot" not in self.odom:
            return
        now = self.get_clock().now().nanoseconds * 1e-9          # sim time
        if self.t0 is None:
            self.t0 = now
        rx, ry, ryaw, rv = self.unpack(self.odom["robot"])
        wx, wy, _, wv = self.unpack(self.odom["target"]) if "target" in self.odom else (float("nan"),) * 4
        dist = math.hypot(wx - rx, wy - ry)
        r = lambda v, n=3: round(v, n)
        self.w.writerow([r(now - self.t0, 2), r(rx), r(ry), r(ryaw), r(wx), r(wy), r(dist), r(self.est),
                         r(wv), r(rv), self.state, self.n_det, r(self.box[0], 1), r(self.box[1], 1), r(self.cmd[0]), r(self.cmd[1]), r(self.ms, 1)])
        self.f.flush()


def main():
    rclpy.init()
    n = Metrics()
    try:
        rclpy.spin(n)
    except KeyboardInterrupt:
        pass
    n.f.close()
    n.destroy_node()
    rclpy.try_shutdown()


if __name__ == "__main__":
    main()
