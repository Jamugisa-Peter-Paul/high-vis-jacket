echo "== usb"; lsusb | grep -v "root hub"
echo "== v4l2 devices"; v4l2-ctl --list-devices 2>/dev/null
for d in /dev/video0 /dev/video1 /dev/video2 /dev/video3; do
  [ -e $d ] || continue
  f=$(v4l2-ctl -d $d --list-formats 2>/dev/null | grep -o "'[A-Z0-9]*'" | tr '\n' ' ')
  echo "$d formats: $f"
done
