#!/usr/bin/env python3
"""Freeze protection-curve means from saved draws; never fit or rerun a model."""

import argparse
import csv
import hashlib
import json
import math
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
MODELS = [
    ("gam_primary", "outputs/primary/tables", "Primary", "#0a6670", 47),
    ("gam_spencer_ferdinands_fast_waning", "outputs/sensitivity/gam_spencer_ferdinands_fast_waning/tables", "Alternative", "#788995", 46),
    ("gam_spencer_slow_waning", "outputs/sensitivity/gam_spencer_slow_waning/tables", "Sustained protection", "#933a4b", 40),
]


def protection(t, initial, beta, lag, model):
    elapsed = t - lag
    if elapsed < 0:
        return 0.0
    if model == "exponential_effect_ratio":
        value = 1 - (1 - initial) * math.exp(beta * elapsed / 4)
    else:
        u = elapsed / 2
        a, b, c = (1.37, .18, .03) if model == "spencer_fast_relative_ve" else (.50, .05, .01)
        retention = max(0, min(1, (55 - a*u + b*u*u - c*u*u*u) / 55))
        value = initial * retention
    return max(0, min(1, value))


def extract(source):
    summary_path = "outputs/sensitivity/summary/tables/robustness_suite_us_summary.csv"
    summary = list(csv.DictReader((source / summary_path).open()))
    paths = [summary_path, "R/decision_engine.R", "R/protection_models.R",
             "manuscript/overleaf_repo/manuscript.tex"]
    times = [day / 7 for day in range(197)]
    curves = []
    for analysis, folder, label, color, expected in MODELS:
        draw_path = f"{folder}/{analysis}_ve_waning_draws.csv"
        manifest_path = f"{folder}/{analysis}_analysis_manifest.json"
        paths.extend([draw_path, manifest_path])
        draws = list(csv.DictReader((source / draw_path).open()))
        manifest = json.loads((source / manifest_path).read_text())
        assert len(draws) == manifest["configuration"]["n_draws"] == 5000
        assert len({r["draw"] for r in draws}) == 5000
        assert {r["age_group"] for r in draws} == {"all"}
        models = {r["protection_model"] for r in draws}
        assert len(models) == 1
        model = models.pop()
        assert model in {"exponential_effect_ratio", "spencer_fast_relative_ve", "spencer_slow_relative_ve"}
        params = [(float(r["initial_ve"]), float(r["beta_wane_per_28d"]) if r["beta_wane_per_28d"] != "NA" else 0,
                   float(r["immune_lag_weeks"])) for r in draws]
        means = [math.fsum(protection(t, *p, model) for p in params) / len(params) for t in times]
        selected = [r for r in summary if r["analysis"] == analysis and r["state"] == "US" and r["age_group"] == "all"]
        assert len(selected) == 1 and int(selected[0]["min_mean_regret_week"]) == expected
        curves.append({"analysis": analysis, "label": label, "color": color,
                       "hypothetical": model == "spencer_slow_relative_ve", "selected_week": expected,
                       "protection_model": model, "mean_protection": means})
    data = {"population": "US, all ages", "n_draws_per_model": 5000,
            "curve_summary": "Mean bounded protection across saved production draws, with each draw's saved response lag and calibrated initial protection",
            "decision_source": "Selected week from the full saved decision analysis, not inferred from the mean protection curve",
            "weeks_after_vaccination": times, "models": curves,
            "source_fingerprints": [{"path": p, "sha256": hashlib.sha256((source / p).read_bytes()).hexdigest()} for p in paths]}
    output = ROOT / "data/slide-28/inputs.json"
    output.parent.mkdir(exist_ok=True)
    output.write_text(json.dumps(data, indent=2) + "\n")
    print("Frozen three mean protection curves, 5,000 saved draws each; selected weeks 47, 46, 40.")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("manuscript_root", type=Path)
    extract(parser.parse_args().manuscript_root)
