#!/usr/bin/env python3
"""Build the archived Slide 14 example and the synthetic Slide 15 teaching graphic."""

import argparse
import csv
import gzip
import hashlib
import io
import json
import math
from pathlib import Path
import subprocess
from statistics import NormalDist

from build_forecasting_intro import HUB_SHA, RAW, read_source, write_json

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data" / "forecast-scores"
TRUTH_SHA = "adc3e7d4cd98a53f9233c188fd9024b81fd90f0a"
SOURCES = {
    "baseline": f"{RAW}{HUB_SHA}/model-output/FluSight-baseline/2024-12-14-FluSight-baseline.csv",
    "later-truth": f"{RAW}{TRUTH_SHA}/target-data/target-hospital-admissions.csv",
}
QUANTILES = [.01, .025, .05, .1, .15, .2, .25, .3, .35, .4, .45, .5,
             .55, .6, .65, .7, .75, .8, .85, .9, .95, .975, .99]


def refresh():
    (DATA / "sources").mkdir(parents=True, exist_ok=True)
    manifest = []
    for name, url in SOURCES.items():
        raw = subprocess.check_output(["curl", "-fsSL", "--retry", "3", url])
        (DATA / "sources" / f"{name}.gz").write_bytes(gzip.compress(raw, mtime=0))
        manifest.append({"name": name, "url": url, "sha256": hashlib.sha256(raw).hexdigest()})
        print(f"Fetched {name}: {len(raw):,} bytes")
    write_json(DATA / "sources.json", manifest)


def cached(name):
    return gzip.decompress((DATA / "sources" / f"{name}.gz").read_bytes()).decode()


def forecast(raw):
    rows = [r for r in csv.DictReader(io.StringIO(raw))
            if r["location"] == "48" and r["reference_date"] == "2024-12-14"
            and r["target"] == "wk inc flu hosp" and r["horizon"] == "1"
            and r["target_end_date"] == "2024-12-21" and r["output_type"] == "quantile"]
    points = sorted((float(r["output_type_id"]), float(r["value"])) for r in rows)
    if [q for q, _ in points] != QUANTILES:
        raise ValueError("Missing, duplicated, or unexpected quantiles")
    values = [v for _, v in points]
    if values != sorted(values) or not all(math.isfinite(v) and v >= 0 for v in values):
        raise ValueError("Invalid or crossing quantiles")
    return {str(q): v for q, v in points}


def wis(quantiles, observed):
    """Bracher et al.: 11 central intervals plus the median, on the count scale."""
    total = .5 * abs(observed - quantiles["0.5"])
    for q in QUANTILES[:11]:
        alpha = 2 * q
        lower, upper = quantiles[str(q)], quantiles[str(round(1 - q, 3))]
        interval_score = upper - lower + 2 / alpha * (max(lower - observed, 0) + max(observed - upper, 0))
        total += alpha / 2 * interval_score
    return total / 11.5


def example():
    ensemble, baseline = forecast(read_source("ensemble")), forecast(cached("baseline"))
    truth = [r for r in csv.DictReader(io.StringIO(cached("later-truth")))
             if r["location"] == "48" and r["date"] == "2024-12-21"]
    if len(truth) != 1:
        raise ValueError("Expected exactly one observed Texas count")
    observed = float(truth[0]["value"])
    if not math.isfinite(observed) or observed < 0:
        raise ValueError("Invalid observed count")
    ensemble_wis, baseline_wis = wis(ensemble, observed), wis(baseline, observed)
    if baseline_wis <= 0:
        raise ValueError("Relative WIS requires a positive baseline score")
    return {"location": "Texas", "issue_date": "2024-12-11", "reference_date": "2024-12-14",
            "target_end_date": "2024-12-21", "horizon": 1, "axis_max": 1400,
            "ensemble": ensemble, "baseline": baseline, "observed": observed,
            "truth_vintage": "2025-06-18", "score_scale": "admission counts",
            "scores": {"absolute_error": abs(observed - ensemble["0.5"]),
                       "ensemble_wis": ensemble_wis, "baseline_wis": baseline_wis,
                       "relative_wis": ensemble_wis / baseline_wis}}


def target_example():
    """Illustrative marginal distributions, not fitted or submitted forecasts."""
    normal = NormalDist()
    forecasts = []
    for horizon, (median, spread) in enumerate(zip([470, 520, 550, 570], [.13, .19, .24, .28])):
        quantiles = {str(q): round(median * math.exp(spread * normal.inv_cdf(q)), 3)
                     for q in QUANTILES}
        forecasts.append({"horizon": horizon, "quantiles": quantiles})
    return {"slide": 15, "synthetic": True, "axis_max": 1000,
            "history": [{"week": week, "value": value}
                        for week, value in zip(range(-5, 0), [110, 155, 230, 305, 390])],
            "forecasts": forecasts, "quantile_count": len(QUANTILES),
            "distribution": "Illustrative lognormal marginals; specified medians and log-scale spreads."}


def slide_data(number, full):
    if number == 15:
        return target_example()
    data = dict(full)
    if number == 14:
        for key in ("baseline", "observed", "truth_vintage", "score_scale", "scores"):
            del data[key]
    data["slide"] = number
    return data


def render(data):
    template = "slide-15.template.html" if data["slide"] == 15 else "forecast-distribution.template.html"
    source = (ROOT / "src" / template).read_text()
    if source.count("/*__SLIDE_DATA__*/") != 1:
        raise ValueError("Expected one data marker")
    return source.replace("/*__SLIDE_DATA__*/", json.dumps(data, ensure_ascii=False, separators=(",", ":")))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--refresh", action="store_true")
    args = parser.parse_args()
    if args.refresh:
        refresh()
    full = example()
    for number in (14, 15):
        data = slide_data(number, full)
        write_json(DATA / f"slide-{number}.json", data)
        (ROOT / "docs" / f"slide-{number}.html").write_text(render(data))
    print("Built Slide 14 (archived forecast) and Slide 15 (synthetic targets and scoring example).")


if __name__ == "__main__":
    main()
