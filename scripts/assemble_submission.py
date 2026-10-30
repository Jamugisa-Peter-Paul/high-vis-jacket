"""Build the single final-project submission folder from the working project.

  py -3.13 scripts/assemble_submission.py

Leaves out what the brief does not ask for: the raw dataset (documented instead), Fuel source meshes,
Raspberry Pi wheel files, test snapshots and build files.
"""
import shutil
from pathlib import Path

P = Path(__file__).resolve().parents[1]
OUT = P.parent / "Final_Project_Submission_S25M25-008_S25M25-003"
SKIP = shutil.ignore_patterns("__pycache__", "*.pyc", "*.log", "*.aux", "*.fls", "*.out", "*.fdb_latexmk", "build", "install")

README = """FINAL PROJECT SUBMISSION: SAFETY-JACKET FOLLOWER ROBOT
Intelligent Systems and Robotics, Uganda Christian University
Jamugisa Peter Paul (S25M25/008) and Ayebare Moses (S25M25/003)
30 October 2026

WHERE TO FIND EACH DELIVERABLE

Report (PDF, 6 pages)        1_Report/Final_Report.pdf  (LaTeX source in 1_Report/latex_source)
Slides (PowerPoint, 10)      2_Presentation/Final_Presentation_Jacket_Follower.pptx  (videos are inside the file)
User manual (1 page)         3_User_Manual/User_Manual.pdf
Contribution statement       4_Contribution_Statement/Contribution_Statement.pdf
Dataset documentation        5_Dataset_Documentation/Dataset_Documentation.pdf
Source code                  6_Source_Code/jacket_follower  (scripts, ros2_setup, robot)
Model weights                6_Source_Code/jacket_follower/models  (jacket_finetuned_v2.pt is the final model)
ROS 2 package                6_Source_Code/jacket_follower/ros2_ws/src/jacket_follower
Gazebo assets                the same package: worlds/ and models/
Configs                      the same package: config/ and launch/ ; training settings in 6_Source_Code/training_config
Demos and videos             7_Demos_and_Results/real_robot and 7_Demos_and_Results/simulation
Results and logs             7_Demos_and_Results  (detector RESULTS.md, simulation SUMMARY.md, CSV logs, plots)

NOTES

- ROS 2 = Robot Operating System 2.
- The full dataset (about 890 MB) is not included. See the dataset documentation.
- Start with the report, then the user manual to run the system.
"""


def copy(src, dst):
    src, dst = P / src, OUT / dst
    dst.parent.mkdir(parents=True, exist_ok=True)
    if src.is_dir():
        shutil.copytree(src, dst, ignore=SKIP)
    else:
        shutil.copy2(src, dst)


if OUT.exists():
    shutil.rmtree(OUT)
OUT.mkdir()
(OUT / "README.txt").write_text(README, encoding="utf-8")

# documents
copy("report_latex/main.pdf", "1_Report/Final_Report.pdf")
copy("report_latex/main.tex", "1_Report/latex_source/main.tex")
copy("report_latex/UCULOGO.png", "1_Report/latex_source/UCULOGO.png")
copy("report_latex/figures", "1_Report/latex_source/figures")
copy("presentation/Final_Presentation_Jacket_Follower.pptx", "2_Presentation/Final_Presentation_Jacket_Follower.pptx")
copy("docs/user_manual.pdf", "3_User_Manual/User_Manual.pdf")
copy("docs/contribution_statement.pdf", "4_Contribution_Statement/Contribution_Statement.pdf")
copy("docs/dataset_documentation.pdf", "5_Dataset_Documentation/Dataset_Documentation.pdf")

# source code, ROS 2 package, Gazebo assets, weights
C = "6_Source_Code/jacket_follower"
shutil.copytree(P / "ros2_ws", OUT / C / "ros2_ws", ignore=shutil.ignore_patterns("models_src", "__pycache__", "*.pyc", "build", "install", "log"))
copy("ros2_setup", f"{C}/ros2_setup")
copy("scripts", f"{C}/scripts")
copy("models", f"{C}/models")
for f in ("masterpi_server.py", "start_server.sh", "motors_off_at_boot.service"):
    copy(f"robot/{f}", f"{C}/robot/{f}")
(OUT / C / "robot" / "tools").mkdir()
for f in sorted((P / "robot" / "tools").iterdir()):
    if f.is_file() and f.suffix in (".py", ".sh", ".ps1", ".json"):
        shutil.copy2(f, OUT / C / "robot" / "tools" / f.name)
copy("results/runs/finetune_v2/args.yaml", "6_Source_Code/training_config/training_args_v2.yaml")
copy("data/finetune_v2/data.yaml", "6_Source_Code/training_config/data_v2.yaml")

# demos and results
R = "7_Demos_and_Results"
copy("results/RESULTS.md", f"{R}/detector/RESULTS.md")
copy("results/evaluation_320.json", f"{R}/detector/evaluation_320.json")
for f in ("results.png", "confusion_matrix.png", "BoxPR_curve.png"):
    copy(f"results/runs/finetune_v2/{f}", f"{R}/detector/training_{f}")
copy("results/sim/SUMMARY.md", f"{R}/simulation/SUMMARY.md")
copy("results/sim/summary.json", f"{R}/simulation/summary.json")
for run in ("s1_normal", "s2_speed", "s3_challenge", "s3_challenge_no_hysteresis"):
    for f in ("debug.mp4", "analysis.png", "run.csv", "video_sheet.jpg"):
        copy(f"results/sim/{run}/{f}", f"{R}/simulation/{run}/{f}")
for f in ("following.mp4", "search.mp4", "highlights.mp4"):
    copy(f"results/real/{f}", f"{R}/real_robot/{f}")
for run in ("run2", "run5", "run6"):
    for f in ("debug.mp4", "probe.txt", "video_sheet.jpg"):
        if (P / f"results/real/{run}/{f}").exists():
            copy(f"results/real/{run}/{f}", f"{R}/real_robot/{run}/{f}")
for f in ("14.jpg", "15.jpg", "16.jpg"):
    copy(f"results/real/photos/{f}", f"{R}/real_robot/photos/lab_{f}")

size, files = 0, 0
for f in OUT.rglob("*"):
    if f.is_file():
        size += f.stat().st_size
        files += 1
print(f"{OUT}\n{files} files, {size / 1e6:.0f} MB")
for d in sorted(OUT.iterdir()):
    s = sum(f.stat().st_size for f in d.rglob("*") if f.is_file()) if d.is_dir() else d.stat().st_size
    print(f"  {d.name:32s} {s / 1e6:7.1f} MB")
