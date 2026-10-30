#!/usr/bin/env python3
"""Runs ON the Hiwonder MasterPi (Raspbian Buster, Python 3.7, no ROS 2).

- Camera  : MJPEG stream on http://<robot>:8081/stream (and /snap for one frame)
- Commands: UDP port 9100, JSON {"v": m/s, "w": rad/s, "seq": n}  -> mecanum chassis
- Sensor  : UDP replies {"range": metres, "battery": V, "seq": n} to the sender (ultrasonic + battery)
- Safety  : WATCHDOG - if no command arrives for 0.5 s the wheels are stopped.
            Speeds are clamped. Ctrl+C / SIGTERM always stops the motors.

Start:  sudo python3 masterpi_server.py        (sudo: the Hiwonder SDK needs I2C/GPIO access)
"""
import json
import math
import signal
import socket
import sys
import threading
import time
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

sys.path.append('/home/pi/MasterPi/')
import cv2
import HiwonderSDK.Board as Board
import HiwonderSDK.mecanum as mecanum
import HiwonderSDK.Sonar as Sonar

CAM_INDEX, W, H = 0, 320, 240          # 320x240 MJPG: fast enough in dim rooms (640x480 fell to 1.5 fps)
HTTP_PORT, UDP_PORT = 8081, 9100
WATCHDOG_S = 0.5
MAX_V, MAX_W = 0.35, 1.2            # m/s, rad/s
# The SDK's mecanum "velocity" goes straight to the motor board as PWM duty (-100..100 %). Wheel speeds
# are computed here with the SDK's mecanum formulas, in m/s, and converted to duty:
#   wheel duty = (START_DUTY + DUTY_PER_MPS * wheel speed) * NOMINAL_V / battery V
# Affine because the gear motors need a minimum push to overcome friction; scaled by battery voltage
# because the same duty gives far more speed on a full pack. Measured 2026-10-17 (duty x volts):
#   28 % @ 6.4 V creeps on tiles (~180), 32 % @ 6.5 V turns on carpet (~210), 36 % @ 6.4 V and
#   31 % @ 8.0 V spin fast with blurred camera frames (~230-250)  ->  start at ~207 duty-volts.
# Wheel speeds below MIN_SPEED are treated as zero. MAX_DUTY is a hard ceiling whatever the laptop sends.
NOMINAL_V = 7.4
START_DUTY = 28.0                  # at 7.4 V (= 207 duty-volts)
DUTY_PER_MPS = 30.0                # at 7.4 V
MIN_SPEED = 0.02                   # m/s
MAX_DUTY = 60.0
battery_v = NOMINAL_V              # low-pass filtered battery voltage, updated by cmd_loop
AB_M = (67 + 59) / 1000.0          # half wheelbase + half track (m), as in HiwonderSDK.mecanum

chassis = mecanum.MecanumChassis()
sonar = Sonar.Sonar()
lock = threading.Lock()
latest_jpg = None
last_cmd_t = 0.0
running = True


def stop_motors(*_):
    chassis.set_velocity(0, 90, 0)


def drive(v, w):
    """v forward m/s, w rad/s (positive = turn left) -> four wheel duties (SDK mecanum formulas)."""
    # SDK: vp = -angular_rate*(a+b), and a positive angular_rate turns RIGHT (measured), so for a left
    # turn (w > 0) angular_rate = -w  ->  vp = +w*(a+b)
    vy, vp = v, w * AB_M
    wheels = (vy - vp, vy + vp, vy - vp, vy + vp)  # motor 1..4 (vx = 0: no sideways motion)
    duties = []
    k = NOMINAL_V / max(5.5, battery_v)          # volt compensation (floor avoids silly values on bad reads)
    for s in wheels:
        d = 0.0 if abs(s) < MIN_SPEED else math.copysign(min(MAX_DUTY, k * (START_DUTY + DUTY_PER_MPS * abs(s))), s)
        duties.append(int(d))
    for i, d in enumerate(duties, 1):
        Board.setMotor(i, d)
    return duties


def shutdown(*_):
    global running
    running = False
    stop_motors()
    sys.exit(0)


signal.signal(signal.SIGINT, shutdown)
signal.signal(signal.SIGTERM, shutdown)


def camera_loop():
    global latest_jpg
    cap = cv2.VideoCapture(CAM_INDEX)
    cap.set(cv2.CAP_PROP_FOURCC, cv2.VideoWriter_fourcc(*'MJPG'))
    cap.set(cv2.CAP_PROP_FPS, 30)
    cap.set(cv2.CAP_PROP_FRAME_WIDTH, W)
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, H)
    while running:
        ok, f = cap.read()
        if not ok:
            time.sleep(0.05)
            continue
        ok, jpg = cv2.imencode('.jpg', f, [cv2.IMWRITE_JPEG_QUALITY, 80])
        if ok:
            with lock:
                latest_jpg = (time.time(), jpg.tobytes())


class Handler(BaseHTTPRequestHandler):
    def log_message(self, *a):
        pass

    def do_GET(self):
        if self.path.startswith('/snap'):
            with lock:
                d = latest_jpg
            self.send_response(200)
            self.send_header('Content-Type', 'image/jpeg')
            self.end_headers()
            self.wfile.write(d[1] if d else b'')
            return
        self.send_response(200)
        self.send_header('Content-Type', 'multipart/x-mixed-replace; boundary=frame')
        self.end_headers()
        last = 0
        try:
            while running:
                with lock:
                    d = latest_jpg
                if d and d[0] != last:
                    last = d[0]
                    # capture timestamp in a header so the laptop can measure network latency
                    self.wfile.write(b"--frame\r\nContent-Type: image/jpeg\r\nX-Stamp: %.4f\r\nContent-Length: %d\r\n\r\n" % (d[0], len(d[1])))
                    self.wfile.write(d[1] + b"\r\n")
                time.sleep(0.01)
        except (BrokenPipeError, ConnectionResetError):
            pass


def cmd_loop():
    global last_cmd_t, battery_v
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    s.bind(('0.0.0.0', UDP_PORT))
    s.settimeout(0.1)
    while running:
        try:
            data, addr = s.recvfrom(1024)
        except socket.timeout:
            continue
        try:
            m = json.loads(data.decode())
            v = max(-MAX_V, min(MAX_V, float(m.get('v', 0))))
            w = max(-MAX_W, min(MAX_W, float(m.get('w', 0))))
        except (ValueError, TypeError):
            continue
        last_cmd_t = time.time()
        try:
            vb = Board.getBattery() / 1000.0
            if 5.0 < vb < 9.0:
                battery_v = 0.8 * battery_v + 0.2 * vb     # filter out sag spikes while motors start
        except Exception:
            vb = -1.0
        duties = drive(v, w)
        try:
            rng = sonar.getDistance() / 1000.0        # mm -> m
        except Exception:
            rng = -1.0
        reply = {'range': rng, 'battery': vb, 'battery_filt': round(battery_v, 3), 'seq': m.get('seq', 0),
                 't': time.time(), 'duty': duties}
        s.sendto(json.dumps(reply).encode(), addr)


def watchdog_loop():
    stopped = True
    while running:
        if time.time() - last_cmd_t > WATCHDOG_S:
            if not stopped:
                stop_motors()
                stopped = True
        else:
            stopped = False
        time.sleep(0.05)


if __name__ == '__main__':
    stop_motors()
    for fn in (camera_loop, cmd_loop, watchdog_loop):
        threading.Thread(target=fn, daemon=True).start()
    print('MasterPi server: camera http://0.0.0.0:%d/stream  commands udp %d  watchdog %.1fs' % (HTTP_PORT, UDP_PORT, WATCHDOG_S))
    ThreadingHTTPServer(('0.0.0.0', HTTP_PORT), Handler).serve_forever()
