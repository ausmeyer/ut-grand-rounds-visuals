#!/usr/bin/env python3
"""Build Slides 12–13 offline; --refresh retrieves the pinned public inputs."""

from __future__ import annotations

import argparse
import csv
from concurrent.futures import ThreadPoolExecutor
from datetime import date, timedelta
import gzip
import hashlib
import io
import json
import math
from pathlib import Path
import re
import subprocess


ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data" / "forecasting-intro"
LEGACY_SHA = "c42804d2507ac590b4d900c28143db289f7d5645"
HUB_SHA = "b758798766336111d3ae0151a3bf4aea383d5d6c"
TRUTH_SHA = "47f76990a0cfba1cf226c7bc0087200777e77766"
RAW = "https://raw.githubusercontent.com/cdcepi/FluSight-forecast-hub/"
SOURCES = {
    "legacy-tree": f"https://api.github.com/repos/cdcepi/FluSight-forecast-data/git/trees/{LEGACY_SHA}?recursive=1",
    "hub-tree": f"https://api.github.com/repos/cdcepi/FluSight-forecast-hub/git/trees/{HUB_SHA}?recursive=1",
    "tasks": f"{RAW}{HUB_SHA}/hub-config/tasks.json",
    "hub-readme": f"{RAW}{HUB_SHA}/README.md",
    "forecast-summary": f"{RAW}{HUB_SHA}/weekly-summaries/2024-12-14/2024-12-14_flu_forecasts_data.csv",
    "ensemble": f"{RAW}{HUB_SHA}/model-output/FluSight-ensemble/2024-12-14-FluSight-ensemble.csv",
    "truth-vintage": f"{RAW}{TRUTH_SHA}/target-data/target-hospital-admissions.csv",
}
# Weekly filename/reference dates, not evaluation-target inclusion rules.
# Season boundaries and supporting sources are recorded in the evidence notes.
SEASONS = [
    ("2021–22", "legacy-tree", "2022-01-10", "2022-06-20"),
    ("2022–23", "legacy-tree", "2022-10-17", "2023-05-15"),
    ("2023–24", "hub-tree", "2023-10-07", "2024-05-04"),
    ("2024–25", "hub-tree", "2024-11-23", "2025-05-31"),
    ("2025–26", "hub-tree", "2025-11-22", "2026-05-30"),
]


def write_json(path: Path, value: object) -> None:
    path.write_text(json.dumps(value, indent=2, ensure_ascii=False) + "\n")


def refresh() -> None:
    (DATA / "sources").mkdir(parents=True, exist_ok=True)
    manifest = []
    for name, url in SOURCES.items():
        content = subprocess.check_output(["curl", "--fail", "--silent", "--show-error", "--location", "--retry", "3", url])
        (DATA / "sources" / f"{name}.gz").write_bytes(gzip.compress(content, mtime=0))
        manifest.append({"name": name, "url": url, "sha256": hashlib.sha256(content).hexdigest()})
        print(f"Fetched {name}: {len(content):,} bytes")
    tree = json.loads(read_source("hub-tree"))
    paths = [item["path"] for item in tree["tree"] if item["type"] == "blob"
             and re.fullmatch(r"model-output/[^/]+/2024-12-14-[^/]+\.(csv|parquet)", item["path"])
             and not item["path"].split("/")[1].startswith("FluSight-")]

    def fetch_model(path: str) -> dict:
        name = "model-" + path.split("/")[1]
        url = f"{RAW}{HUB_SHA}/{path}"
        content = subprocess.check_output(["curl", "-fsSL", "--retry", "3", url])
        digest = hashlib.sha256(content).hexdigest()
        if path.endswith(".parquet"):
            # Only refresh needs pyarrow; the offline build reads the CSV snapshot.
            import pyarrow.parquet as pq
            (DATA / "sources" / f"{name}.parquet.gz").write_bytes(gzip.compress(content, mtime=0))
            table = pq.read_table(io.BytesIO(content))
            converted = io.StringIO()
            writer = csv.DictWriter(converted, fieldnames=table.column_names)
            writer.writeheader()
            writer.writerows(table.to_pylist())
            content = converted.getvalue().encode()
        (DATA / "sources" / f"{name}.gz").write_bytes(gzip.compress(content, mtime=0))
        return {"name": name, "url": url, "sha256": digest}

    with ThreadPoolExecutor(max_workers=6) as executor:
        manifest.extend(executor.map(fetch_model, sorted(paths)))
    print(f"Fetched {len(paths)} individual model submissions")
    write_json(DATA / "sources.json", manifest)


def read_source(name: str) -> str:
    return gzip.decompress((DATA / "sources" / f"{name}.gz").read_bytes()).decode()


def weeks_between(start: str, end: str) -> list[str]:
    day, last = date.fromisoformat(start), date.fromisoformat(end)
    weeks = []
    while day <= last:
        weeks.append(day.isoformat())
        day += timedelta(days=7)
    return weeks


def model_weeks(tree: dict, prefix: str, weeks: list[str]) -> dict[str, list[str]]:
    """Count unique archived participant-model weeks, not files or locations."""
    if tree.get("truncated"):
        raise ValueError("Incomplete GitHub tree")
    allowed = set(weeks)
    found: dict[str, set[str]] = {}
    for item in tree["tree"]:
        path = item["path"]
        if item["type"] != "blob" or not path.startswith(prefix + "/"):
            continue
        parts = path.split("/")
        if len(parts) != 3:
            continue
        model, filename = parts[1:]
        if model.lower().startswith("flusight-"):
            continue
        match = re.fullmatch(r"(\d{4}-\d{2}-\d{2})-" + re.escape(model) + r"\.(?:csv|parquet)", filename)
        if match and match[1] in allowed:
            found.setdefault(model, set()).add(match[1])
    return {model: sorted(dates) for model, dates in sorted(found.items())}


def participation() -> dict:
    trees = {name: json.loads(read_source(name)) for name in ("legacy-tree", "hub-tree")}
    tasks = json.loads(read_source("tasks"))
    permitted = set(tasks["rounds"][0]["model_tasks"][0]["task_ids"]["reference_date"]["optional"])
    audit, bars = [], []
    for label, source, start, end in SEASONS:
        weeks = weeks_between(start, end)
        if source == "hub-tree" and not set(weeks) <= permitted:
            raise ValueError(f"Unconfigured round in {label}")
        counts = model_weeks(trees[source], "data-forecasts" if source == "legacy-tree" else "model-output", weeks)
        minimum = math.ceil(len(weeks) / 2)
        models = [{"model": model, "weeks": dates, "count": len(dates), "included": len(dates) >= minimum} for model, dates in counts.items()]
        count = sum(model["included"] for model in models)
        bars.append({"season": label, "models": count, "scheduled_weeks": len(weeks), "minimum_weeks": minimum})
        audit.append({"season": label, "scheduled_weeks": weeks, "minimum_weeks": minimum, "models": models})
    write_json(DATA / "participation-audit.json", audit)
    return {"seasons": bars, "target_season": "2026–27"}


def forecast_example() -> dict:
    summary = list(csv.DictReader(io.StringIO(read_source("forecast-summary"))))
    rows = [row for row in summary if row["abbreviation"] == "TX" and int(row["horizon"]) in range(4)]
    models: dict[str, list[dict]] = {}
    for source in sorted((DATA / "sources").glob("model-*.gz")):
        if source.name.endswith(".parquet.gz"):
            continue
        model = source.name.removeprefix("model-").removesuffix(".gz")
        raw_model = csv.DictReader(io.StringIO(gzip.decompress(source.read_bytes()).decode()))
        points = [{"date": r["target_end_date"], "median": float(r["value"])} for r in raw_model
                  if r["location"] == "48" and r["target"] == "wk inc flu hosp" and r["output_type"] == "quantile"
                  and float(r["output_type_id"]) == .5 and r["horizon"] in ("0", "1", "2", "3")]
        if points:
            models[model] = points
    raw = list(csv.DictReader(io.StringIO(read_source("ensemble"))))
    ensemble_rows = [r for r in raw if r["location"] == "48" and r["target"] == "wk inc flu hosp"
                     and r["output_type"] == "quantile" and r["horizon"] in ("0", "1", "2", "3")]
    direct = {(r["target_end_date"], float(r["output_type_id"])): float(r["value"]) for r in ensemble_rows}
    ensemble = [{"date": day, "lower": direct[(day, .025)], "median": direct[(day, .5)], "upper": direct[(day, .975)]}
                for day in sorted({r["target_end_date"] for r in ensemble_rows})]
    # Independently check all horizons available in the CDC weekly summary.
    for row in rows:
        model = row["model"]
        if model.startswith("FluSight-") and model != "FluSight-ensemble":
            continue
        if row["reference_date"] != "2024-12-14" or row["forecast_due_date"] != "2024-12-11":
            raise ValueError("Unexpected forecast date")
        points = ensemble if model == "FluSight-ensemble" else models[model]
        value = next(p["median"] for p in points if p["date"] == row["target_end_date"])
        if not math.isclose(value, float(row["quantile_0.5"]), rel_tol=1e-8):
            raise ValueError(f"Summary differs from original submission: {model}")
    for model, points in models.items():
        points.sort(key=lambda p: p["date"])
        if len({p["date"] for p in points}) != len(points):
            raise ValueError(f"Duplicated forecast: {model}")
        if not all(math.isfinite(p["median"]) and p["median"] >= 0 for p in points):
            raise ValueError(f"Invalid forecast: {model}")
    for point in ensemble:
        if not 0 <= point["lower"] <= point["median"] <= point["upper"]:
            raise ValueError("Crossing ensemble quantiles")
    truth = list(csv.DictReader(io.StringIO(read_source("truth-vintage"))))
    observed = sorted([{"date": r["date"], "value": float(r["value"])} for r in truth
                       if r["location"] == "48" and r["date"] <= "2024-12-11" and r["value"] not in ("", "NA")], key=lambda p: p["date"])[-10:]
    if len(observed) != 10 or observed[-1]["date"] != "2024-12-07":
        raise ValueError("Unexpected observation vintage")
    return {"location": "Texas", "issue_date": "2024-12-11", "reference_date": "2024-12-14",
            "observed": observed, "models": [{"id": model, "points": points} for model, points in sorted(models.items())],
            "ensemble": ensemble, "season_teams": 33, "season_models": 46}


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--refresh", action="store_true", help="Download pinned inputs before building")
    args = parser.parse_args()
    if args.refresh:
        refresh()
    for number, data in ((12, forecast_example()), (13, {"target_season": "2026–27"})):
        write_json(DATA / f"slide-{number}.json", data)
        template = ROOT / "src" / f"slide-{number}.template.html"
        source = template.read_text()
        if source.count("/*__SLIDE_DATA__*/") != 1:
            raise ValueError(f"Missing or repeated data marker: {template}")
        rendered = source.replace("/*__SLIDE_DATA__*/", json.dumps(data, ensure_ascii=False, separators=(",", ":")))
        (ROOT / "docs" / f"slide-{number}.html").write_text(rendered)
        print(f"Slide {number}: " + (f"{len(data['models'])} individual models" if number == 12 else data["target_season"] + " targets"))


if __name__ == "__main__":
    main()
