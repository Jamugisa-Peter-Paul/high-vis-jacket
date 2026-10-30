"""Physical MasterPi: bridge + the SAME detector and follower nodes used in Gazebo.

ros2 launch jacket_follower real.launch.py robot_ip:=192.168.149.1 enable_motion:=false   # dry run (wheels never move)
ros2 launch jacket_follower real.launch.py enable_motion:=true                            # follow for real
"""
import os

from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument
from launch.substitutions import LaunchConfiguration
from launch_ros.actions import Node


def generate_launch_description():
    pkg = get_package_share_directory("jacket_follower")
    return LaunchDescription([
        DeclareLaunchArgument("robot_ip", default_value="192.168.149.1"),
        DeclareLaunchArgument("enable_motion", default_value="false"),
        DeclareLaunchArgument("model", default_value=os.path.expanduser("~/jacket_follower/models/jacket_finetuned_v2.pt")),
        Node(package="jacket_follower", executable="masterpi_bridge", output="screen",
             parameters=[{"robot_ip": LaunchConfiguration("robot_ip"), "enable_motion": LaunchConfiguration("enable_motion")}]),
        Node(package="jacket_follower", executable="detector", output="screen",
             parameters=[os.path.join(pkg, "config", "detector.yaml"),
                         {"model_path": LaunchConfiguration("model"), "crop_bottom_px": 50}]),
        Node(package="jacket_follower", executable="follower", output="screen",
             # real USB camera: ~71 deg field of view (from the pan-servo calibration: 0.705 px per servo
             # step of 0.09 deg -> f = 449 px); the bridge sends no focal length, so hfov is used
             parameters=[os.path.join(pkg, "config", "follower.yaml"), {"max_lin": 0.25, "hfov_rad": 1.24,
                                                                         "search_pause": 1.5, "search_turn": 0.5,
                                                                         "watchdog": 2.0, "k_turn": 0.8,
                                                                         "acquire_conf": 0.50}]),
             # acquire_conf 0.50: at 2.5-3 m in a dim lab the real vest scores only ~0.6-0.7, so the sim's
             # 0.70 (set against orange-shirt distractors) never let it lock on
             # real robot: camera drops to ~3 fps while driving on a weak battery and the motors have a
             # large dead zone, so turn gently (k_turn 0.8) and make search turns long enough to start moving
        Node(package="rqt_image_view", executable="rqt_image_view", arguments=["/jacket/debug_image"]),
    ])
