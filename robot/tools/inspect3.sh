cd ~/MasterPi
echo "== battery (from MasterPi log)"; sudo journalctl -u masterpi --no-pager 2>/dev/null | grep -i voltage | tail -3
echo "== setMotor"; sed -n '40,75p' HiwonderSDK/Board.py
echo "== getBattery"; sed -n '165,186p' HiwonderSDK/Board.py
echo "== sonar"; grep -n "def " HiwonderSDK/Sonar.py
echo "== demo"; sed -n '1,60p' MecanumControl/Car_Forward_Demo.py
echo "== internet on robot?"; ping -c 1 -W 2 8.8.8.8 >/dev/null 2>&1 && echo yes || echo no
echo "== network"; ip -4 -o addr | awk '{print $2, $4}'
echo "== camera formats"; v4l2-ctl -d /dev/video0 --list-formats-ext 2>/dev/null | head -30
