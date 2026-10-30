"""Score every model on every independent test set at the deployment size (320 px).
Detection metrics + false-alarm rate on images of people WITHOUT a vest + per-frame hit rate on robot frames."""
import json
from pathlib import Path

from ultralytics import YOLO

ROOT = Path(__file__).resolve().parents[1]
MODELS = {"original": "original_best_jacket.pt", "finetuned_v1": "jacket_finetuned_v1.pt", "finetuned_v2": "jacket_finetuned_v2.pt"}
TESTS = {"robot_hard_block": ROOT / "data" / "robot_test" / "session1_mid",
         "public_hb1204": ROOT / "data" / "public_test" / "ppe_hb1204",
         "public_vincent": ROOT / "data" / "public_test" / "ppe_vincent"}
SKIP = {("finetuned_v1", "robot_hard_block")}      # v1 was trained on these frames, so its score would be meaningless
IMGSZ, CONF = 320, 0.25


def per_image(model, d):
    """Fraction of positive images with >=1 detection, and of negative images with >=1 detection (false alarm)."""
    pos = neg = hit_pos = hit_neg = 0
    for p in sorted((d / "images").glob("*")):
        has = bool((d / "labels" / (p.stem + ".txt")).read_text().strip())
        det = len(model.predict(str(p), imgsz=IMGSZ, conf=CONF, verbose=False)[0].boxes) > 0
        pos += has
        neg += not has
        hit_pos += has and det
        hit_neg += (not has) and det
    return hit_pos / max(1, pos), (hit_neg / neg if neg else None), pos, neg


def main():
    out = {}
    for mname, mfile in MODELS.items():
        path = ROOT / "models" / mfile
        if not path.exists():
            continue
        for tname, d in TESTS.items():
            if (mname, tname) in SKIP:
                continue
            m = YOLO(str(path))
            r = m.val(data=str(d / "data.yaml"), split="val", imgsz=IMGSZ, single_cls=True, batch=16, conf=0.001,
                      plots=False, verbose=False, project=str(ROOT / "results" / "runs"), name=f"eval_{mname}_{tname}", exist_ok=True)
            found, false_alarm, npos, nneg = per_image(m, d)
            row = {"precision": round(float(r.box.mp), 3), "recall": round(float(r.box.mr), 3),
                   "mAP50": round(float(r.box.map50), 3), "mAP50_95": round(float(r.box.map), 3),
                   "frames_found": round(found, 3), "false_alarm_rate": None if false_alarm is None else round(false_alarm, 3),
                   "n_pos": npos, "n_neg": nneg}
            out[f"{mname}|{tname}"] = row
            print(f"{mname:13s} {tname:17s} {row}")
    json.dump(out, open(ROOT / "results" / "evaluation_320.json", "w"), indent=1)


if __name__ == "__main__":
    main()
