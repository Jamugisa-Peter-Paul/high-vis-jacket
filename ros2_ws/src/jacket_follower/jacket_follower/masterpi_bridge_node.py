"""ROS 2 <-> real Hiwonder MasterPi bridge (runs on the laptop).

The robot runs Raspbian Buster / Python 3.7 (no ROS 2), so it runs robot/masterpi_server.py and this node
connects it to the SAME topics the Gazebo robot uses:

  robot MJPEG stream  ->  /camera/image_raw (sensor_msgs/Image), /camera/camera_info
  /cmd_vel (Twist)    ->  UDP JSON to the robot (sent at 10 Hz; robot stops if commands stop for 0.5 s)
  robot ultrasonic    ->  /range_front (sensor_msgs/Range)
  latency             ->  /bridge/frame_age_ms (capture -> ROS publish), /bridge/cmd_rtt_ms (command round trip)
"""
import json
import socket
import threading
import time
import urllib.request

import cv2
import numpy as np
import rclpy
from cv_bridge import CvBridge
from geometry_msgs.msg import Twist
from rclpy.node import Node
from sensor_msgs.msg import CameraInfo, Image, Range
from std_msgs.msg import Float32


class MasterPiBridge(Node):
    def __init__(self):
        super().__init__("masterpi_bridge")
        self.declare_parameter("robot_ip", "192.168.149.1")
        self.declare_parameter("http_port", 8081)
        self.declare_parameter("udp_port", 9100)
        self.declare_parameter("enable_motion", False)      # must be set true explicitly to move the wheels
        self.ip = self.get_parameter("robot_ip").value
        self.http_port = int(self.get_parameter("http_port").value)
        self.udp_port = int(self.get_parameter("udp_port").value)
        self.motion = bool(self.get_parameter("enable_motion").value)

        self.bridge = CvBridge()
        self.pub_img = self.create_publisher(Image, "/camera/image_raw", 2)
        self.pub_info = self.create_publisher(CameraInfo, "/camera/camera_info", 2)
        self.pub_rng = self.create_publisher(Range, "/range_front", 10)
        self.pub_age = self.create_publisher(Float32, "/bridge/frame_age_ms", 10)
        self.pub_rtt = self.create_publisher(Float32, "/bridge/cmd_rtt_ms", 10)
        self.create_subscription(Twist, "/cmd_vel", self.on_cmd, 10)

        self.sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.sock.settimeout(0.2)
        self.cmd = (0.0, 0.0)
        self.seq = 0
        self.sent = {}
        self.clock_offset = None
        threading.Thread(target=self.stream_loop, daemon=True).start()
        threading.Thread(target=self.reply_loop, daemon=True).start()
        self.create_timer(0.1, self.send_cmd)
        self.get_logger().info(f"robot {self.ip}  motion {'ENABLED' if self.motion else 'disabled (dry run)'}")

    def on_cmd(self, msg):
        self.cmd = (msg.linear.x, msg.angular.z)

    def send_cmd(self):
        v, w = self.cmd if self.motion else (0.0, 0.0)
        self.seq += 1
        self.sent[self.seq] = time.time()
        self.sock.sendto(json.dumps({"v": v, "w": w, "seq": self.seq}).encode(), (self.ip, self.udp_port))

    def reply_loop(self):
        while rclpy.ok():
            try:
                data, _ = self.sock.recvfrom(1024)
            except (socket.timeout, OSError):
                continue
            m = json.loads(data.decode())
            t_sent = self.sent.pop(m.get("seq"), None)
            if t_sent:
                self.pub_rtt.publish(Float32(data=(time.time() - t_sent) * 1000.0))
                # robot-laptop clock offset estimate (for frame-age measurement), midpoint method
                off = m["t"] - (t_sent + time.time()) / 2
                self.clock_offset = off if self.clock_offset is None else 0.9 * self.clock_offset + 0.1 * off
            r = Range()
            r.header.stamp = self.get_clock().now().to_msg()
            r.header.frame_id = "sonar"
            r.radiation_type = Range.ULTRASOUND
            r.field_of_view, r.min_range, r.max_range = 0.26, 0.03, 4.0
            r.range = float(m["range"]) if m["range"] > 0 else float("inf")
            self.pub_rng.publish(r)

    def stream_loop(self):
        url = f"http://{self.ip}:{self.http_port}/stream"
        while rclpy.ok():
            try:
                s = urllib.request.urlopen(url, timeout=5)
                buf, stamp = b"", None
                while rclpy.ok():
                    line = s.readline()
                    if line.startswith(b"X-Stamp:"):
                        stamp = float(line.split(b":")[1])
                    elif line.startswith(b"Content-Length:"):
                        n = int(line.split(b":")[1])
                        s.readline()
                        jpg = s.read(n)
                        self.publish_frame(jpg, stamp)
            except Exception as e:
                self.get_logger().warn(f"camera stream: {e}; retrying")
                time.sleep(1.0)

    def publish_frame(self, jpg, stamp):
        f = cv2.imdecode(np.frombuffer(jpg, np.uint8), cv2.IMREAD_COLOR)
        if f is None:
            return
        msg = self.bridge.cv2_to_imgmsg(f, encoding="bgr8")
        msg.header.stamp = self.get_clock().now().to_msg()
        msg.header.frame_id = "camera"
        self.pub_img.publish(msg)
        info = CameraInfo()
        info.header = msg.header
        info.width, info.height = f.shape[1], f.shape[0]
        self.pub_info.publish(info)
        if stamp and self.clock_offset is not None:
            self.pub_age.publish(Float32(data=(time.time() - (stamp - self.clock_offset)) * 1000.0))


def main():
    rclpy.init()
    n = MasterPiBridge()
    try:
        rclpy.spin(n)
    except KeyboardInterrupt:
        pass
    n.cmd = (0.0, 0.0)
    n.motion = False
    n.send_cmd()
    n.destroy_node()
    rclpy.try_shutdown()


if __name__ == "__main__":
    main()
