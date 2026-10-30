"""Follower: turns jacket detections into safe velocity commands.

Subscribes : /jacket/detections  (vision_msgs/Detection2DArray)
             /camera/camera_info (sensor_msgs/CameraInfo)          focal length + image size
             /range_front        (sensor_msgs/Range, real sonar)    or /range_front_scan (sim sonar)
Publishes  : /cmd_vel            (geometry_msgs/Twist)
             /follower/state     (std_msgs/String)   SEARCH | CONFIRMING | FOLLOW | HOLD | TOO_CLOSE | E_STOP
             /follower/distance  (std_msgs/Float32)  estimated distance to the jacket (m), NaN if none

Distance estimate (pinhole camera): d = min(f_x * jacket_width_m / box_w, f_x * jacket_height_m / box_h).
Each failure mode only ever makes one estimate too LARGE: up close the low camera crops the top of the
vest (box height too small), and a person turned sideways shows a narrower vest (box width too small).
Taking the smaller of the two keeps the estimate right in both cases (and errs on the safe side).
Sonar fusion: when the target is near the image centre (|x_err| < sonar_cone) the front ultrasonic sensor
points at it, so a fresh sonar range is used as a third estimate (minimum again). This covers a person
walking across close by, where the vest is both side-on AND cropped and both visual cues read too far.

Control (FOLLOW):  v = k_dist * (d - target_dist) + k_rate * d_dot
                   w = -k_turn * x_err            (x_err = horizontal offset in -1..1)
  The d_dot term (filtered rate of change of distance) reacts to the person speeding up or slowing
  down before the gap changes much -> speed matching.

Safety / uncertainty handling
  CONFIRMING : jacket must be seen in >= confirm_frames consecutive frames before any motion.
  Hysteresis : a NEW target needs score >= acquire_conf (0.70) in confirm_frames consecutive frames; the
               target being followed is kept down to min_conf (0.40), but only near its last bearing
               (|x_err - last| < gate). Hi-vis-coloured clothing (e.g. an orange shirt) scores ~0.55 with
               occasional single frames above 0.70: it is drawn, but never confirmed.
               While confirming a candidate during a search the robot keeps turning (half speed), so a
               flickering false positive cannot freeze the search.
  HOLD       : lost < lost_timeout s -> brake to 0, keep turning gently towards the last bearing.
  SEARCH     : lost > search_after s  -> rotate slowly in place towards the side it was last seen.
               search_pause > 0 makes it stop-and-look (turn search_turn s, stand still search_pause s):
               on the real robot a continuous turn blurs the camera frames and the detector misses the vest.
  TOO_CLOSE  : d < stop_dist -> no forward motion (still turns to keep it centred).
  E_STOP     : no detector message for > watchdog s, or sonar < min_range -> zero velocity.
"""
import math

import rclpy
from geometry_msgs.msg import Twist
from rclpy.node import Node
from rclpy.qos import qos_profile_sensor_data
from sensor_msgs.msg import CameraInfo, LaserScan, Range
from std_msgs.msg import Float32, String
from vision_msgs.msg import Detection2DArray


class Follower(Node):
    def __init__(self):
        super().__init__("jacket_follower")
        P = {
            "image_width": 640, "image_height": 480,
            "hfov_rad": 1.55,              # used only if camera_info has no focal length (real robot)
            "jacket_width_m": 0.45,        # typical torso/vest width seen from behind
            "jacket_height_m": 0.57,       # visible vest height (box h/w ~ 1.27 from behind)
            "target_dist": 1.5, "stop_dist": 0.8,
            "k_dist": 0.8, "k_rate": 0.6, "k_turn": 1.6,
            "max_lin": 0.35, "max_ang": 1.2, "max_lin_acc": 0.6,
            "confirm_frames": 3, "min_conf": 0.40, "acquire_conf": 0.70, "gate": 0.5,
            "lost_timeout": 1.5, "search_after": 3.0, "search_ang": 0.5, "search_turn": 0.4, "search_pause": 0.0,
            "watchdog": 1.0, "min_range": 0.25, "rate_hz": 20.0,
            "enable_search": True, "sonar_cone": 0.2,
        }
        for k, v in P.items():
            self.declare_parameter(k, v)
        self.p = {k: self.get_parameter(k).value for k in P}
        self.fx = (self.p["image_width"] / 2) / math.tan(self.p["hfov_rad"] / 2)

        self.pub = self.create_publisher(Twist, "/cmd_vel", 10)
        self.pub_state = self.create_publisher(String, "/follower/state", 10)
        self.pub_dist = self.create_publisher(Float32, "/follower/distance", 10)
        self.create_subscription(Detection2DArray, "/jacket/detections", self.on_det, 10)
        self.create_subscription(CameraInfo, "/camera/camera_info", self.on_info, qos_profile_sensor_data)
        self.create_subscription(Range, "/range_front", self.on_range, 10)
        self.create_subscription(LaserScan, "/range_front_scan", self.on_scan, qos_profile_sensor_data)

        self.state = "SEARCH"
        self.seen_streak = 0
        self.last_det_msg = 0.0
        self.last_seen = 0.0               # last time the CONFIRMED target was seen
        self.last_det_t = 0.0              # last time any accepted detection arrived (for filtering)
        self.last_x_err = 0.0
        self.target = None                 # (x_err, distance)
        self.dist_f, self.rate_f, self.prev = None, 0.0, None
        self.range, self.range_t = math.inf, -1.0
        self.v_cmd = 0.0
        self.create_timer(1.0 / self.p["rate_hz"], self.control)
        self.get_logger().info(f"follower ready: target {self.p['target_dist']} m, stop {self.p['stop_dist']} m")

    # ---------------------------------------------------------------- inputs
    def on_info(self, msg):
        if msg.width and msg.height:
            self.p["image_width"], self.p["image_height"] = msg.width, msg.height
            if msg.k[0] > 0:
                self.fx = msg.k[0]
            else:                                  # no calibration sent: focal length from hfov and actual width
                self.fx = (msg.width / 2) / math.tan(self.p["hfov_rad"] / 2)

    def on_range(self, msg):
        self.range = msg.range if msg.min_range < msg.range < msg.max_range else math.inf
        self.range_t = self.now()

    def on_scan(self, msg):
        valid = [r for r in msg.ranges if msg.range_min < r < msg.range_max]
        self.range = min(valid) if valid else math.inf
        self.range_t = self.now()

    def now(self):
        return self.get_clock().now().nanoseconds * 1e-9      # sim time in Gazebo, wall time on the robot

    def on_det(self, msg):
        now = self.now()
        self.last_det_msg = now
        W = self.p["image_width"]
        tracking = self.state in ("FOLLOW", "TOO_CLOSE", "HOLD")

        def x_err(d):
            return (d.bbox.center.position.x - W / 2) / (W / 2)

        def accept(d):
            if not d.results:
                return False
            score = d.results[0].hypothesis.score
            if tracking and abs(x_err(d) - self.last_x_err) < self.p["gate"]:
                return score >= self.p["min_conf"]          # same target, near where it was
            return score >= self.p["acquire_conf"]          # anything else must be convincing

        good = [d for d in msg.detections if accept(d)]
        if not good:
            self.seen_streak = 0
            self.target = None
            return

        # identity: while following, keep the jacket nearest the last bearing; otherwise take the largest (closest)
        if tracking:
            d = min(good, key=lambda d: abs(x_err(d) - self.last_x_err))
        else:
            d = max(good, key=lambda d: d.bbox.size_x)
        dist = min(self.fx * self.p["jacket_width_m"] / max(d.bbox.size_x, 1.0),
                   self.fx * self.p["jacket_height_m"] / max(d.bbox.size_y, 1.0))
        # low-pass the distance and its rate (detections are noisy)
        if self.dist_f is None or now - self.last_det_t > 0.5:
            self.dist_f, self.rate_f = dist, 0.0
        else:
            dt = max(now - self.last_det_t, 1e-3)
            new_f = 0.6 * self.dist_f + 0.4 * dist
            self.rate_f = 0.7 * self.rate_f + 0.3 * (new_f - self.dist_f) / dt
            self.dist_f = new_f
        self.target = (x_err(d), self.dist_f)
        self.last_det_t = now
        self.seen_streak += 1
        if self.seen_streak >= self.p["confirm_frames"]:
            self.last_x_err = x_err(d)
            self.last_seen = now

    # ---------------------------------------------------------------- control loop
    def control(self):
        p, now = self.p, self.now()
        v = w = 0.0
        dist_out = float("nan")
        if now - self.last_det_msg > p["watchdog"]:
            state = "E_STOP"                       # detector or camera silent: fail safe
        elif self.range < p["min_range"]:
            state = "E_STOP"                       # obstacle right in front (sonar)
        elif self.target and self.seen_streak >= p["confirm_frames"]:
            x_err, dist = self.target
            if abs(x_err) < p["sonar_cone"] and now - self.range_t < 0.5:
                dist = min(dist, self.range)       # sonar points at the target: use it too
            dist_out = dist
            w = -p["k_turn"] * x_err
            if dist < p["stop_dist"]:
                state = "TOO_CLOSE"
            else:
                state = "FOLLOW"
                v = p["k_dist"] * (dist - p["target_dist"]) + p["k_rate"] * self.rate_f
                v = max(0.0, v)                    # never reverse into space we cannot see
        elif self.target:
            state = "CONFIRMING"                   # candidate: no forward motion until confirmed
            if p["enable_search"] and now - self.last_seen > p["search_after"] and p["search_pause"] <= 0:
                w = 0.5 * p["search_ang"] * (-1.0 if self.last_x_err > 0 else 1.0)   # keep searching, slower
            # (stop-and-look search: stand still while a candidate is being confirmed)
        elif now - self.last_seen < p["lost_timeout"]:
            state = "HOLD"
            w = -0.5 * p["k_turn"] * self.last_x_err
        elif p["enable_search"] and now - self.last_seen > p["search_after"]:
            state = "SEARCH"
            w = p["search_ang"] * (-1.0 if self.last_x_err > 0 else 1.0)
            if p["search_pause"] > 0:          # stop-and-look: turn, then hold still for sharp frames
                period = p["search_turn"] + p["search_pause"]
                if (now - self.last_seen - p["search_after"]) % period > p["search_turn"]:
                    w = 0.0
        else:
            state = "HOLD"

        v = min(v, p["max_lin"])
        w = max(-p["max_ang"], min(p["max_ang"], w))
        dv = p["max_lin_acc"] / p["rate_hz"]
        self.v_cmd += max(-2 * dv, min(dv, v - self.v_cmd))       # brake twice as fast as accelerate
        if state == "E_STOP":
            self.v_cmd, w = 0.0, 0.0

        t = Twist()
        t.linear.x, t.angular.z = float(self.v_cmd), float(w)
        self.pub.publish(t)
        if state != self.state:
            self.get_logger().info(f"{self.state} -> {state}")
            self.state = state
        self.pub_state.publish(String(data=state))
        self.pub_dist.publish(Float32(data=dist_out))

    def stop(self):
        try:
            self.pub.publish(Twist())
        except Exception:          # Ctrl+C already shut ROS down: nothing left to tell
            pass


def main():
    rclpy.init()
    node = Follower()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    node.stop()
    node.destroy_node()
    rclpy.try_shutdown()


if __name__ == "__main__":
    main()
