"""Run a command on the robot over SSH: python rsh.py "<command>" (credentials from env ROBOT_USER / ROBOT_PASS)."""
import os
import sys

import paramiko

HOST = os.environ.get("ROBOT_HOST", "192.168.149.1")
USER = os.environ.get("ROBOT_USER", "pi")
PASS = os.environ.get("ROBOT_PASS", "raspberrypi")

c = paramiko.SSHClient()
c.set_missing_host_key_policy(paramiko.AutoAddPolicy())
c.connect(HOST, username=USER, password=PASS, timeout=8, banner_timeout=8, auth_timeout=8, look_for_keys=False, allow_agent=False)
cmd = sys.argv[1]
if cmd.startswith("@"):
    cmd = open(cmd[1:], encoding="utf-8").read().replace("\r", "")
_, out, err = c.exec_command(cmd, timeout=int(os.environ.get("ROBOT_TIMEOUT", "60")))
sys.stdout.write(out.read().decode(errors="replace"))
e = err.read().decode(errors="replace")
if e.strip():
    sys.stdout.write("[stderr] " + e)
c.close()
