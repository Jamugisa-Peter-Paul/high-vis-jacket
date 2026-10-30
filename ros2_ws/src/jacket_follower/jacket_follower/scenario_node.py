"""Scenario driver (simulation only): moves the people in Gazebo along timed scripts by publishing
velocity commands to their VelocityControl plugins (/model/<name>/cmd_vel, bridged to Gazebo).

A script is a list of segments (duration_s, forward_speed_m_s, turn_rate_rad_s).
  s1_normal    : steady walk, two 90-degree turns                              -> normal following
  s2_speed     : slow -> medium -> faster than the robot can go -> stop -> slow -> speed matching + limits
  s3_challenge : orange-shirt distractor in view; a white-shirt person crosses and stands between
                 robot and worker (occlusion, 20 s) while the worker sprints off right -> HOLD / SEARCH
"""
import math

import rclpy
from geometry_msgs.msg import Twist
from rclpy.node import Node
from std_msgs.msg import String

TURN = 1.0                       # rad/s used for 90-degree turns
Q = math.pi / 2 / TURN           # seconds for a 90-degree turn

SCRIPTS = {
    "s1_normal": {
        "worker": [(4, 0, 0), (14, 0.30, 0), (Q, 0, TURN), (6, 0.30, 0), (Q, 0, TURN), (10, 0.30, 0), (30, 0, 0)],
    },
    "s2_speed": {
        "worker": [(4, 0, 0), (8, 0.15, 0), (8, 0.35, 0), (5, 0.60, 0), (6, 0, 0), (Q, 0, TURN), (8, 0.20, 0), (30, 0, 0)],
    },
    "s3_challenge": {
        # worker stops at x=5 (t=14), turns right (t=16) and sprints 3.2 m to the right (t=17.6-21.6)
        "worker": [(4, 0, 0), (10, 0.30, 0), (2, 0, 0), (Q, 0, -TURN), (4, 0.80, 0), (60, 0, 0)],
        # crosses y=0 at x=4.2 (between robot and worker) at t~16.5, i.e. while the worker turns, stops at
        # (4.2,-1.8) right in the robot's line of sight to the worker, stands there 20 s, then walks away (+x)
        "person_plain": [(11.5, 0, 0), (8, 0.60, 0), (20, 0, 0), (Q, 0, TURN), (6, 0.60, 0), (60, 0, 0)],
        # background distractor: (8.5,-3.5) -> (8.5,2.0), stays in view on the left
        "person_orange": [(2, 0, 0), (11, 0.50, 0), (60, 0, 0)],
    },
}


class Scenario(Node):
    def __init__(self):
        super().__init__("scenario")
        self.declare_parameter("scenario", "s1_normal")
        self.declare_parameter("start_delay", 3.0)     # let the detector/follower start first
        name = self.get_parameter("scenario").value
        self.script = SCRIPTS[name]
        self.pubs = {m: self.create_publisher(Twist, f"/model/{m}/cmd_vel", 10) for m in self.script}
        self.pub_phase = self.create_publisher(String, "/scenario/phase", 10)
        self.t0 = None
        self.delay = float(self.get_parameter("start_delay").value)
        self.create_timer(0.05, self.tick)
        self.get_logger().info(f"scenario {name}: {list(self.script)}")

    def now(self):
        return self.get_clock().now().nanoseconds * 1e-9

    def tick(self):
        if self.t0 is None:
            if self.now() > 0:
                self.t0 = self.now() + self.delay
            return
        t = self.now() - self.t0
        phase = []
        for model, segs in self.script.items():
            v = w = 0.0
            acc, idx = 0.0, None
            for i, (d, sv, sw) in enumerate(segs):
                if t >= 0 and acc <= t < acc + d:
                    v, w, idx = sv, sw, i
                    break
                acc += d
            msg = Twist()
            msg.linear.x, msg.angular.z = float(v), float(w)
            self.pubs[model].publish(msg)
            phase.append(f"{model}:{idx if idx is not None else '-'}:{v:.2f}")
        self.pub_phase.publish(String(data=" ".join(phase)))


def main():
    rclpy.init()
    n = Scenario()
    try:
        rclpy.spin(n)
    except KeyboardInterrupt:
        pass
    n.destroy_node()
    rclpy.try_shutdown()


if __name__ == "__main__":
    main()
