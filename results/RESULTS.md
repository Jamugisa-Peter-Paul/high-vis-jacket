# Safety-jacket detector: fine-tuning results

All scores at the deployment input size (320 px), confidence 0.25 for frame-level rates.
Raw numbers: `evaluation_320.json`. Scripts: `scripts/`.

## Test sets (none used for training)

| Test set | Images | Labels made by | What it measures |
|---|---|---|---|
| Robot hard block | 99 robot-camera frames (94 with jacket, 5 without) | Grounding DINO + human check, **independent of all YOLO models** | the real deployment view: walking, side/back views, people half hidden by chairs |
| Public HB1204 test | 242 photos (186 with vests, 56 people without) | humans (Roboflow, CC BY 4.0) | generalisation to other vests, people and places; false alarms |
| Public Vincent test+valid | 208 photos (112 with vests, 96 people without) | humans (Roboflow, CC BY 4.0); some vests unlabelled | second generalisation check |

## Results

| Model | Test set | Precision | Recall | mAP50 | mAP50-95 | Frames where jacket found | False alarms on no-vest images |
|---|---|---|---|---|---|---|---|
| Original | Robot hard block | 0.798 | 0.777 | 0.824 | 0.535 | 69.1% | 0% (5 images) |
| **Fine-tuned v2** | Robot hard block | **0.894** | **0.851** | **0.925** | **0.713** | **97.9%** | 0% (5 images) |
| Original | HB1204 | 0.291 | 0.193 | 0.128 | 0.054 | 38.2% | 16.1% |
| Fine-tuned v1 | HB1204 | 0.320 | 0.159 | 0.118 | 0.058 | 48.4% | 30.4% |
| **Fine-tuned v2** | HB1204 | **0.864** | **0.738** | **0.811** | **0.483** | **96.8%** | 16.1% |
| Original | Vincent | 0.501 | 0.345 | 0.332 | 0.154 | 57.1% | 21.9% |
| Fine-tuned v1 | Vincent | 0.509 | 0.325 | 0.315 | 0.149 | 74.1% | 33.3% |
| **Fine-tuned v2** | Vincent | **0.878** | **0.782** | **0.874** | **0.477** | **92.0%** | **14.6%** |

(v1 is not scored on the robot block because it was trained on those frames.)

## What was done

- **Original model:** YOLOv8n, 2 classes, trained on 301 eye-level phone photos of one jacket.
- **v1:** fine-tuned on robot-camera frames only, with no frames without a jacket. False alarms doubled, a lesson in why negatives matter.
- **v2:** fine-tuned from the original on 3,140 images: 328 robot frames (×2), 284 original photos, 1,500 human-labelled public vest photos, 700 photos of people without vests. One merged class (`safety_jacket`), 320 px, AdamW, cosine learning rate, early stopping (best epoch 56 of 76, 31 min on an RTX 4050).

## Honest limitations

- The robot test frames come from the same room, person and day as the robot training frames (a different time block). A test session recorded in a new place is still needed.
- The robot test has only 5 frames without a jacket, so its 0% false-alarm figure is weak evidence. The public sets give the stronger false-alarm numbers.
- Fine-tuned v2 still raises a false alarm on about 15% of photos of people without vests (mostly orange/yellow clothing or equipment). For the follower, combine with a confidence threshold and require detection over several consecutive frames.
