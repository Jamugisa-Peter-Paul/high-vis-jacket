"""Copy files to/from the robot: python rcp.py put <local> <remote> | get <remote> <local>"""
import os
import sys

import paramiko

c = paramiko.SSHClient()
c.set_missing_host_key_policy(paramiko.AutoAddPolicy())
c.connect(os.environ.get("ROBOT_HOST", "192.168.149.1"), username=os.environ.get("ROBOT_USER", "pi"),
          password=os.environ.get("ROBOT_PASS", "raspberry"), timeout=8, look_for_keys=False, allow_agent=False)
sftp = c.open_sftp()
op, a, b = sys.argv[1:4]
(sftp.put if op == "put" else sftp.get)(a, b)
print(op, a, "->", b)
sftp.close()
c.close()
