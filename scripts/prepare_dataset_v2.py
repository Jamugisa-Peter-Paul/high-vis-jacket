"""v2 fine-tuning set (single class 'safety_jacket').
train: robot session-1 frames OUTSIDE the test block (x2) + original phone photos
       + public human-labelled vests (sampled) + public 'person without vest' negatives (sampled)
val:   HB1204 valid split (public, human-labelled) - used only for early stopping
tests (never trained on): robot frames 230-330 (DINO-labelled), HB1204 test, Vincent test+valid."""
import random
import shutil
from pathlib import Path

from huggingface_hub import snapshot_download

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "data" / "finetune_v2"
S1 = ROOT / "data" / "labelled" / "session1_lab"
V1 = ROOT / "data" / "finetune" / "train"          # contains the re-labelled original photos (orig_*)
TEST_LO, TEST_HI, GAP = 230, 330, 10
N_VEST, N_NEG = 1500, 700
random.seed(42)

PUBLIC = {"ppe_vincent": ("VincentGOURBIN/ppe-detection", {4}, {2}),
          "ppe_hb1204": ("HB1204/PPE_Detection", {10}, {7})}

if OUT.exists():
    shutil.rmtree(OUT)
for sp in ("train", "val"):
    (OUT / sp / "images").mkdir(parents=True)
    (OUT / sp / "labels").mkdir(parents=True)


def put(sp, img, rows, name=None):
    name = name or img.stem
    shutil.copy2(img, OUT / sp / "images" / (name + img.suffix))
    with open(OUT / sp / "labels" / (name + ".txt"), "w") as fh:
        fh.writelines(rows)


# 1) robot frames outside the test block (+gap), duplicated to weight the robot domain
n_robot = 0
for img in sorted((S1 / "images").glob("*.jpg")):
    i = int(img.stem.split("_")[-1])
    if TEST_LO - GAP <= i <= TEST_HI + GAP:
        continue
    rows = open(S1 / "labels" / (img.stem + ".txt")).readlines()
    put("train", img, rows)
    put("train", img, rows, img.stem + "_dup")
    n_robot += 1

# 2) original phone photos
n_orig = 0
for img in sorted((V1 / "images").glob("orig_*.jpg")):
    put("train", img, open(V1 / "labels" / (img.stem + ".txt")).readlines())
    n_orig += 1

# 3) public train splits -> vests and negatives
vests, negs = [], []
for name, (repo, vest, novest) in PUBLIC.items():
    raw = ROOT / "data" / "public_raw" / name
    snapshot_download(repo_id=repo, repo_type="dataset", local_dir=str(raw), allow_patterns=["train/*", "valid/*"])
    for img in (raw / "train" / "images").glob("*"):
        lbl = raw / "train" / "labels" / (img.stem + ".txt")
        rows = [l.split() for l in open(lbl)] if lbl.exists() else []
        keep = ["0 " + " ".join(r[1:5]) + "\n" for r in rows if len(r) == 5 and int(r[0]) in vest]
        if keep:
            vests.append((img, keep))
        elif any(r and int(r[0]) in novest for r in rows):
            negs.append((img, []))
    if name == "ppe_hb1204":                              # validation split for early stopping
        for img in (raw / "valid" / "images").glob("*"):
            lbl = raw / "valid" / "labels" / (img.stem + ".txt")
            rows = [l.split() for l in open(lbl)] if lbl.exists() else []
            keep = ["0 " + " ".join(r[1:5]) + "\n" for r in rows if len(r) == 5 and int(r[0]) in vest]
            if keep or any(r and int(r[0]) in novest for r in rows):
                put("val", img, keep)
random.shuffle(vests)
random.shuffle(negs)
for img, rows in vests[:N_VEST] + negs[:N_NEG]:
    put("train", img, rows)

(OUT / "data.yaml").write_text(f"path: {OUT.as_posix()}\ntrain: train/images\nval: val/images\nnames:\n  0: safety_jacket\n")
nval = len(list((OUT / "val" / "images").glob("*")))
print(f"train: robot {n_robot}x2, original {n_orig}, public vests {min(N_VEST, len(vests))}/{len(vests)}, "
      f"public negatives {min(N_NEG, len(negs))}/{len(negs)} | val (HB1204 valid): {nval}")
