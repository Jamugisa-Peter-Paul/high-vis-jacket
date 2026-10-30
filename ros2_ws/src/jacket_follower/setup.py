import os
from glob import glob

from setuptools import setup

package_name = "jacket_follower"


def tree(src):
    """All files under src, keeping the folder structure (for share/ install)."""
    out = {}
    for root, _, files in os.walk(src):
        if files:
            out.setdefault(os.path.join("share", package_name, root), []).extend(os.path.join(root, f) for f in files)
    return list(out.items())


setup(
    name=package_name,
    version="0.1.0",
    packages=[package_name],
    data_files=[
        ("share/ament_index/resource_index/packages", ["resource/" + package_name]),
        ("share/" + package_name, ["package.xml"]),
        ("share/" + package_name + "/launch", glob("launch/*.py")),
        ("share/" + package_name + "/config", glob("config/*.yaml")),
    ] + tree("worlds") + tree("models"),
    install_requires=["setuptools"],
    zip_safe=True,
    maintainer="Jamugisa Peter Paul",
    maintainer_email="Jamugisa-Peter-Paul@users.noreply.github.com",
    description="Safety-jacket follower (ROS 2 Jazzy, Gazebo Harmonic)",
    license="MIT",
    entry_points={
        "console_scripts": [
            "detector = jacket_follower.detector_node:main",
            "follower = jacket_follower.follower_node:main",
            "metrics = jacket_follower.metrics_node:main",
            "scenario = jacket_follower.scenario_node:main",
            "masterpi_bridge = jacket_follower.masterpi_bridge_node:main",
        ],
    },
)
