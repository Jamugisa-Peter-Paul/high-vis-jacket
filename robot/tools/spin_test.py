"""Runs ON the robot: spin in place at a fixed wheel power for up to N s, snapshot every 0.25 s.
The laptop finds when the view repeats (one full turn) -> turn rate and camera pixels-per-radian."""
import os, sys, time, urllib.request
sys.path.append('/home/pi/MasterPi/')
import HiwonderSDK.mecanum as mecanum
duty, secs = int(sys.argv[1]), float(sys.argv[2])
ch = mecanum.MecanumChassis()
os.makedirs('/tmp/spin', exist_ok=True)
for f in os.listdir('/tmp/spin'):
    os.remove('/tmp/spin/' + f)
t0 = time.time(); i = 0
ch.set_velocity(0, 90, -duty / 126.0)        # negative angular_rate = turn LEFT
try:
    while time.time() - t0 < secs:
        img = urllib.request.urlopen('http://127.0.0.1:8081/snap', timeout=3).read()
        open('/tmp/spin/%03d_%.3f.jpg' % (i, time.time() - t0), 'wb').write(img); i += 1
        time.sleep(0.2)
finally:
    ch.set_velocity(0, 90, 0)
print(i, 'frames')
