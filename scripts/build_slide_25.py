#!/usr/bin/env python3
"""Build standalone slide 25 from the frozen, validated manuscript scenarios."""

import json
import math
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data" / "slide-25"


def week_index(week, max_week):
    return week - 36 if week >= 36 else max_week - 36 + week


def protection(elapsed, params):
    since_response = elapsed - params["immune_lag_weeks"]
    if since_response < 0:
        return 0
    return min(1, max(0, 1 - (1 - params["initial_ve"]) * math.exp(
        params["beta_wane_per_28d"] * since_response / 4)))


def build():
    data = json.loads((DATA / "inputs.json").read_text())
    assert data["n_draws"] == 5000 and len(data["scenarios"]) == 10
    assert data["candidate_weeks"] == list(range(36, 53)) + list(range(1, 13))
    assert len(set(s["draw"] for s in data["scenarios"])) == 10
    max_error = 0
    for s in data["scenarios"]:
        params = s["parameters"]
        s["elapsed_weeks"] = [week_index(w, s["max_week"]) for w in s["weeks"]]
        residuals = []
        for j, week in enumerate(data["candidate_weeks"]):
            vaccination = week_index(week, s["max_week"])
            remaining = [b * (1 - protection(t - vaccination, params))
                         for b, t in zip(s["burden"], s["elapsed_weeks"])]
            assert all(0 <= r <= b for r, b in zip(remaining, s["burden"]))
            max_error = max(max_error, abs(sum(remaining) - s["remaining"][j]))
            residuals.append(remaining)
        if s is data["scenarios"][0]:
            s["residual_by_date"] = residuals
        points = []
        for i in range(145):
            t = i / 4
            if t == params["immune_lag_weeks"]:
                points.append([t, 0])
            points.append([t, protection(t, params)])
        s["protection_points"] = points
    assert max_error < 1e-12
    assert min(range(29), key=data["mean_remaining"].__getitem__) == data["best_index"]
    assert data["candidate_weeks"][data["best_index"]] == 47
    assert all(e < 1e-10 for k, e in data["validation"].items() if k.endswith("error"))
    data["validation"]["displayed_290_totals_max_absolute_error"] = max_error
    data["burden_y_max"] = math.ceil(max(max(s["burden"]) for s in data["scenarios"]) * 100) / 100
    data["decision_y_max"] = math.ceil(max(max(s["remaining"]) for s in data["scenarios"]) * 10) / 10
    (DATA / "slide-25.json").write_text(json.dumps(data, indent=2) + "\n")
    source = (ROOT / "src" / "slide-25.html").read_text()
    assert source.count("/*__SLIDE_DATA__*/") == 1
    html = source.replace("/*__SLIDE_DATA__*/", json.dumps(data, separators=(",", ":")))
    (ROOT / "docs" / "slide-25.html").write_text(html)
    print(f"Built slide 25: 10 examples, 5,000-simulation mean, week 47 minimum; display error {max_error:.3g}.")


if __name__ == "__main__":
    build()
