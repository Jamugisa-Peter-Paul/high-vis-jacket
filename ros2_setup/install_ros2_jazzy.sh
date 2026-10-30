#!/bin/bash
# Install ROS 2 Jazzy + Gazebo Harmonic (ros_gz) on Ubuntu 24.04. Run as root inside WSL.
set -e
export DEBIAN_FRONTEND=noninteractive
apt-get update
apt-get install -y software-properties-common curl locales
locale-gen en_US en_US.UTF-8 && update-locale LC_ALL=en_US.UTF-8 LANG=en_US.UTF-8
add-apt-repository -y universe

# ROS 2 apt source (official ros2-apt-source package)
VER=$(curl -s https://api.github.com/repos/ros-infrastructure/ros-apt-source/releases/latest | grep -F '"tag_name"' | awk -F'"' '{print $4}')
curl -L -o /tmp/ros2-apt-source.deb "https://github.com/ros-infrastructure/ros-apt-source/releases/download/${VER}/ros2-apt-source_${VER}.$(. /etc/os-release && echo ${UBUNTU_CODENAME:-$VERSION_CODENAME})_all.deb"
dpkg -i /tmp/ros2-apt-source.deb
apt-get update

apt-get install -y ros-jazzy-desktop ros-dev-tools \
    ros-jazzy-ros-gz ros-jazzy-vision-msgs ros-jazzy-cv-bridge ros-jazzy-image-transport \
    ros-jazzy-xacro ros-jazzy-robot-state-publisher ros-jazzy-joint-state-publisher ros-jazzy-rqt-image-view \
    python3-pip python3-venv python3-colcon-common-extensions
grep -q "ros/jazzy/setup.bash" /root/.bashrc || echo "source /opt/ros/jazzy/setup.bash" >> /root/.bashrc
source /opt/ros/jazzy/setup.bash
echo "ROS_DISTRO=$ROS_DISTRO"
gz sim --versions || true
echo INSTALL_DONE
