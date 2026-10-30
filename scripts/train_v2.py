"""Fine-tune v2: start from the original jacket model, train on robot + original + public vests + negatives."""
import shutil
from pathlib import Path

from ultralytics import YOLO

ROOT = Path(__file__).resolve().parents[1]


def main():
    model = YOLO(str(ROOT / "models" / "original_best_jacket.pt"))
    model.train(data=str(ROOT / "data" / "finetune_v2" / "data.yaml"), imgsz=320, epochs=80, patience=20,
                batch=32, device=0, seed=42, workers=4, lr0=0.002, optimizer="AdamW", cos_lr=True,
                warmup_epochs=2, close_mosaic=10, hsv_h=0.01, hsv_s=0.5, hsv_v=0.4, degrees=5,
                fliplr=0.5, scale=0.5, mosaic=1.0, project=str(ROOT / "results" / "runs"),
                name="finetune_v2", exist_ok=True, verbose=False)
    shutil.copy2(ROOT / "results" / "runs" / "finetune_v2" / "weights" / "best.pt", ROOT / "models" / "jacket_finetuned_v2.pt")
    print("saved models/jacket_finetuned_v2.pt")


if __name__ == "__main__":
    main()
