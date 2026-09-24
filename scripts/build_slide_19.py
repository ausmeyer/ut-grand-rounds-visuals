#!/usr/bin/env python3
"""Build Texas horizon views from saved no-covariate forecasts, without fitting."""

import argparse
import csv
from datetime import date, timedelta
import hashlib
import json
import math
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data" / "slide-19"
MODEL = "distributional_gaussian_nll_joint_base_spatial_no_donors"
QUANTILES = {0.05: "q05", 0.25: "q25", 0.5: "median", 0.75: "q75", 0.95: "q95"}
WASTEWATER_MODEL = "distributional_gaussian_nll_joint_base_no_donors_wastewaterscan_lags124"
WASTEWATER_COLUMNS = ["wastewaterscan_flu_a_log10_pmmov" + suffix for suffix in ["", "_lag1", "_lag2", "_lag4"]]


def validate_model(model, model_id):
    if model["model_id"] != model_id or model["feature_recipe"]["spatial_mode"] != "none":
        raise ValueError("Wrong forecast model")
    external = model.get("external_covariates", {})
    if model_id == MODEL:
        if external:
            raise ValueError("Expected no external covariates")
    elif model_id == WASTEWATER_MODEL:
        if external.get("columns") != WASTEWATER_COLUMNS:
            raise ValueError("Expected only the wastewater level and lag block")
    else:
        raise ValueError("Unsupported presentation model")


def sha256(path):
    with path.open("rb") as stream:
        return hashlib.file_digest(stream, "sha256").hexdigest()


def rows(path):
    with path.open(newline="", encoding="utf-8-sig") as stream:
        yield from csv.DictReader(stream)


def write_json(path, value):
    path.write_text(json.dumps(value, indent=2, ensure_ascii=False, allow_nan=False) + "\n")


def import_sources(source_root, data_dir=DATA, model_id=MODEL):
    config_path = source_root / "configs/study_config.json"
    config = json.loads(config_path.read_text())
    recipe = next(row for row in config["corrected_nll_ablation_recipes"] if row["model_id"] == model_id)
    model_config = {**config["corrected_nll_ablation_defaults"], **recipe}
    validate_model(model_config, model_id)
    forecast_file = f"outputs/checkpoint_{model_id}_conditional_gaussian_log_sigma_v2.csv"
    start, end = config["evaluation_period"]["start"], config["evaluation_period"]["end"]
    truth = [row for row in rows(source_root / config["data_file"])
             if row["location_name"] == "Texas" and start <= row["date"] <= end]
    available = {row["date"] for row in truth}
    forecasts = [row for row in rows(source_root / forecast_file)
                 if row["model_id"] == model_id and row["location"] == "48"
                 and row["target_end_date"] in available
                 and float(row["output_type_id"]) in QUANTILES]
    references = {row["reference_date"] for row in forecasts}
    origins = [row for row in rows(source_root / "outputs/asof_anchor_audit.csv")
               if row["reference_date"] in references]
    if not truth or not forecasts or {row["reference_date"] for row in origins} != references:
        raise ValueError("Missing Texas forecasts, observations, or origin audit rows")
    location = next(row for row in rows(source_root / config["location_file"]) if row["location_name"] == "Texas")
    if location["location"] != "48":
        raise ValueError("Unexpected Texas location code")
    data_dir.mkdir(parents=True, exist_ok=True)
    manifest = []
    for kind, original, selected in [
        ("forecast", forecast_file, forecasts),
        ("truth", config["data_file"], truth),
        ("origins", "outputs/asof_anchor_audit.csv", origins),
    ]:
        snapshot = data_dir / f"{kind}-source.csv"
        with snapshot.open("w", newline="") as stream:
            writer = csv.DictWriter(stream, fieldnames=list(selected[0]), lineterminator="\n")
            writer.writeheader()
            writer.writerows(selected)
        manifest.append({"kind": kind, "source_path": original,
                         "source_sha256": sha256(source_root / original),
                         "snapshot": snapshot.name, "snapshot_sha256": sha256(snapshot), "rows": len(selected)})
    write_json(data_dir / "sources.json", {
        "source_project": "joint_twostage_distribution_study", "files": manifest,
        "config_sha256": sha256(config_path), "model_config": model_config,
        "runtime": {**config["runtime"], **model_config.get("runtime_overrides", {})},
        "evaluation_period": config["evaluation_period"], "as_of_data": config["as_of_data"],
        "location": location, "production_lineup": config["production_model_lineup"],
    })


def chart_data(data_dir=DATA, model_id=MODEL, slide=19, model_label="MIGHTE-Base without additional covariates"):
    provenance = json.loads((data_dir / "sources.json").read_text())
    sources = {}
    for source in provenance["files"]:
        path = data_dir / source["snapshot"]
        if sha256(path) != source["snapshot_sha256"]:
            raise ValueError(f"Source snapshot changed: {path.name}")
        sources[source["kind"]] = list(rows(path))
        if len(sources[source["kind"]]) != source["rows"]:
            raise ValueError("Source row count changed")
    model = provenance["model_config"]
    validate_model(model, model_id)
    observed = []
    for row in sources["truth"]:
        value = float(row["total_hosp"])
        if row["location_name"] != "Texas" or not math.isfinite(value) or value < 0:
            raise ValueError("Invalid Texas truth row")
        observed.append({"date": row["date"], "value": value})
    observed.sort(key=lambda point: point["date"])
    if any((date.fromisoformat(b["date"]) - date.fromisoformat(a["date"])).days != 7
           for a, b in zip(observed, observed[1:])):
        raise ValueError("Expected unique weekly observations")
    truth_dates = {point["date"] for point in observed}
    origin_dates = {}
    for row in sources["origins"]:
        if row["has_exact_vintage"] != "True":
            raise ValueError("Forecast origin lacks an exact archived vintage")
        anchor, reference = date.fromisoformat(row["anchor_date"]), date.fromisoformat(row["reference_date"])
        if (reference - anchor).days != 7:
            raise ValueError("Unexpected reference-date convention")
        origin_dates[row["reference_date"]] = row["anchor_date"]
    grouped = {}
    for row in sources["forecast"]:
        horizon, quantile, value = int(row["horizon"]), float(row["output_type_id"]), float(row["value"])
        target, reference = date.fromisoformat(row["target_end_date"]), date.fromisoformat(row["reference_date"])
        if (row["model_id"] != model_id or row["location"] != "48" or row["target"] != "wk inc flu hosp"
                or row["output_type"] != "quantile" or horizon not in range(4) or quantile not in QUANTILES
                or not math.isfinite(value) or value < 0 or target != reference + timedelta(weeks=horizon)
                or row["target_end_date"] not in truth_dates or row["reference_date"] not in origin_dates):
            raise ValueError("Invalid forecast row or target-week alignment")
        key = (horizon, row["target_end_date"])
        point = grouped.setdefault(key, {"date": row["target_end_date"], "reference_date": row["reference_date"],
                                         "data_cutoff": origin_dates[row["reference_date"]]})
        field = QUANTILES[quantile]
        if field in point:
            raise ValueError("Duplicate forecast quantile")
        point[field] = value
    series = []
    for horizon in range(4):
        points = [point for (h, stamp), point in sorted(grouped.items()) if h == horizon]
        if not points:
            raise ValueError("Missing forecast horizon")
        for point in points:
            if not set(QUANTILES.values()) <= point.keys():
                raise ValueError("Incomplete forecast interval")
            values = [point[field] for field in QUANTILES.values()]
            if values != sorted(values):
                raise ValueError("Crossed forecast quantiles")
        series.append({"horizon": horizon, "points": points})
    maximum = max([point["value"] for point in observed] + [point["q95"] for group in series for point in group["points"]])
    return {"slide": slide, "location": "Texas", "model_id": model_id,
            "model_label": model_label, "season_bags": provenance["runtime"]["num_bags"],
            "start": observed[0]["date"], "end": observed[-1]["date"],
            # Match the axes on the hospitalization-only and wastewater-lag slides.
            "axis_max": max(12000, math.ceil(maximum / 2000) * 2000), "tick_step": 2000,
            "horizon_convention": "target_end_date = reference_date + 7 * horizon days; data cutoff is reference_date minus 7 days",
            "intervals": {"50": [0.25, 0.75], "90": [0.05, 0.95]}, "observed": observed, "series": series}


def render(data):
    template = (ROOT / "src" / "slide-19.template.html").read_text()
    if template.count("/*__SLIDE_DATA__*/") != 1:
        raise ValueError("Expected one data marker")
    return template.replace("/*__SLIDE_DATA__*/", json.dumps(data, separators=(",", ":"), ensure_ascii=False, allow_nan=False))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source-root", type=Path, help="Refresh the selected source snapshots from this study checkout")
    args = parser.parse_args()
    if args.source_root:
        import_sources(args.source_root)
    data = chart_data()
    write_json(DATA / "slide-19.json", data)
    (ROOT / "docs" / "slide-19.html").write_text(render(data))
    print(f"Built Slide 19: Texas, {data['start']} to {data['end']}; forecasts per horizon: "
          + ", ".join(str(len(group["points"])) for group in data["series"]))


if __name__ == "__main__":
    main()
