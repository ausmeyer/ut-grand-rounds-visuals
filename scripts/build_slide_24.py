#!/usr/bin/env python3
"""Build slide 24 from a saved national season and fixed primary-model inputs."""

import json
import math
from datetime import date, timedelta
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data" / "slide-24"


def build():
    inputs = json.loads((DATA / "inputs.json").read_text())
    weeks = inputs["weeks"]
    params = inputs["parameters"]
    total = sum(w["burden"] for w in weeks)
    baseline = [w["burden"] / total for w in weeks]
    candidates = []
    for j, week in enumerate(weeks[:29]):
        protection = []
        for i in range(len(weeks)):
            elapsed = i - j - params["immune_lag_weeks"]
            q = 0 if elapsed < 0 else 1 - (1 - params["initial_ve"]) * math.exp(
                params["beta_wane_per_28d"] * elapsed / 4)
            protection.append(min(1, max(0, q)))
        residual = [b * (1 - q) for b, q in zip(baseline, protection)]
        start = date.fromisoformat(week["date"])
        end = start + timedelta(days=6)
        label = (f"{start:%b} {start.day}–{end.day}" if start.month == end.month
                 else f"{start:%b} {start.day} – {end:%b} {end.day}")
        candidates.append({"index": j, "week": week["week"], "date_label": label,
                           "protection": protection, "residual": residual,
                           "remaining": sum(residual)})
    best = min(range(len(candidates)), key=lambda j: candidates[j]["remaining"])
    assert len(weeks) == 39 and [w["week"] for w in weeks] == list(range(36, 53)) + list(range(1, 23))
    assert abs(sum(baseline) - 1) < 1e-12
    data = {"slide": 24, "season": inputs["season"], "parameters": params,
            "weeks": weeks, "baseline": baseline, "candidates": candidates,
            "best_index": best, "early_index": 2, "late_index": 22}
    (DATA / "slide-24.json").write_text(json.dumps(data, indent=2) + "\n")
    source = (ROOT / "src" / "slide-24.html").read_text()
    assert source.count("/*__SLIDE_DATA__*/") == 1
    html = source.replace("/*__SLIDE_DATA__*/", json.dumps(data, separators=(",", ":")))
    (ROOT / "docs" / "slide-24.html").write_text(html)
    print(f"Built slide 24: 2017/18, 29 candidate dates, example minimum week {candidates[best]['week']}.")


if __name__ == "__main__":
    build()
