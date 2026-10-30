"""Final presentation (UCU template, 10 slides) for the safety-jacket follower project.

  py -3.13 presentation/make_final_deck.py   -> presentation/Final_Presentation_Jacket_Follower.pptx

Starts from the birds-CNN deck (already on the UCU template: title slide, logo, band, footer) and keeps
only its title slide; every other slide is built here on the template's TITLE_ONLY layout.
"""
import copy
from pathlib import Path

from lxml import etree
from pptx import Presentation
from pptx.chart.data import CategoryChartData
from pptx.dml.color import RGBColor
from pptx.enum.chart import XL_CHART_TYPE, XL_LABEL_POSITION, XL_LEGEND_POSITION
from pptx.enum.shapes import MSO_CONNECTOR, MSO_SHAPE
from pptx.enum.text import MSO_ANCHOR, PP_ALIGN
from pptx.oxml.ns import qn
from pptx.util import Inches, Pt

P = Path(__file__).resolve().parents[1]
MEDIA = P / "presentation" / "media"
BASE = Path(r"D:\mscs\intelligent_systems_and_robotics\submission\4_Presentation\Presentation_Birds_CNN.pptx")
OUT = P / "presentation" / "Final_Presentation_Jacket_Follower.pptx"

NAVY, MAGENTA, INK, MUTED = "0B3D91", "D7004D", "1F2A36", "5B6B7C"
NAVY_T, PINK_T, GREY_T, HIVIS, GREEN = "E8EEF8", "FBE6EE", "F2F4F7", "C8EE1E", "1E7B46"
FONT = "Trebuchet MS"          # matches the template and the birds deck
X0, X1 = 1.35, 12.4            # content area (clear of the template's bottom-left graphic)

prs = Presentation(BASE)
# keep only the title slide of the base deck
ids = prs.slides._sldIdLst
for sid in list(ids)[1:]:
    prs.part.drop_rel(sid.rId)
    ids.remove(sid)
LAYOUT = prs.slide_layouts.get_by_name("TITLE_ONLY")


def rgb(h):
    return RGBColor.from_string(h)


def style_run(r, size, bold=False, color=INK, italic=False):
    r.font.size, r.font.bold, r.font.italic, r.font.name = Pt(size), bold, italic, FONT
    r.font.color.rgb = rgb(color)


def text(slide, x, y, w, h, content, size=14, bold=False, color=INK, align=PP_ALIGN.LEFT,
         anchor=MSO_ANCHOR.TOP, name=None, italic=False):
    """content: str, or list of paragraphs; a paragraph is a str or a list of (text, {opts}) runs."""
    tb = slide.shapes.add_textbox(Inches(x), Inches(y), Inches(w), Inches(h))
    if name:
        tb.name = name
    tf = tb.text_frame
    tf.word_wrap = True
    tf.vertical_anchor = anchor
    for m in ("margin_left", "margin_right", "margin_top", "margin_bottom"):
        setattr(tf, m, Inches(0.04))
    paras = content if isinstance(content, list) else [content]
    for i, para in enumerate(paras):
        p = tf.paragraphs[0] if i == 0 else tf.add_paragraph()
        p.alignment = align
        runs = para if isinstance(para, list) else [(para, {})]
        for t, o in runs:
            r = p.add_run()
            r.text = t
            style_run(r, o.get("size", size), o.get("bold", bold), o.get("color", color), o.get("italic", italic))
    return tb


def bullets(slide, x, y, w, h, items, size=15, color=INK, space=6, name=None):
    tb = text(slide, x, y, w, h, items, size=size, color=color, name=name)
    for p in tb.text_frame.paragraphs:
        pPr = p._p.get_or_add_pPr()
        pPr.set("marL", str(Inches(0.25)))
        pPr.set("indent", str(-Inches(0.22)))
        for tag in ("a:buNone", "a:buChar", "a:buAutoNum"):
            for e in pPr.findall(qn(tag)):
                pPr.remove(e)
        clr = etree.SubElement(pPr, qn("a:buClr"))
        etree.SubElement(clr, qn("a:srgbClr")).set("val", MAGENTA)
        bu = etree.SubElement(pPr, qn("a:buChar"))
        bu.set("char", "•")
        p.space_after = Pt(space)
    return tb


def box(slide, x, y, w, h, fill, line=None, shape=MSO_SHAPE.ROUNDED_RECTANGLE, name=None, radius=0.08):
    s = slide.shapes.add_shape(shape, Inches(x), Inches(y), Inches(w), Inches(h))
    if name:
        s.name = name
    s.fill.solid()
    s.fill.fore_color.rgb = rgb(fill)
    if line:
        s.line.color.rgb = rgb(line)
        s.line.width = Pt(1.25)
    else:
        s.line.fill.background()
    s.shadow.inherit = False
    if shape == MSO_SHAPE.ROUNDED_RECTANGLE:
        s.adjustments[0] = radius
    s.text_frame.text = ""
    return s


def chip(slide, x, y, w, h, label, fill=NAVY, color="FFFFFF", size=13, bold=True, name=None):
    s = box(slide, x, y, w, h, fill, name=name, radius=0.25)
    tf = s.text_frame
    tf.word_wrap = True
    for m in ("margin_left", "margin_right", "margin_top", "margin_bottom"):
        setattr(tf, m, Inches(0.04))
    tf.vertical_anchor = MSO_ANCHOR.MIDDLE
    lines = label.split("\n")
    for i, ln in enumerate(lines):
        p = tf.paragraphs[0] if i == 0 else tf.add_paragraph()
        p.alignment = PP_ALIGN.CENTER
        r = p.add_run()
        r.text = ln
        style_run(r, size if i == 0 else size - 2, bold if i == 0 else False, color)
    return s


def arrow(slide, x1, y1, x2, y2, color=MUTED, width=2.0):
    c = slide.shapes.add_connector(MSO_CONNECTOR.STRAIGHT, Inches(x1), Inches(y1), Inches(x2), Inches(y2))
    c.line.color.rgb = rgb(color)
    c.line.width = Pt(width)
    ln = c.line._get_or_add_ln()
    tail = etree.SubElement(ln, qn("a:tailEnd"))
    tail.set("type", "triangle")
    tail.set("w", "med")
    tail.set("len", "med")
    return c


def picture(slide, path, x, y, w=None, h=None, name=None):
    pic = slide.shapes.add_picture(str(path), Inches(x), Inches(y),
                                   Inches(w) if w else None, Inches(h) if h else None)
    if name:
        pic.name = name
    return pic


def movie(slide, path, x, y, w, h, poster, name):
    m = slide.shapes.add_movie(str(path), Inches(x), Inches(y), Inches(w), Inches(h),
                               poster_frame_image=str(poster), mime_type="video/mp4")
    m.name = name
    return m


def new_slide(title, notes):
    s = prs.slides.add_slide(LAYOUT)
    t = s.shapes.title
    t.text = title
    t.width = Inches(9.5)                       # stop short of the UCU logo (top right)
    style_run(t.text_frame.paragraphs[0].runs[0], 28, False, "1F497D")
    t.text_frame.vertical_anchor = MSO_ANCHOR.MIDDLE
    s.notes_slide.notes_text_frame.text = notes
    return s


def caption(slide, x, y, w, t, h=0.3):
    return text(slide, x, y, w, h, t, size=11, color=MUTED, italic=True)


# ------------------------------------------------------------------ 1. title (re-use the UCU title slide)
title = prs.slides[0]
for sh in title.shapes:
    if not sh.has_text_frame:
        continue
    t = sh.text_frame.text
    if t.startswith("Bird Species"):
        sh.text_frame.paragraphs[0].runs[0].text = "Safety-Jacket Follower Robot"
    elif t.startswith("A convolutional"):
        sh.text_frame.paragraphs[0].runs[0].text = "Fine-tuned YOLOv8 detector, ROS 2, Gazebo and a Hiwonder MasterPi robot"
    elif t.startswith("Sat "):
        sh.text_frame.paragraphs[0].runs[0].text = "Thu 29th Oct 2026"
    elif t.startswith("Course"):
        values = [("Course: ", "Intelligent Systems and Robotics, Final Project"),
                  ("Student 1: ", "Jamugisa Peter Paul (Reg. No. S25M25/008)"),
                  ("Student 2: ", "Moses (Reg. No. ________)"),
                  ("Programme: ", "MSc Computer Science"),
                  ("Date: ", "29 October 2026")]
        for p, (lab, val) in zip(sh.text_frame.paragraphs, values):
            p.runs[0].text = lab
            p.runs[1].text = val
            for r in p.runs[2:]:
                r.text = ""
title.notes_slide.notes_text_frame.text = (
    "PETER: Good morning. We are Jamugisa Peter Paul and Moses. Our project is a robot that finds the person "
    "wearing a safety jacket and follows them, keeping a safe gap and speeding up when they speed up. "
    "I built and fine-tuned the jacket detector and deployed the system on the real Hiwonder MasterPi robot; "
    "Moses built the ROS 2 system and the Gazebo simulation. We will cover the problem, data, detector, "
    "ROS 2 design, simulation results, the real robot, the challenges we met, and what comes next.")

# ------------------------------------------------------------------ 2. problem
s = new_slide("The problem: follow the worker in the jacket",
              "PETER: On a site, a robot that carries tools could follow the worker who is wearing the hi-vis "
              "jacket and ignore everyone else. Our target object is one class: the safety jacket. The robot must "
              "find it, keep about 1.5 metres behind, speed up when the person speeds up, search when it loses "
              "them, and always fail safe. The pipeline at the bottom is the whole system in one line.")
bullets(s, X0, 2.05, 5.75, 3.4, [
    [("Goal: ", {"bold": True}), ("the MasterPi robot finds the person wearing a hi-vis safety jacket and follows them", {})],
    [("Speed matching: ", {"bold": True}), ("keeps a ~1.5 m gap and speeds up when the person speeds up", {})],
    [("Search: ", {"bold": True}), ("turns to look for the jacket when it is lost; people without jackets are ignored", {})],
    [("Safety first: ", {"bold": True}), ("stops if the camera feed stalls, an obstacle is too close, or the detection is uncertain", {})],
    [("Target object: ", {"bold": True}), ("one class, ", {}), ("safety_jacket", {"bold": True, "color": NAVY}),
     (" (hi-vis vest with reflective bands)", {})],
], size=15, name="Problem bullets")
picture(s, MEDIA / "robot_lab.jpg", 7.8, 2.05, w=4.6, name="Robot in the lab photo")
caption(s, 7.8, 5.53, 4.6, "Our Hiwonder MasterPi (Raspberry Pi 4B) in the lab")
steps = ["Arm camera", "YOLOv8n jacket\ndetector", "Follower\nstate machine", "Speed + turn\ncommand", "Mecanum\nwheels"]
cw, gap, y = 1.75, 0.55, 6.12
for i, st in enumerate(steps):
    x = X0 + i * (cw + gap)
    chip(s, x, y, cw, 0.62, st.split("\n")[0] if "\n" not in st else st.replace("\n", " "),
         fill=NAVY if i not in (1,) else MAGENTA, size=12, name=f"Pipeline step {i + 1}")
    if i < len(steps) - 1:
        arrow(s, x + cw + 0.05, y + 0.31, x + cw + gap - 0.05, y + 0.31)

# ------------------------------------------------------------------ 3. dataset
s = new_slide("Dataset: robot frames, public vests, negatives",
              "PETER: The original model had only 301 eye-level phone photos of one jacket, so it struggled on the "
              "robot's low camera. I recorded frames from the robot camera and labelled them automatically with "
              "Grounding DINO plus a hi-vis colour check, then checked them by hand. I added 1,500 human-labelled "
              "public vest photos and 700 photos of people without vests, so the model also learns what is NOT a "
              "jacket. Testing uses three sets the model never trained on, including a robot block split by time "
              "so neighbouring frames cannot leak between training and testing.")
cards = [("3,140", "training images in total\n(+115 for validation)"),
         ("328", "robot-camera frames,\nauto-labelled + human-checked"),
         ("1,500", "public vest photos,\nhuman-labelled (CC BY 4.0)"),
         ("700", "people WITHOUT vests:\nnegatives against false alarms")]
for i, (num, lab) in enumerate(cards):
    cx, cy = X0 + (i % 2) * 2.75, 2.05 + (i // 2) * 2.0
    box(s, cx, cy, 2.55, 1.8, NAVY_T if i != 3 else PINK_T, name=f"Dataset card {i + 1}")
    text(s, cx + 0.15, cy + 0.12, 2.25, 0.75, num, size=34, bold=True, color=NAVY if i != 3 else MAGENTA,
         name=f"Dataset number {i + 1}")
    text(s, cx + 0.15, cy + 0.88, 2.3, 0.85, lab.split("\n"), size=12, color=INK)
text(s, X0, 6.12, 5.3, 0.55, "Also: 284 original phone photos. One merged class, 320 px input.", size=12, color=MUTED)
picture(s, MEDIA / "robot_labels_crop.jpg", 7.1, 2.05, w=5.3, name="Labelled robot frames")
caption(s, 7.1, 4.73, 5.3, "Robot-camera frames with checked jacket labels (red boxes)")
rows = [("Independent test set", "Images"), ("Robot camera, held-out time block", "99"),
        ("Public set A (HB1204)", "242"), ("Public set B (Vincent)", "208")]
tbl = s.shapes.add_table(4, 2, Inches(7.1), Inches(5.1), Inches(5.3), Inches(1.5)).table
tbl.columns[0].width, tbl.columns[1].width = Inches(4.1), Inches(1.2)
for r, row in enumerate(rows):
    for c, val in enumerate(row):
        cell = tbl.cell(r, c)
        cell.text = val
        cell.fill.solid()
        cell.fill.fore_color.rgb = rgb(NAVY if r == 0 else ("FFFFFF" if r % 2 else GREY_T))
        para = cell.text_frame.paragraphs[0]
        para.alignment = PP_ALIGN.RIGHT if c == 1 else PP_ALIGN.LEFT
        style_run(para.runs[0], 12, r == 0, "FFFFFF" if r == 0 else INK)
        cell.margin_top = cell.margin_bottom = Inches(0.03)

# ------------------------------------------------------------------ 4. detector
s = new_slide("Detector: fine-tuning made it far more reliable",
              "PETER: Here are the results on the three test sets. On the robot's own camera, mAP50 rose from 0.82 to "
              "0.93 and the jacket is found in 98 percent of frames instead of 69. On public photos from other places "
              "it went from very poor to good, and false alarms on people without vests dropped from 22 to 15 percent. "
              "An important lesson: my first fine-tune used only robot frames and doubled the false alarms, which is "
              "why version 2 includes 700 negative images.")
cd = CategoryChartData()
cd.categories = ["Robot camera (99)", "Public set A (242)", "Public set B (208)"]
cd.add_series("Original model", (0.824, 0.128, 0.332))
cd.add_series("Fine-tuned v2", (0.925, 0.811, 0.874))
gf = s.shapes.add_chart(XL_CHART_TYPE.COLUMN_CLUSTERED, Inches(X0), Inches(2.0), Inches(6.6), Inches(4.25), cd)
gf.name = "mAP50 chart"
ch = gf.chart
ch.has_title = True
ch.chart_title.text_frame.text = "mAP50 on test sets never used in training"
style_run(ch.chart_title.text_frame.paragraphs[0].runs[0], 14, True, INK)
ch.has_legend = True
ch.legend.position = XL_LEGEND_POSITION.BOTTOM
ch.legend.include_in_layout = False
ch.legend.font.size, ch.legend.font.name = Pt(12), FONT
for ser, col in zip(ch.series, ("A7B1BD", NAVY)):
    ser.format.fill.solid()
    ser.format.fill.fore_color.rgb = rgb(col)
plot = ch.plots[0]
plot.gap_width = 70
plot.has_data_labels = True
dl = plot.data_labels
dl.number_format, dl.number_format_is_linked = "0.00", False
dl.position = XL_LABEL_POSITION.OUTSIDE_END
dl.font.size, dl.font.name = Pt(12), FONT
va = ch.value_axis
va.maximum_scale, va.minimum_scale = 1.0, 0
va.has_major_gridlines = True
va.major_gridlines.format.line.color.rgb = rgb("E3E7EC")
va.tick_labels.font.size = Pt(11)
va.format.line.fill.background()
ch.category_axis.tick_labels.font.size = Pt(12)
ch.category_axis.tick_labels.font.name = FONT
stats = [("69% → 98%", "robot-camera frames where\nthe jacket is found"),
         ("0.82 → 0.93", "mAP50 on the robot camera"),
         ("22% → 15%", "false alarms on people\nwithout vests (set B)")]
for i, (big, small) in enumerate(stats):
    y = 2.05 + i * 1.3
    box(s, 8.3, y, 4.1, 1.15, NAVY_T, name=f"Stat card {i + 1}")
    text(s, 8.45, y + 0.06, 3.85, 0.6, big, size=26, bold=True, color=NAVY)
    text(s, 8.45, y + 0.62, 3.85, 0.5, small.split("\n"), size=11, color=INK)
text(s, 8.3, 5.98, 4.1, 0.75, ["YOLOv8n · 320 px · AdamW + cosine LR · early stop",
                               "(best epoch 56 of 76, 31 min on an RTX 4050)"], size=11, color=MUTED)

# ------------------------------------------------------------------ 5. ROS 2 architecture
s = new_slide("ROS 2: same nodes in Gazebo and on the robot",
              "MOSES: Our ROS 2 Jazzy package has one node per job. The camera images come either from the Gazebo "
              "camera or, on the real robot, from a bridge node that reads the robot's video stream. The detector "
              "node runs YOLO on the GPU in 15 to 20 milliseconds and publishes detections. The follower node turns "
              "them into speed and turn commands with a state machine, and the commands go to Gazebo's mecanum drive "
              "or to the real robot. Because the detector and follower are identical in both worlds, what we test "
              "in simulation is what runs on the robot. The follower estimates distance from the box size, keeps "
              "1.5 metres, and adds the rate of change of distance, which is what makes it speed up with the person.")
nodes = [(X0, "Camera source", "Gazebo camera, or\nrobot video bridge", NAVY),
         (4.35, "detector_node", "YOLOv8n on GPU\n15-20 ms per frame", MAGENTA),
         (7.35, "follower_node", "state machine +\nspeed / turn control", NAVY),
         (10.35, "Robot base", "Gazebo drive, or\nreal robot (UDP)", NAVY)]
for x, head, sub, col in nodes:
    box(s, x, 2.05, 2.05, 1.3, col, name=f"Node {head}")
    text(s, x + 0.05, 2.12, 1.95, 0.42, head, size=14, bold=True, color="FFFFFF", align=PP_ALIGN.CENTER)
    text(s, x + 0.05, 2.55, 1.95, 0.75, sub.split("\n"), size=11, color="FFFFFF", align=PP_ALIGN.CENTER)
for (xa, ta), (xb, _t) in zip([(n[0], None) for n in nodes[:-1]], [(n[0], None) for n in nodes[1:]]):
    arrow(s, xa + 2.1, 2.7, xb - 0.05, 2.7, color=INK)
for x, t in ((3.85, "/camera/image_raw"), (6.85, "/jacket/detections"), (9.85, "/cmd_vel")):
    text(s, x - 0.75, 3.4, 1.5, 0.3, t, size=10, color=MUTED, align=PP_ALIGN.CENTER)
chip(s, 7.35, 3.85, 2.05, 0.45, "front sonar  /range_front", fill=GREY_T, color=INK, size=11, bold=False,
     name="Sonar input")
arrow(s, 8.375, 3.85, 8.375, 3.4, color=INK, width=1.5)
text(s, 10.35, 3.85, 2.05, 0.5, "sim only: scenario + metrics nodes", size=10, color=MUTED, italic=True)
text(s, X0, 4.5, 5.0, 0.4, "Follower state machine", size=15, bold=True, color=NAVY)
states = [("SEARCH", MUTED), ("CONFIRMING", NAVY), ("FOLLOW", GREEN), ("HOLD", "B07800")]
for i, (st, col) in enumerate(states):
    x = X0 + i * 1.38
    chip(s, x, 5.0, 1.26, 0.5, st, fill=col, size=10, name=f"State {st}")
    if i < len(states) - 1:
        arrow(s, x + 1.27, 5.25, x + 1.37, 5.25, color=INK, width=1.5)
chip(s, X0, 5.7, 1.8, 0.5, "TOO_CLOSE", fill="B07800", size=10, name="State TOO_CLOSE")
chip(s, X0 + 1.95, 5.7, 1.8, 0.5, "E_STOP", fill=MAGENTA, size=10, name="State E_STOP")
text(s, X0 + 3.9, 5.7, 1.5, 0.6, ["stop states:", "safety"], size=10, color=MUTED)
bullets(s, 6.95, 4.5, 5.45, 2.3, [
    [("Distance: ", {"bold": True}), ("d = f · 0.45 m / box width (also from height and sonar; smallest wins)", {})],
    [("Speed: ", {"bold": True}), ("v = 0.8 (d − 1.5) + 0.6 ḋ  → faster when the person speeds up", {})],
    [("Lock-on: ", {"bold": True}), ("3 frames in a row, score ≥ 0.70; keep tracking down to 0.40", {})],
    [("Fail-safe: ", {"bold": True}), ("no detector output for 1 s or sonar < 0.25 m → stop", {})],
], size=13, space=4, name="Control bullets")

# ------------------------------------------------------------------ 6. Gazebo
s = new_slide("Gazebo: robot model, world and 3 scenarios",
              "MOSES: The simulation runs ROS 2 Jazzy with Gazebo Harmonic. I modelled the MasterPi with mecanum "
              "wheels, the arm camera and the front sonar, and built a 20 by 10 metre hall. The people are walking "
              "person models driven by a scenario node, and Gazebo's odometry gives us ground truth for every "
              "measurement. This clip is the robot's camera in the hardest scenario, with a white-shirt person "
              "crossing and an orange-shirt distractor. Scenario 1 is a normal walk with two turns, scenario 2 "
              "changes speed, and scenario 3 is the challenging one.")
movie(s, P / "results/sim/s3_challenge/debug.mp4", X0, 2.05, 5.2, 3.9, MEDIA / "poster_sim_s3.jpg",
      "Gazebo scenario 3 video")
caption(s, X0, 6.0, 5.2, "Robot camera in scenario 3 (click to play)")
bullets(s, 6.95, 2.0, 5.45, 2.35, [
    "ROS 2 Jazzy + Gazebo Harmonic on Ubuntu 24.04 (WSL2)",
    "MasterPi model: mecanum drive, arm camera 640×480 at 15 Hz, front sonar",
    "20 × 10 m hall with desks; walking people moved by a scenario node",
    "Ground truth from Gazebo odometry → CSV metrics for every run",
], size=13, space=4, name="Gazebo setup bullets")
scen = [("S1  Normal", "walk 4 m, two 90° turns, walk back", NAVY),
        ("S2  Speed", "0.15 → 0.35 → 0.60 m/s, stop, turn", NAVY),
        ("S3  Challenge", "view blocked, worker sprints out of sight, orange-shirt distractor", MAGENTA)]
for i, (head, sub, col) in enumerate(scen):
    y = 4.45 + i * 0.78
    chip(s, 6.95, y, 1.75, 0.66, head, fill=col, size=12, name=f"Scenario chip {i + 1}")
    text(s, 8.85, y, 3.55, 0.66, sub.split("\n"), size=12, color=INK, anchor=MSO_ANCHOR.MIDDLE)

# ------------------------------------------------------------------ 7. simulation results
s = new_slide("Simulation: it follows in all three scenarios",
              "MOSES: These numbers come from Gazebo ground truth. The robot followed 96 to 100 percent of the time in "
              "the first two scenarios and never got closer than 1.17 metres, against a stop distance of 0.8. In "
              "scenario 2 it matches 0.15 and 0.35 metres per second and caps at its 0.35 limit when the worker "
              "runs at 0.6. In scenario 3 it searched for 27 seconds while the worker was hidden, ignored the orange "
              "shirt and found the worker again. When we switched off the lock-on hysteresis, the robot followed the "
              "orange shirt for 11 seconds: that is our failure case and the reason for the design.")
rows = [("Scenario", "Following", "Wrong person", "Closest", "Ends on worker", "Speed match (worker → robot)"),
        ("S1 normal walk", "96%", "0 s", "1.17 m", "yes", "0.30 → 0.19 m/s (incl. turns)"),
        ("S2 speed changes", "100%", "0 s", "1.82 m", "yes", "0.15→0.13, 0.35→0.32, 0.6→cap"),
        ("S3 challenge", "70%", "0 s", "1.93 m", "yes", "searched 27 s, re-found the worker"),
        ("S3, hysteresis off", "39%", "11 s", "1.95 m", "NO", "failure: followed orange shirt")]
widths = (2.2, 1.45, 1.3, 1.05, 1.65, 3.4)
tbl = s.shapes.add_table(len(rows), len(widths), Inches(X0), Inches(2.0), Inches(sum(widths)), Inches(2.1)).table
for c, wdt in enumerate(widths):
    tbl.columns[c].width = Inches(wdt)
for r, row in enumerate(rows):
    for c, val in enumerate(row):
        cell = tbl.cell(r, c)
        cell.text = val
        cell.fill.solid()
        bad = r == 4
        cell.fill.fore_color.rgb = rgb(NAVY if r == 0 else (PINK_T if bad else ("FFFFFF" if r % 2 else GREY_T)))
        para = cell.text_frame.paragraphs[0]
        style_run(para.runs[0], 12, r == 0 or (bad and c in (2, 4)), "FFFFFF" if r == 0 else (MAGENTA if bad and c in (2, 4) else INK))
        cell.margin_top = cell.margin_bottom = Inches(0.03)
picture(s, P / "results/sim/s2_speed/analysis.png", X0, 4.35, w=7.45, name="Scenario 2 analysis plot")
caption(s, X0, 6.5, 7.45, "S2 ground truth: top view, true vs estimated distance, worker vs robot speed")
box(s, 9.0, 4.35, 3.4, 2.4, PINK_T, name="Ablation card")
text(s, 9.15, 4.45, 3.1, 0.45, "Why lock-on hysteresis?", size=14, bold=True, color=MAGENTA)
text(s, 9.15, 4.9, 3.1, 1.8, ["The detector scores an orange shirt ~0.55. Without the 0.70 lock-on rule the "
                              "robot followed the wrong person for 11 s; with it, 0 s."], size=12, color=INK)

# ------------------------------------------------------------------ 8. physical robot
s = new_slide("Real robot: deployed, detects and locks on",
              "PETER: I deployed the same detector and follower on the real MasterPi. The robot runs a small server "
              "that streams the camera and receives motor commands, with its own half-second stop if commands stop; "
              "a bridge node on the laptop connects it to ROS 2. On the left, a phone video of the robot in the lab "
              "turning and moving towards the jacket on the chair. On the right, the robot's own view: it finds the "
              "jacket, scores 0.72 to 0.84, and switches to FOLLOW. Standing still, the camera runs at 8.5 frames per "
              "second, detection takes 15 to 20 milliseconds and commands round-trip in 10 milliseconds.")
text(s, X0, 1.95, 11.05, 0.4, [[("Robot: ", {"bold": True}), ("camera + motor server, 0.5 s stop watchdog     ", {}),
                                ("Laptop: ", {"bold": True}), ("ROS 2 bridge + the same detector and follower", {})]],
     size=12, color=INK)
movie(s, P / "results/real/following.mp4", X0, 2.45, 5.6, 3.15, MEDIA / "poster_following.jpg", "Phone video of robot")
movie(s, P / "results/real/highlights.mp4", 7.3, 2.45, 4.2, 3.15, MEDIA / "poster_highlights.jpg", "Robot view highlights")
caption(s, X0, 5.62, 5.6, "Phone view: robot drives towards the jacket (click to play)")
caption(s, 7.3, 5.62, 5.1, "Robot view: jacket found (0.72-0.84) → FOLLOW, three runs")
facts = [("8.5 fps", "camera (standing)"), ("15-20 ms", "detection, RTX 4050"), ("10 ms", "command round trip"),
         ("0.72-0.84", "jacket score on robot")]
for i, (big, small) in enumerate(facts):
    x = X0 + i * 2.8
    box(s, x, 6.0, 2.6, 0.78, NAVY_T, name=f"Robot fact {i + 1}")
    text(s, x + 0.1, 6.02, 2.4, 0.42, big, size=17, bold=True, color=NAVY)
    text(s, x + 0.1, 6.42, 2.4, 0.33, small, size=11, color=INK)

# ------------------------------------------------------------------ 9. challenges
s = new_slide("Real-robot challenges and our fixes",
              "PETER: The real robot taught us more than the simulation. The batteries sagged from 8 to about 6 volts "
              "under load and the Raspberry Pi rebooted mid-run; once, the motor board kept its last speed and the "
              "robot spun on the spot, so we added a service that zeroes the motors at every boot. The camera was "
              "out of focus and dim: 640 by 480 gave 1.5 frames per second until we switched it to MJPG mode, and "
              "while driving on a weak battery it still drops to 2 or 3. The motors do nothing below about 30 "
              "percent power and then jump, so small turns overshoot. On the right, the robot's view while "
              "searching: the jacket is visible but too small and dim at 3 metres to be detected. We are still "
              "working on these, starting with fresh batteries.")
probs = [("Battery brown-outs", "8.0 → 6.2 V under load; the Pi rebooted mid-run",
          "volt-compensated motor power; slow arm moves"),
         ("Runaway after a reboot", "motor board kept the last speed; robot spun",
          "motors zeroed at every boot + 0.5 s watchdog"),
         ("Blurry, dim camera", "out of focus; 1.5 fps; jacket missed at 3 m",
          "manual focus, MJPG mode (8.5 fps), camera tilt"),
         ("Frame rate drops while driving", "2-3 fps under motor load → late reactions",
          "2 s watchdog, stop-and-look search, gentler turns"),
         ("Motor dead zone", "no motion below ~30 % power, then sudden spins",
          "start-power model + 60 % cap (caught a 100 % bug)"),
         ("Wi-Fi drops", "laptop silently left the robot's hotspot",
          "auto-reconnect; robot stops itself when commands stop")]
for i, (head, prob, fix) in enumerate(probs):
    x, y = X0 + (i % 2) * 3.85, 2.0 + (i // 2) * 1.62
    box(s, x, y, 3.7, 1.47, GREY_T, name=f"Challenge card {i + 1}")
    text(s, x + 0.12, y + 0.07, 3.5, 0.35, head, size=13, bold=True, color=MAGENTA)
    text(s, x + 0.12, y + 0.42, 3.5, 0.5, prob, size=11, color=INK)
    text(s, x + 0.12, y + 0.93, 3.5, 0.5, [[("Fix: ", {"bold": True, "color": GREEN}), (fix, {})]], size=11, color=INK)
movie(s, P / "results/real/search.mp4", 9.15, 2.0, 3.25, 1.83, MEDIA / "poster_search.jpg", "Robot search video")
caption(s, 9.15, 3.88, 3.25, "Robot view while searching: jacket in view but too small and dim at 3 m", h=0.55)
box(s, 9.15, 4.6, 3.25, 2.15, NAVY_T, name="Lesson card")
text(s, 9.3, 4.68, 3.0, 0.4, "Lesson", size=14, bold=True, color=NAVY)
text(s, 9.3, 5.08, 3.0, 1.6, ["Simulation proved the logic; the real robot is limited by power, light and "
                              "motors. Fresh batteries come first."], size=12, color=INK)

# ------------------------------------------------------------------ 10. contributions + conclusion
s = new_slide("Contributions, conclusion, next steps",
              "PETER and MOSES: To conclude: the fine-tuned detector is much more reliable on the robot's camera, the "
              "robot follows in all three Gazebo scenarios and the lock-on rule stops it following the wrong person, "
              "and the full system runs on the real robot, where it detects and locks onto the jacket. Steady real "
              "following is limited by the battery, the camera and the motors, and that is our next step. Thank you, "
              "we welcome your questions.")
people = [("Jamugisa Peter Paul", "S25M25/008", ["Detector: robot data, auto-labelling, fine-tuning v1/v2, evaluation",
                                                 "Physical robot: server, ROS 2 bridge, calibration, safety fixes, live tests"]),
          ("Moses", "Reg. No. ________", ["ROS 2 package: detector, follower, bridge and scenario nodes, launch files",
                                          "Gazebo: MasterPi model, hall world, people, 3 scenarios, metrics"])]
for i, (name, reg, items) in enumerate(people):
    x = X0 + i * 5.6
    box(s, x, 2.0, 5.45, 1.95, NAVY_T, name=f"Contribution card {i + 1}")
    text(s, x + 0.15, 2.07, 5.1, 0.42, [[(name, {"bold": True, "color": NAVY, "size": 16}),
                                         ("   " + reg, {"color": MUTED, "size": 12})]])
    bullets(s, x + 0.15, 2.55, 5.15, 1.45, items, size=12, space=4)
text(s, X0, 4.25, 5.4, 0.4, "Conclusion", size=15, bold=True, color=NAVY)
bullets(s, X0, 4.65, 5.45, 2.1, [
    "Detector: mAP50 0.82 → 0.93 on the robot camera",
    "Gazebo: follows in all 3 scenarios; lock-on rule prevents following the wrong person",
    "Real robot: full pipeline deployed; detects and locks on to the jacket",
], size=13, space=4)
text(s, 6.95, 4.25, 5.4, 0.4, "Next steps", size=15, bold=True, color=MAGENTA)
bullets(s, 6.95, 4.65, 3.3, 2.1, [
    "Fresh batteries, then repeat the following test",
    "Test set from a new place and light",
    "Pan-servo tracking to keep the jacket in view",
], size=13, space=4)
chip(s, 10.45, 4.85, 1.95, 1.2, "Questions?", fill=MAGENTA, size=18, name="Questions chip")

prs.save(OUT)
print("saved", OUT, "slides:", len(prs.slides))
