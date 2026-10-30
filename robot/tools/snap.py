"""Grab one JPEG frame from the robot's MJPEG stream on port 8080."""
import socket
import sys

out = sys.argv[1]
s = socket.create_connection(("192.168.149.1", 8080), timeout=5)
s.sendall(b"GET /?action=stream HTTP/1.0\r\nHost: 192.168.149.1\r\n\r\n")
buf = b""
while len(buf) < 3_000_000:
    chunk = s.recv(65536)
    if not chunk:
        break
    buf += chunk
    a = buf.find(b"\xff\xd8")
    b = buf.find(b"\xff\xd9", a + 2) if a >= 0 else -1
    if a >= 0 and b > a:
        open(out, "wb").write(buf[a:b + 2])
        print("saved", out, b + 2 - a, "bytes")
        break
else:
    print("no frame; header:", buf[:300])
s.close()
