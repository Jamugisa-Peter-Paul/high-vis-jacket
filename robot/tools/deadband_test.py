"""Runs ON the robot: short in-place turns at increasing motor power, snapshot before/after each.
Finds the motor dead zone (power below which the wheels do not turn the robot)."""
import sys, time, urllib.request
sys.path.append('/home/pi/MasterPi/')
import HiwonderSDK.mecanum as mecanum
ch = mecanum.MecanumChassis()
def snap(name):
    open('/tmp/cal/%s.jpg' % name, 'wb').write(urllib.request.urlopen('http://127.0.0.1:8081/snap', timeout=3).read())
import os; os.makedirs('/tmp/cal', exist_ok=True)
for duty in [int(x) for x in sys.argv[1:]]:
    rate = duty / 126.0                      # angular_rate -> wheel duty = rate * (a+b)
    snap('d%d_a' % duty)
    ch.set_velocity(0, 90, rate); time.sleep(0.8); ch.set_velocity(0, 90, 0)
    time.sleep(0.6); snap('d%d_b' % duty)
    print('duty', duty, 'done', flush=True)
ch.set_velocity(0, 90, 0)
