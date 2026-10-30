"""Gazebo people for the scenarios, built from Fuel 'Walking person' (Open Robotics, CC-BY 4.0):
  worker_vest   : T-shirt recoloured fluorescent yellow-green with two silver reflective bands (TARGET)
  person_plain  : original grey T-shirt                                   (distractor: no vest)
  person_orange : orange T-shirt, no bands                                (hard distractor: hi-vis-like colour)
Each model is visual-only, gravity off, and moved by Gazebo's VelocityControl system
(topic /model/<name>/cmd_vel), driven by the ROS 2 scenario node."""
import shutil
from pathlib import Path

import cv2
import numpy as np

PKG = Path(__file__).resolve().parents[1] / "ros2_ws" / "src" / "jacket_follower"
SRC = PKG / "models_src" / "Walking_person"
OUT = PKG / "models"

tex = cv2.imread(str(SRC / "materials" / "textures" / "tshirt02_texture.png"), cv2.IMREAD_UNCHANGED)
bgr, alpha = tex[..., :3], (tex[..., 3] if tex.shape[2] == 4 else np.full(tex.shape[:2], 255, np.uint8))
hsv = cv2.cvtColor(bgr, cv2.COLOR_BGR2HSV)
cloth = (alpha > 0) & (hsv[..., 2] > 60)                       # shirt pixels (incl. logo)
# front and back pieces touch in the texture: erode to split them, label, then grow labels back over the cloth
core = cv2.erode(cloth.astype(np.uint8), np.ones((25, 25), np.uint8))
n, lab_core, st, _ = cv2.connectedComponentsWithStats(core)
pieces = [i for i in range(1, n) if st[i, cv2.CC_STAT_AREA] > 30000]
dist_maps = [cv2.distanceTransform((lab_core != i).astype(np.uint8), cv2.DIST_L2, 5) for i in pieces]
lab = np.zeros_like(lab_core)
nearest = np.argmin(np.stack(dist_maps), axis=0)
for k, i in enumerate(pieces):
    lab[cloth & (nearest == k)] = i
for i in pieces:                                   # bounding boxes of the grown pieces
    ys, xs = np.where(lab == i)
    st[i, :4] = xs.min(), ys.min(), xs.max() - xs.min(), ys.max() - ys.min()


def paint(hue, sat, val, bands):
    out = hsv.copy()
    shade = hsv[..., 2].astype(np.float32) / max(1.0, float(np.median(hsv[..., 2][cloth])))   # keep wrinkles/shading
    out[..., 0][cloth] = hue
    out[..., 1][cloth] = sat
    out[..., 2][cloth] = np.clip(val * shade[cloth], 0, 255).astype(np.uint8)
    img = cv2.cvtColor(out, cv2.COLOR_HSV2BGR)
    if bands:
        # two shirt pieces in the 1024x1024 UV map: back (upper-left, stored upside down) and front (lower-right)
        S = tex.shape[0] / 1024.0
        yy, xx = np.mgrid[0:tex.shape[0], 0:tex.shape[1]]
        back = cloth & (yy < 500 * S) & (xx < 640 * S)
        front = cloth & ~back
        for piece, fracs in ((front, (0.55, 0.75)), (back, (0.22, 0.42))):     # back is flipped: waist at the top
            ys = np.where(piece.any(axis=1))[0]
            y_top, h = ys.min(), ys.max() - ys.min()
            for f in fracs:
                band = piece & (yy >= y_top + f * h) & (yy < y_top + (f + 0.05) * h)
                img[band] = (205, 205, 205)
    return np.dstack([img, alpha]) if tex.shape[2] == 4 else img


variants = {"worker_vest": paint(38, 235, 245, True), "person_plain": tex.copy(), "person_orange": paint(12, 230, 240, False)}
for name, img in variants.items():
    d = OUT / name
    if d.exists():
        shutil.rmtree(d)
    shutil.copytree(SRC, d, ignore=shutil.ignore_patterns("thumbnails"))
    # the renderer caches meshes/materials/textures by name: the three people share one mesh, so give each
    # its own mesh file, shirt material id and texture file name, or they all render with the first one loaded
    (d / "materials" / "textures" / "tshirt02_texture.png").unlink()
    cv2.imwrite(str(d / "materials" / "textures" / f"tshirt_{name}.png"), img)
    dae = (d / "meshes" / "walking.dae").read_text()
    dae = dae.replace("tshirt02_texture.png", f"tshirt_{name}.png").replace("tshirt02_tshirt02Material", f"tshirt02_{name}")
    (d / "meshes" / f"walking_{name}.dae").write_text(dae)
    (d / "meshes" / "walking.dae").unlink()
    (d / "model.config").write_text(
        f"<?xml version='1.0'?>\n<model><name>{name}</name><version>1.0</version><sdf version='1.9'>model.sdf</sdf>"
        "<author><name>Open Robotics (Walking person, CC-BY 4.0); recoloured for jacket_follower</name></author>"
        "<description>Visual-only walking person moved by VelocityControl.</description></model>\n")
    (d / "model.sdf").write_text(f"""<?xml version="1.0"?>
<sdf version="1.9">
  <model name="{name}">
    <link name="link">
      <gravity>false</gravity>
      <inertial><pose>0 0 0.95 0 0 0</pose><mass>80</mass>
        <inertia><ixx>27.8</ixx><iyy>24.9</iyy><izz>4.6</izz><ixy>0</ixy><ixz>0</ixz><iyz>0</iyz></inertia></inertial>
      <visual name="visual"><pose>0 0 -0.02 0 0 1.5708</pose>
        <geometry><mesh><uri>model://{name}/meshes/walking_{name}.dae</uri></mesh></geometry></visual>
    </link>
    <plugin filename="gz-sim-velocity-control-system" name="gz::sim::systems::VelocityControl"/>
    <plugin filename="gz-sim-odometry-publisher-system" name="gz::sim::systems::OdometryPublisher">
      <odom_frame>world</odom_frame><robot_base_frame>{name}</robot_base_frame><odom_publish_frequency>20</odom_publish_frequency><dimensions>2</dimensions></plugin>
  </model>
</sdf>
""")
    cv2.imwrite(str(Path(__file__).resolve().parents[1] / "results" / f"shirt_{name}.png"), cv2.resize(img[..., :3], (256, 256)))
for stale in ("worker_vest_actor", "visitor_plain", "visitor_orange"):
    if (OUT / stale).exists():
        shutil.rmtree(OUT / stale)
print("models:", sorted(p.name for p in OUT.iterdir()), "| shirt pieces:", len(pieces))
