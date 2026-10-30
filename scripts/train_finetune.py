"""Before/after: validate the original model, then fine-tune it on robot-camera frames at the deployment size (320)."""
import json
from pathlib import Path

from ultralytics import YOLO

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data" / "finetune" / "data.yaml"
ORIG = ROOT / "models" / "original_best_jacket.pt"
RES = ROOT / "results"
RES.mkdir(exist_ok=True)


def summarise(m):
    return {"precision": round(float(m.box.mp), 4), "recall": round(float(m.box.mr), 4),
            "mAP50": round(float(m.box.map50), 4), "mAP50_95": round(float(m.box.map), 4)}


def main():
    before = YOLO(str(ORIG)).val(data=str(DATA), imgsz=320, single_cls=True, batch=16, plots=False,
                                 project=str(RES / "runs"), name="val_original", exist_ok=True, verbose=False)
    print("ORIGINAL model on robot val:", summarise(before))

    model = YOLO(str(ORIG))
    model.train(data=str(DATA), imgsz=320, epochs=80, patience=20, batch=32, device=0, seed=42,
                lr0=0.002, optimizer="AdamW", cos_lr=True, warmup_epochs=2, close_mosaic=10,
                hsv_h=0.01, hsv_s=0.5, hsv_v=0.4, degrees=5, fliplr=0.5, scale=0.5, mosaic=1.0,
                project=str(RES / "runs"), name="finetune_v1", exist_ok=True, verbose=False)

    best = RES / "runs" / "finetune_v1" / "weights" / "best.pt"
    after = YOLO(str(best)).val(data=str(DATA), imgsz=320, batch=16, plots=True,
                                project=str(RES / "runs"), name="val_finetuned", exist_ok=True, verbose=False)
    print("FINE-TUNED model on robot val:", summarise(after))
    json.dump({"original": summarise(before), "finetuned": summarise(after)}, open(RES / "before_after_val.json", "w"), indent=1)
    (ROOT / "models").mkdir(exist_ok=True)
    import shutil
    shutil.copy2(best, ROOT / "models" / "jacket_finetuned_v1.pt")
    print("saved models/jacket_finetuned_v1.pt")


if __name__ == "__main__":
    main()
