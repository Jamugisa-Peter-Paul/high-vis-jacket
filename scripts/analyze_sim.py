"""Turn the Gazebo scenario CSVs (results/sim/<run>/run.csv, written by metrics_node) into metrics + plots.

  py -3 scripts/analyze_sim.py            -> results/sim/<run>/analysis.png, results/sim/SUMMARY.md, summary.json

Metrics (ground truth = Gazebo odometry of robot and worker):
  following ratio  : share of time (after first lock-on) in FOLLOW/TOO_CLOSE
  wrong-target time: time in FOLLOW while the real worker is outside the camera's field of view
                     (so the robot must be following something else)
  gap              : true centre-to-centre distance robot->worker while the worker walks
  min distance     : closest approach (safety; stop distance is 0.8 m)
  speed matching   : mean robot speed for each worker walking speed
  ends on worker   : in the last 10 s, following with the real worker in view >50% of the time
  losses           : FOLLOW -> HOLD events, longest time without a confirmed target, recovered or not
  distance estimate: bias / spread of (true distance - estimated distance) while following
"""
import json
import math
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1] / "results" / "sim"
RUNS = {
    "s1_normal": "S1 normal walk + two 90° turns",
    "s2_speed": "S2 speed changes (0.15 → 0.35 → 0.60 m/s)",
    "s3_challenge": "S3 occlusion + sprint + orange distractor",
    "s3_challenge_no_hysteresis": "S3 ablation: no acquisition hysteresis",
}
HALF_FOV = 1.55 / 2
TRACK = ("FOLLOW", "TOO_CLOSE")
COLORS = {"FOLLOW": "#2a9d4b", "TOO_CLOSE": "#e9a23b", "HOLD": "#f2d14b", "CONFIRMING": "#7fb3e6",
          "SEARCH": "#d9534f", "E_STOP": "#555555"}


def wrap(a):
    return (a + math.pi) % (2 * math.pi) - math.pi


def analyse(name):
    df = pd.read_csv(ROOT / name / "run.csv").dropna(subset=["state"])
    df = df[df.state.str.len() > 0].reset_index(drop=True)
    dt = df.t.diff().fillna(0).clip(upper=0.5)
    bearing = np.arctan2(df.worker_y - df.robot_y, df.worker_x - df.robot_x)
    df["worker_off"] = [abs(wrap(b - y)) for b, y in zip(bearing, df.robot_yaw)]
    first = df.index[df.state.isin(TRACK)].min()
    after = df.loc[first:]
    walking = df[(df.worker_speed > 0.05) & df.state.isin(TRACK)]
    m = {"run": name, "duration_s": round(df.t.iloc[-1], 1)}
    m["state_share_%"] = {s: round(100 * dt[after.index][after.state == s].sum() / dt[after.index].sum(), 1)
                          for s in COLORS if (after.state == s).any()}
    m["following_ratio_%"] = round(100 * dt[after.index][after.state.isin(TRACK)].sum() / dt[after.index].sum(), 1)
    wrong = df.state.isin(TRACK) & (df.worker_off > HALF_FOV)
    m["wrong_target_s"] = round(dt[wrong].sum(), 1)
    m["gap_walking_mean_m"] = round(walking.distance.mean(), 2)
    m["gap_walking_std_m"] = round(walking.distance.std(), 2)
    m["min_distance_m"] = round(df.loc[first:, "distance"].min(), 2)
    m["final_distance_m"] = round(df.distance.iloc[-1], 2)
    m["final_state"] = df.state.iloc[-1]
    last = df[df.t > df.t.iloc[-1] - 10]                     # last 10 s: following the real worker most of the time?
    m["ends_on_worker"] = bool((last.state.isin(TRACK) & (last.worker_off < HALF_FOV)).mean() > 0.5)
    # speed matching: robot speed for each commanded worker speed (only while following a walking worker)
    lv = walking.assign(level=walking.worker_speed.round(2))
    m["speed_match"] = {f"{k:.2f}": round(g.robot_speed.mean(), 3) for k, g in lv.groupby("level") if len(g) > 15}
    # losses: runs of non-tracking states after first lock-on
    tracking = after.state.isin(TRACK).to_numpy()
    t = after.t.to_numpy()
    gaps, start = [], None
    for i, tr in enumerate(tracking):
        if not tr and start is None:
            start = t[i]
        if tr and start is not None:
            gaps.append(t[i] - start)
            start = None
    m["losses"] = len(gaps) + (start is not None)
    m["longest_loss_s"] = round(max(gaps + ([t[-1] - start] if start is not None else []), default=0.0), 1)
    m["recovered_all"] = start is None
    est = df[df.state.isin(TRACK) & df.est_distance.notna()]
    err = est.distance - est.est_distance
    m["est_bias_m"], m["est_std_m"] = round(err.mean(), 2), round(err.std(), 2)
    m["inference_ms_mean"] = round(df.infer_ms.mean(), 1)
    plot(df, name, m)
    return m


def plot(df, name, m):
    fig, ax = plt.subplots(1, 3, figsize=(16, 4.6), gridspec_kw={"width_ratios": [1.1, 1.5, 1.5]})
    a = ax[0]
    a.plot(df.worker_x, df.worker_y, color="#c9b400", lw=3, label="worker (vest)")
    for s, g in df.groupby("state"):
        a.scatter(g.robot_x, g.robot_y, s=5, color=COLORS.get(s, "k"), label=f"robot: {s}")
    a.plot(df.robot_x.iloc[0], df.robot_y.iloc[0], "ks", ms=7)
    a.set_aspect("equal", adjustable="datalim"), a.set_xlabel("x (m)"), a.set_ylabel("y (m)"), a.set_title("Top view (ground truth)")
    a.legend(fontsize=7, loc="best"), a.grid(alpha=0.3)

    def shade(a):
        prev, t0 = None, df.t.iloc[0]
        for t, s in zip(df.t, df.state):
            if s != prev:
                if prev is not None:
                    a.axvspan(t0, t, color=COLORS.get(prev, "w"), alpha=0.15, lw=0)
                prev, t0 = s, t
        a.axvspan(t0, df.t.iloc[-1], color=COLORS.get(prev, "w"), alpha=0.15, lw=0)

    a = ax[1]
    shade(a)
    a.plot(df.t, df.distance, "k", lw=1.8, label="true distance (centre-centre)")
    a.plot(df.t, df.est_distance, color="#1f77b4", lw=1.2, label="robot's estimate (camera-vest)")
    a.axhline(1.5, ls="--", color="#2a9d4b", lw=1, label="target gap 1.5 m")
    a.axhline(0.8, ls=":", color="#d9534f", lw=1, label="stop distance 0.8 m")
    a.set_xlabel("sim time (s)"), a.set_ylabel("m"), a.set_title("Distance (background = follower state)")
    a.legend(fontsize=7), a.grid(alpha=0.3)
    a = ax[2]
    shade(a)
    a.plot(df.t, df.worker_speed, color="#c9b400", lw=2, label="worker speed")
    a.plot(df.t, df.robot_speed, "k", lw=1.2, label="robot speed")
    a.axhline(0.35, ls=":", color="grey", lw=1, label="robot speed cap 0.35")
    a.set_xlabel("sim time (s)"), a.set_ylabel("m/s"), a.set_title("Speed matching")
    a.legend(fontsize=7), a.grid(alpha=0.3)
    fig.suptitle(f"{RUNS[name]}  |  following {m['following_ratio_%']}%  ·  min dist {m['min_distance_m']} m  ·  "
                 f"wrong-target {m['wrong_target_s']} s  ·  ends on worker: {'yes' if m['ends_on_worker'] else 'NO'}",
                 fontsize=11)
    fig.tight_layout()
    fig.savefig(ROOT / name / "analysis.png", dpi=110)
    plt.close(fig)


rows = [analyse(n) for n in RUNS if (ROOT / n / "run.csv").exists()]
(ROOT / "summary.json").write_text(json.dumps(rows, indent=1), encoding="utf-8")
cols = [("Run", lambda m: RUNS[m["run"]]), ("Following %", "following_ratio_%"), ("Wrong-target s", "wrong_target_s"),
        ("Gap walking (m)", lambda m: f"{m['gap_walking_mean_m']} ± {m['gap_walking_std_m']}"),
        ("Min dist (m)", "min_distance_m"), ("Losses", "losses"), ("Longest loss (s)", "longest_loss_s"),
        ("Final", lambda m: f"{m['final_state']} @ {m['final_distance_m']} m"),
        ("Ends following the worker", lambda m: "yes" if m["ends_on_worker"] else "**no**"),
        ("Speed match worker→robot (m/s)", lambda m: ", ".join(f"{k}→{v:.2f}" for k, v in m["speed_match"].items())),
        ("Est. bias ± sd (m)", lambda m: f"{m['est_bias_m']} ± {m['est_std_m']}"), ("Infer ms", "inference_ms_mean")]
lines = ["| " + " | ".join(c for c, _ in cols) + " |", "|" + "---|" * len(cols)]
for m in rows:
    lines.append("| " + " | ".join(str(f(m) if callable(f) else m[f]) for _, f in cols) + " |")
(ROOT / "SUMMARY.md").write_text("# Gazebo scenario results\n\n" + "\n".join(lines) + "\n", encoding="utf-8")
print("\n".join(lines))
