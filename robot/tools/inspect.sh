echo "== model"; tr -d '\0' < /proc/device-tree/model; echo
echo "== os"; grep PRETTY /etc/os-release; uname -m -r
echo "== python"; python3 --version; python3 -c "import struct;print(struct.calcsize('P')*8,'bit')"
echo "== pip pkgs"; python3 -m pip list 2>/dev/null | grep -iE "^(numpy|opencv|torch|onnx|ncnn|ultralytics|tflite|mediapipe|pyyaml)"
echo "== cpu/mem/disk"; nproc; free -m | head -2; df -h / | tail -1; vcgencmd measure_temp; vcgencmd get_throttled
echo "== camera"; ls /dev/video*; lsusb
echo "== home"; ls ~
echo "== hiwonder"; ls ~/MasterPi | head -40
echo "== running"; ps aux --sort=-%cpu | head -8 | cut -c1-160
