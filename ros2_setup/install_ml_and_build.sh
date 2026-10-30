#!/bin/bash
# Python ML environment for the detector node + build the ROS 2 workspace. Run as root inside WSL.
set -e
source /opt/ros/jazzy/setup.bash
PROJ=/mnt/d/mscs/intelligent_systems_and_robotics/jacket_follower

# venv that can still see ROS's system packages (rclpy, cv_bridge)
if [ ! -d /root/venv ]; then python3 -m venv --system-site-packages /root/venv; fi
source /root/venv/bin/activate
pip install --upgrade pip -q
pip install -q torch torchvision --index-url https://download.pytorch.org/whl/cu128
pip install -q ultralytics "numpy<2" "opencv-python-headless<4.11"
python -c "import torch, ultralytics, numpy, cv2; print('torch', torch.__version__, 'cuda', torch.cuda.is_available(), '| ultralytics', ultralytics.__version__, '| numpy', numpy.__version__, '| cv2', cv2.__version__)"
python -c "from cv_bridge import CvBridge; import numpy as np; b=CvBridge(); m=b.cv2_to_imgmsg(np.zeros((4,4,3),np.uint8),'bgr8'); print('cv_bridge OK')"

# model weights into the Linux home (fast local disk)
mkdir -p /root/jacket_follower/models
cp $PROJ/models/jacket_finetuned_v2.pt $PROJ/models/original_best_jacket.pt /root/jacket_follower/models/

# workspace: symlink the package from the Windows project folder, build with symlink-install
mkdir -p /root/ros2_ws/src
ln -sfn $PROJ/ros2_ws/src/jacket_follower /root/ros2_ws/src/jacket_follower
cd /root/ros2_ws && colcon build --symlink-install 2>&1 | tail -3
grep -q "ros2_ws/install/setup.bash" /root/.bashrc || cat >> /root/.bashrc <<'EOF'
source /root/venv/bin/activate
source /root/ros2_ws/install/setup.bash
export PYTHONPATH=/root/venv/lib/python3.12/site-packages:$PYTHONPATH
EOF
echo ML_BUILD_DONE
