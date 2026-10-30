"""Calibration drive for the MasterPi through masterpi_server.py (UDP 9100), no ROS needed.

  py drive_test.py look                       sonar readings + snapshot, wheels stay still
  py drive_test.py drive <v m/s> <seconds>    straight line, then stop
  py drive_test.py turn  <w rad/s> <seconds>  turn in place, then stop

Safety: commands are sent at 10 Hz and the robot stops by itself 0.5 s after they stop; the test
aborts at once if the sonar reads closer than ABORT_M. Before/after sonar + snapshots are saved so the
distance travelled (sonar) and the angle turned (image shift) can be measured.
"""
import json
import socket
import sys
import time
import urllib.request

ROBOT = ("192.168.149.1", 9100)
SNAP = "http://192.168.149.1:8081/snap"
ABORT_M = 0.40
sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
sock.settimeout(0.3)
seq = 0


def send(v, w):
    global seq
    seq += 1
    sock.sendto(json.dumps({"v": v, "w": w, "seq": seq}).encode(), ROBOT)
    try:
        return json.loads(sock.recv(1024).decode())
    except socket.timeout:
        return None


def sonar(n=8):
    rs = []
    for _ in range(n):
        r = send(0, 0)
        if r and r["range"] > 0:
            rs.append(r["range"])
        time.sleep(0.1)
    rs.sort()
    return (rs[len(rs) // 2] if rs else float("nan")), (r or {}).get("battery")


def snap(name):
    with open(name, "wb") as f:
        f.write(urllib.request.urlopen(SNAP, timeout=5).read())


def run(v, w, secs):
    t0, log = time.time(), []
    while time.time() - t0 < secs:
        r = send(v, w)
        if r:
            log.append((round(time.time() - t0, 2), r["range"], r["battery"]))
            if 0 < r["range"] < ABORT_M and v > 0:
                print("ABORT: obstacle at %.2f m" % r["range"])
                break
        time.sleep(0.1)
    for _ in range(5):
        send(0, 0)
        time.sleep(0.05)
    return log


mode = sys.argv[1]
d0, b0 = sonar()
snap(f"{mode}_before.jpg")
print(f"before: sonar {d0:.3f} m   battery {b0} V")
if mode in ("drive", "turn"):
    val, secs = float(sys.argv[2]), float(sys.argv[3])
    log = run(val, 0, secs) if mode == "drive" else run(0, val, secs)
    time.sleep(0.8)
    d1, b1 = sonar()
    snap(f"{mode}_after.jpg")
    print(f"after : sonar {d1:.3f} m   battery {b1} V   (min battery while moving {min((x[2] for x in log), default=None)} V)")
    if mode == "drive":
        print(f"sonar says moved {d0 - d1:.3f} m in {secs} s at command {val} m/s -> expected {val * secs:.3f} m")
