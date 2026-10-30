"""Generate the Gazebo scenario worlds. Each world = the same indoor hall + MasterPi + people at their
start poses. The people are moved by the ROS 2 scenario node (jacket_follower/scenario_node.py), which
holds the walking scripts:

  s1_normal    : worker walks 4 m, turns left, 1.8 m, turns left, walks back.            (normal)
  s2_speed     : worker 0.15 -> 0.35 -> 0.60 m/s, stops, turns, walks slowly.            (speed matching)
  s3_challenge : orange-shirt distractor walks in the background; a white-shirt person crosses between
                 robot and worker (occlusion) just as the worker turns right and sprints out of view
                 at 0.8 m/s -> HOLD / SEARCH with a hi-vis-coloured distractor in view.  (challenging/failure)
"""
from pathlib import Path

PKG = Path(__file__).resolve().parents[1] / "ros2_ws" / "src" / "jacket_follower"
OUT = PKG / "worlds"
OUT.mkdir(exist_ok=True)

HALL = """
    <light type="directional" name="sun"><cast_shadows>true</cast_shadows><pose>0 0 10 0 0 0</pose>
      <diffuse>0.9 0.9 0.88 1</diffuse><specular>0.2 0.2 0.2 1</specular><direction>-0.4 0.3 -0.9</direction></light>
    <light type="point" name="ceiling1"><pose>4 0 3.2 0 0 0</pose><diffuse>0.6 0.6 0.6 1</diffuse>
      <attenuation><range>14</range><constant>0.4</constant><linear>0.05</linear><quadratic>0.01</quadratic></attenuation></light>
    <model name="floor"><static>true</static><link name="l">
      <collision name="c"><geometry><plane><normal>0 0 1</normal><size>40 40</size></plane></geometry>
        <surface><friction><ode><mu>1.0</mu><mu2>1.0</mu2></ode></friction></surface></collision>
      <visual name="v"><geometry><plane><normal>0 0 1</normal><size>40 40</size></plane></geometry>
        <material><diffuse>0.55 0.55 0.53 1</diffuse><ambient>0.45 0.45 0.43 1</ambient></material></visual></link></model>
""" + "".join(f"""
    <model name="wall_{n}"><static>true</static><pose>{x} {y} 1.5 0 0 {yaw}</pose><link name="l">
      <collision name="c"><geometry><box><size>{L} 0.15 3</size></box></geometry></collision>
      <visual name="v"><geometry><box><size>{L} 0.15 3</size></box></geometry>
        <material><diffuse>0.82 0.85 0.78 1</diffuse></material></visual></link></model>"""
    for n, x, y, yaw, L in [("n", 6, 5, 0, 20), ("s", 6, -5, 0, 20), ("e", 16, 0, 1.5708, 10), ("w", -4, 0, 1.5708, 10)]) + "".join(f"""
    <model name="{n}"><static>true</static><pose>{x} {y} {z} 0 0 0</pose><link name="l">
      <collision name="c"><geometry><box><size>{sx} {sy} {sz}</size></box></geometry></collision>
      <visual name="v"><geometry><box><size>{sx} {sy} {sz}</size></box></geometry>
        <material><diffuse>{col}</diffuse></material></visual></link></model>"""
    for n, x, y, z, sx, sy, sz, col in [
        ("desk1", 9, 3.6, 0.38, 1.6, 0.7, 0.76, "0.85 0.85 0.85 1"),
        ("desk2", 11.5, -3.6, 0.38, 1.6, 0.7, 0.76, "0.85 0.85 0.85 1"),
        ("cabinet", 14.5, 3.8, 0.9, 0.8, 0.5, 1.8, "0.75 0.78 0.8 1"),
        ("yellow_bin", 7.5, -3.8, 0.35, 0.5, 0.5, 0.7, "0.95 0.85 0.05 1"),   # yellow object: colour distractor
    ])


def person(name, model, x, y, yaw):
    """A walking-person model (moved at runtime by the scenario node through VelocityControl)."""
    return f"""
    <include><uri>model://{model}</uri><name>{name}</name><pose>{x} {y} 0 0 0 {yaw}</pose></include>"""


# start poses; the motion itself is scripted in jacket_follower/scenario_node.py
SCENARIOS = {
    "s1_normal": [person("worker", "worker_vest", 2.0, 0.0, 0.0)],
    "s2_speed": [person("worker", "worker_vest", 2.0, 0.0, 0.0)],
    "s3_challenge": [
        person("worker", "worker_vest", 2.0, 0.0, 0.0),
        person("person_plain", "person_plain", 4.2, 3.0, -1.5708),     # crosses -y between robot and worker
        person("person_orange", "person_orange", 8.5, -3.5, 1.5708),   # walks +y in the background
    ],
}
PILLAR = ""
for name, actors in SCENARIOS.items():
    world = f"""<?xml version="1.0"?>
<sdf version="1.9">
  <world name="hall">
    <physics name="1ms" type="ignored"><max_step_size>0.004</max_step_size><real_time_factor>1.0</real_time_factor></physics>
    <plugin filename="gz-sim-physics-system" name="gz::sim::systems::Physics"/>
    <plugin filename="gz-sim-user-commands-system" name="gz::sim::systems::UserCommands"/>
    <plugin filename="gz-sim-scene-broadcaster-system" name="gz::sim::systems::SceneBroadcaster"/>
    <plugin filename="gz-sim-sensors-system" name="gz::sim::systems::Sensors"><render_engine>ogre2</render_engine></plugin>
    <gui fullscreen="0"><camera name="user_camera"><pose>-2.5 -4.5 4.0 0 0.55 0.75</pose></camera></gui>
    <scene><ambient>0.55 0.55 0.55 1</ambient><background>0.75 0.8 0.85 1</background><shadows>true</shadows></scene>
{HALL}
{PILLAR if name == "s3_challenge" else ""}
    <include><uri>model://masterpi_sim</uri><name>masterpi</name><pose>0 0 0.04 0 0 0</pose></include>
{"".join(actors)}
  </world>
</sdf>
"""
    (OUT / f"{name}.sdf").write_text(world)
print("worlds:", sorted(p.name for p in OUT.glob("*.sdf")))
