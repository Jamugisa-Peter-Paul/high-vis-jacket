"""Live MJPEG camera feed (http://192.168.149.1:8081) with optional recording.
Recording: write a session name into /tmp/record_session  -> saves ~2 frames/s to /home/pi/dataset/<name>/
           delete /tmp/record_session                       -> stops recording.
Camera only: never touches motors or servos. Python 3.7 compatible."""
import os
import sys
import threading
import time
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

import cv2
import numpy as np

PORT = 8081
CAMS = tuple(int(a) for a in (sys.argv[1:] or ['0']))
REC_FLAG = '/tmp/record_session'
REC_ROOT = '/home/pi/dataset'
REC_PERIOD = 0.5
lock = threading.Lock()
frames = {i: None for i in CAMS}
scores = {i: 0.0 for i in CAMS}
latest = None
rec_state = {'name': None, 'count': 0, 'last': 0.0}


def grab(idx):
    cap = cv2.VideoCapture(idx)
    cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
    while True:
        ok, f = cap.read()
        if not ok:
            time.sleep(0.1)
            continue
        s = cv2.Laplacian(cv2.cvtColor(f, cv2.COLOR_BGR2GRAY), cv2.CV_64F).var()
        with lock:
            frames[idx], scores[idx] = f, s
        if idx == CAMS[0]:
            record(f)


def record(f):
    name = None
    if os.path.exists(REC_FLAG):
        try:
            name = open(REC_FLAG).read().strip() or None
        except OSError:
            name = None
    if name != rec_state['name']:
        rec_state.update(name=name, count=0, last=0.0)
        if name:
            os.makedirs(os.path.join(REC_ROOT, name), exist_ok=True)
    if name and time.time() - rec_state['last'] >= REC_PERIOD:
        rec_state['last'] = time.time()
        rec_state['count'] += 1
        path = os.path.join(REC_ROOT, name, '%s_%05d.jpg' % (name, rec_state['count']))
        cv2.imwrite(path, f, [cv2.IMWRITE_JPEG_QUALITY, 92])


def compose():
    global latest
    while True:
        tiles = []
        with lock:
            items = [(i, frames[i], scores[i]) for i in CAMS]
        for i, f, s in items:
            t = np.zeros((480, 640, 3), np.uint8) if f is None else f.copy()
            cv2.rectangle(t, (0, 0), (640, 40), (0, 0, 0), -1)
            col = (0, 255, 0) if s > 100 else (0, 255, 255)
            cv2.putText(t, "video%d  sharp %4.0f" % (i, s), (10, 28), cv2.FONT_HERSHEY_SIMPLEX, 0.75, col, 2)
            if rec_state['name'] and i == CAMS[0]:
                cv2.circle(t, (420, 20), 9, (0, 0, 255), -1)
                cv2.putText(t, "REC %s %d" % (rec_state['name'], rec_state['count']), (435, 28),
                            cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 0, 255), 2)
            tiles.append(t)
        ok, jpg = cv2.imencode('.jpg', np.hstack(tiles), [cv2.IMWRITE_JPEG_QUALITY, 70])
        if ok:
            with lock:
                latest = jpg.tobytes()
        with open('/tmp/sharpness.txt', 'w') as fh:
            fh.write(" ".join("video%d=%.0f" % (i, s) for i, _, s in items) + "\n")
        time.sleep(0.08)


class Handler(BaseHTTPRequestHandler):
    def log_message(self, *args):
        pass

    def do_GET(self):
        if self.path.startswith('/snap'):
            with lock:
                data = latest
            self.send_response(200)
            self.send_header('Content-Type', 'image/jpeg')
            self.end_headers()
            self.wfile.write(data or b'')
            return
        if self.path != '/stream':
            page = (b"<html><body style='margin:0;background:#111;color:#eee;font-family:sans-serif'>"
                    b"<p style='padding:8px'>MasterPi live camera (red REC = recording training data)</p>"
                    b"<img src='/stream' style='width:100%;max-width:960px'></body></html>")
            self.send_response(200)
            self.send_header('Content-Type', 'text/html')
            self.end_headers()
            self.wfile.write(page)
            return
        self.send_response(200)
        self.send_header('Content-Type', 'multipart/x-mixed-replace; boundary=frame')
        self.end_headers()
        try:
            while True:
                with lock:
                    data = latest
                if data:
                    self.wfile.write(b"--frame\r\nContent-Type: image/jpeg\r\nContent-Length: %d\r\n\r\n" % len(data))
                    self.wfile.write(data + b"\r\n")
                time.sleep(0.08)
        except (BrokenPipeError, ConnectionResetError):
            pass


for c in CAMS:
    threading.Thread(target=grab, args=(c,), daemon=True).start()
threading.Thread(target=compose, daemon=True).start()
ThreadingHTTPServer(('0.0.0.0', PORT), Handler).serve_forever()
