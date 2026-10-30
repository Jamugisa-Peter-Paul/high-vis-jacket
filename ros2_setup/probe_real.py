"""Measure the real-robot pipeline for N seconds: topic rates, latency, inference time, follower states.
   python3 probe_real.py 30"""
import math
import sys
import time
from collections import Counter, defaultdict

import rclpy
from rclpy.node import Node
from rclpy.qos import qos_profile_sensor_data
from sensor_msgs.msg import Image, Range
from std_msgs.msg import Float32, String
from vision_msgs.msg import Detection2DArray

DUR = float(sys.argv[1]) if len(sys.argv) > 1 else 30
rclpy.init()
n = Node("probe_real")
t_msgs = defaultdict(list)
vals = defaultdict(list)
states = Counter()
scores = []


def stamp(name):
    t_msgs[name].append(time.time())


n.create_subscription(Image, "/camera/image_raw", lambda m: stamp("camera"), qos_profile_sensor_data)
n.create_subscription(Detection2DArray, "/jacket/detections",
                      lambda m: (stamp("detections"), scores.extend(d.results[0].hypothesis.score for d in m.detections if d.results)), 10)
for topic, key in (("/bridge/frame_age_ms", "frame_age_ms"), ("/bridge/cmd_rtt_ms", "cmd_rtt_ms"),
                   ("/jacket/inference_ms", "inference_ms"), ("/follower/distance", "est_distance_m")):
    n.create_subscription(Float32, topic, lambda m, k=key: vals[k].append(m.data), 10)
n.create_subscription(Range, "/range_front", lambda m: vals["sonar_m"].append(m.range), 10)
n.create_subscription(String, "/follower/state", lambda m: states.update([m.data]), 10)

end = time.time() + DUR
while time.time() < end:
    rclpy.spin_once(n, timeout_sec=0.1)

for k, ts in t_msgs.items():
    gaps = [b - a for a, b in zip(ts, ts[1:])]
    print(f"{k:12s} {len(ts) / DUR:5.1f} Hz   longest gap {max(gaps, default=float('nan')):.2f} s")
for k, v in vals.items():
    v = [x for x in v if not math.isnan(x) and not math.isinf(x)]
    if v:
        v.sort()
        print(f"{k:16s} median {v[len(v) // 2]:7.2f}   min {v[0]:7.2f}   max {v[-1]:7.2f}   (n={len(v)})")
print("follower states:", dict(states))
print("detections:", len(scores), "scores median %.2f" % sorted(scores)[len(scores) // 2] if scores else "")
n.destroy_node()
rclpy.shutdown()
