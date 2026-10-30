"""Download human-labelled PPE datasets (CC BY 4.0) from Hugging Face and convert them to a
single-class 'safety_jacket' test set. Images whose only labels are 'no vest' people are kept as negatives."""
from pathlib import Path
import shutil

from huggingface_hub import snapshot_download

ROOT = Path(__file__).resolve().parents[1]
SOURCES = {
    # name: (repo, vest class ids, no-vest class ids, splits)
    "ppe_vincent": ("VincentGOURBIN/ppe-detection", {4}, {2}, ("test", "valid")),
    "ppe_hb1204": ("HB1204/PPE_Detection", {10}, {7}, ("test",)),
}

for name, (repo, vest, novest, splits) in SOURCES.items():
    raw = ROOT / "data" / "public_raw" / name
    snapshot_download(repo_id=repo, repo_type="dataset", local_dir=str(raw),
                      allow_patterns=[f"{s}/*" for s in splits] + ["data.yaml", "README*"])
    out = ROOT / "data" / "public_test" / name
    if out.exists():
        shutil.rmtree(out)
    (out / "images").mkdir(parents=True)
    (out / "labels").mkdir(parents=True)
    n_pos = n_neg = n_skip = n_boxes = 0
    for sp in splits:
        for img in sorted((raw / sp / "images").glob("*")):
            lbl = raw / sp / "labels" / (img.stem + ".txt")
            rows = [l.split() for l in open(lbl)] if lbl.exists() else []
            keep = [r for r in rows if r and int(r[0]) in vest and len(r) == 5]
            has_novest = any(r and int(r[0]) in novest for r in rows)
            if not keep and not has_novest:
                n_skip += 1          # no person-with/without-vest information: not useful here
                continue
            shutil.copy2(img, out / "images" / img.name)
            with open(out / "labels" / (img.stem + ".txt"), "w") as fh:
                for r in keep:
                    fh.write("0 " + " ".join(r[1:5]) + "\n")
            n_boxes += len(keep)
            n_pos += bool(keep)
            n_neg += not keep
    (out / "data.yaml").write_text(f"path: {out.as_posix()}\ntrain: images\nval: images\nnames:\n  0: safety_jacket\n")
    print(f"{name}: {n_pos} images with vests ({n_boxes} boxes), {n_neg} negatives (people without vests), {n_skip} skipped")
