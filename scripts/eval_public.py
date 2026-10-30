"""Original vs fine-tuned model on independent, human-labelled public test sets."""
import json
from pathlib import Path

from ultralytics import YOLO

ROOT = Path(__file__).resolve().parents[1]
MODELS = {"original": ROOT / "models" / "original_best_jacket.pt", "finetuned_v1": ROOT / "models" / "jacket_finetuned_v1.pt"}
SETS = ["ppe_hb1204", "ppe_vincent"]


def false_alarm_rate(model, d, imgsz):
    """Share of negative images (people WITHOUT vests, no vest labels) where the model still reports a jacket."""
    neg = [p for p in (d / "images").glob("*") if not (d / "labels" / (p.stem + ".txt")).read_text().strip()]
    hits = sum(len(model.predict(str(p), imgsz=imgsz, conf=0.25, verbose=False)[0].boxes) > 0 for p in neg)
    return hits / max(1, len(neg)), len(neg)


def main():
    out = {}
    for s in SETS:
        d = ROOT / "data" / "public_test" / s
        for imgsz in (320, 640):
            for name, path in MODELS.items():
                m = YOLO(str(path))
                r = m.val(data=str(d / "data.yaml"), split="val", imgsz=imgsz, single_cls=True, batch=16,
                          plots=False, verbose=False, project=str(ROOT / "results" / "runs"), name=f"pub_{s}_{name}_{imgsz}", exist_ok=True)
                far, nneg = false_alarm_rate(m, d, imgsz)
                row = {"precision": round(float(r.box.mp), 3), "recall": round(float(r.box.mr), 3),
                       "mAP50": round(float(r.box.map50), 3), "mAP50_95": round(float(r.box.map), 3),
                       "false_alarm_on_no_vest_images": round(far, 3), "n_negatives": nneg}
                out[f"{s}|{imgsz}|{name}"] = row
                print(f"{s:12s} {imgsz}  {name:13s} {row}")
    json.dump(out, open(ROOT / "results" / "public_test_eval.json", "w"), indent=1)


if __name__ == "__main__":
    main()
