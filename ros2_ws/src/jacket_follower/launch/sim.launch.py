"""Gazebo simulation: world + MasterPi + bridge + detector + follower + metrics.

ros2 launch jacket_follower sim.launch.py scenario:=s1_normal model:=/path/to/jacket_finetuned_v2.pt
"""
import os

from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument, IncludeLaunchDescription, SetEnvironmentVariable
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch.substitutions import LaunchConfiguration, PathJoinSubstitution
from launch_ros.actions import Node


def generate_launch_description():
    pkg = get_package_share_directory("jacket_follower")
    scenario = LaunchConfiguration("scenario")
    model = LaunchConfiguration("model")
    gui = LaunchConfiguration("gui")
    out_csv = LaunchConfiguration("out_csv")

    gz = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(os.path.join(get_package_share_directory("ros_gz_sim"), "launch", "gz_sim.launch.py")),
        launch_arguments={"gz_args": [PathJoinSubstitution([pkg, "worlds", [scenario, ".sdf"]]), " -r ", LaunchConfiguration("gz_extra")]}.items(),
    )
    bridge = Node(
        package="ros_gz_bridge", executable="parameter_bridge", output="screen",
        arguments=[
            "/clock@rosgraph_msgs/msg/Clock[gz.msgs.Clock",
            "/camera/image_raw@sensor_msgs/msg/Image[gz.msgs.Image",
            "/camera/camera_info@sensor_msgs/msg/CameraInfo[gz.msgs.CameraInfo",
            "/cmd_vel@geometry_msgs/msg/Twist]gz.msgs.Twist",
            "/odom@nav_msgs/msg/Odometry[gz.msgs.Odometry",
            "/range_front_scan@sensor_msgs/msg/LaserScan[gz.msgs.LaserScan",
            "/model/masterpi/odometry@nav_msgs/msg/Odometry[gz.msgs.Odometry",       # ground truth (OdometryPublisher)
            "/model/worker/odometry@nav_msgs/msg/Odometry[gz.msgs.Odometry",
            "/model/worker/cmd_vel@geometry_msgs/msg/Twist]gz.msgs.Twist",
            "/model/person_plain/cmd_vel@geometry_msgs/msg/Twist]gz.msgs.Twist",
            "/model/person_orange/cmd_vel@geometry_msgs/msg/Twist]gz.msgs.Twist",
        ],
        parameters=[{"use_sim_time": True}],
    )
    common = {"use_sim_time": True}
    detector = Node(package="jacket_follower", executable="detector", output="screen",
                    parameters=[os.path.join(pkg, "config", "detector.yaml"), {"model_path": model}, common])
    follower = Node(package="jacket_follower", executable="follower", output="screen",
                    parameters=[os.path.join(pkg, "config", "follower.yaml"),
                                {"acquire_conf": LaunchConfiguration("acquire_conf")}, common])
    metrics = Node(package="jacket_follower", executable="metrics", output="screen",
                   parameters=[{"out_csv": out_csv}, common])
    scenario_node = Node(package="jacket_follower", executable="scenario", output="screen",
                         parameters=[{"scenario": scenario, "start_delay": 4.0}, common])
    viewer = Node(package="rqt_image_view", executable="rqt_image_view", arguments=["/jacket/debug_image"],
                  condition=__import__("launch.conditions", fromlist=["IfCondition"]).IfCondition(gui))

    return LaunchDescription([
        DeclareLaunchArgument("scenario", default_value="s1_normal", description="s1_normal | s2_speed | s3_challenge"),
        DeclareLaunchArgument("model", default_value=os.path.expanduser("~/jacket_follower/models/jacket_finetuned_v2.pt")),
        DeclareLaunchArgument("gui", default_value="true", description="open the detector debug-image viewer"),
        DeclareLaunchArgument("out_csv", default_value="/tmp/scenario.csv"),
        DeclareLaunchArgument("acquire_conf", default_value="0.70",
                              description="score needed to lock onto a new target (0.40 = hysteresis off, ablation)"),
        DeclareLaunchArgument("gz_extra", default_value="", description="extra gz sim args, e.g. '-s --headless-rendering'"),
        SetEnvironmentVariable("GZ_SIM_RESOURCE_PATH", os.path.join(pkg, "models")),
        gz, bridge, detector, follower, metrics, scenario_node, viewer,
    ])
