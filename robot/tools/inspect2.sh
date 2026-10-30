cd ~/MasterPi
echo "== SDK files"; ls HiwonderSDK MecanumControl Functions
echo "== mecanum"; f=$(ls HiwonderSDK/mecanum.py MecanumControl/*.py 2>/dev/null | head -1); echo "$f"; sed -n '1,200p' HiwonderSDK/mecanum.py 2>/dev/null | head -120
echo "== Camera.py head"; sed -n '1,60p' Camera.py
echo "== MasterPi.py head"; sed -n '1,80p' MasterPi.py
echo "== Board motor funcs"; grep -n "def setMotor\|def setPWMServo\|def setBusServo\|def getBattery\|def setBuzzer" HiwonderSDK/Board.py
echo "== how MasterPi is started"; systemctl list-unit-files --no-pager | grep -i -E "masterpi|hiwonder|mjpg"; ls /etc/systemd/system | grep -i -E "master|hiwonder|mjpg"
echo "== ultrasonic/sonar"; ls HiwonderSDK | grep -i -E "sonar|ultra"
echo "== piwheels / pip config"; cat /etc/pip.conf 2>/dev/null
