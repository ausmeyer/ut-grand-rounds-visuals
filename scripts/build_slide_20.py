#!/usr/bin/env python3
"""Build aligned surveillance signals from retained study data, without fitting."""
import argparse
import csv
from datetime import date
import json
import math
from pathlib import Path

from build_slide_19 import ROOT, rows, sha256, write_json

DATA = ROOT / "data" / "slide-20"
SIGNALS = [
    {"id": "hospital", "label": ["Hospitalizations"], "unit": "Weekly admissions", "color": "#111111",
     "column": "total_hosp", "geography": "Texas", "domain": [0, 5000], "ticks": [0, 2500, 5000]},
    {"id": "influenza_ed", "label": ["Influenza ED visits"], "unit": "% of ED visits", "color": "#267dad",
     "column": "nssp_influenza_pct_ed_visits", "geography": "United States", "domain": [0, 10], "ticks": [0, 5, 10],
     "file": "nssp_influenza_national.csv"},
    {"id": "wastewater", "label": ["Influenza A", "wastewater"], "unit": "log₁₀ normalized RNA", "color": "#7952a4",
     "column": "wastewaterscan_flu_a_log10_pmmov", "geography": "National equal-site median", "domain": [-5, -3], "ticks": [-5, -4, -3],
     "file": "wastewaterscan_flu_a_national.csv"},
    {"id": "rsv_ed", "label": ["RSV ED visits"], "unit": "% of ED visits", "color": "#c67535",
     "column": "nssp_rsv_pct_ed_visits", "geography": "United States", "domain": [0, 1.2], "ticks": [0, .6, 1.2],
     "file": "nssp_rsv_national.csv"},
]


def import_sources(source_root):
    forecast = json.loads((ROOT / "data/slide-19/slide-19.json").read_text())
    DATA.mkdir(parents=True, exist_ok=True)
    sources = []
    for signal in SIGNALS:
        if signal["id"] == "hospital":
            original = ROOT / "data/slide-19/truth-source.csv"
        else:
            original = source_root / "data/surveillance_covariates" / signal["file"]
        selected = {}
        for row in rows(original):
            if forecast["start"] <= row["date"] <= forecast["end"]:
                previous = selected.get(row["date"])
                if previous is None or row.get("available_date", "") > previous.get("available_date", ""):
                    selected[row["date"]] = row
        if not selected:
            raise ValueError(f"No rows for {signal['id']}")
        records = [selected[key] for key in sorted(selected)]
        snapshot = DATA / f"{signal['id']}-source.csv"
        with snapshot.open("w", newline="") as stream:
            writer = csv.DictWriter(stream, fieldnames=list(records[0]), lineterminator="\n")
            writer.writeheader()
            writer.writerows(records)
        sources.append({"id": signal["id"], "source_path": str(original.relative_to(ROOT) if signal["id"] == "hospital" else original.relative_to(source_root)),
                        "source_sha256": sha256(original), "snapshot": snapshot.name,
                        "snapshot_sha256": sha256(snapshot), "rows": len(records)})
    metadata = source_root / "data/surveillance_covariates/surveillance_covariate_sources.json"
    write_json(DATA / "sources.json", {"source_project": "joint_twostage_distribution_study",
        "start": forecast["start"], "end": forecast["end"], "files": sources,
        "signal_metadata": json.loads(metadata.read_text()), "signal_metadata_sha256": sha256(metadata),
        "selection": "Latest retained issue for each source week, for a retrospective signal illustration. This is not an as-of forecast input trace. No smoothing, interpolation, normalization across signals, or calendar shifting."})


def chart_data():
    provenance = json.loads((DATA / "sources.json").read_text())
    panels = []
    for signal, source in zip(SIGNALS, provenance["files"]):
        if signal["id"] != source["id"]:
            raise ValueError("Unexpected signal order")
        snapshot = DATA / source["snapshot"]
        if sha256(snapshot) != source["snapshot_sha256"]:
            raise ValueError("Source snapshot changed")
        records = list(rows(snapshot))
        if len(records) != source["rows"]:
            raise ValueError("Source row count changed")
        points = []
        for row in records:
            value = float(row[signal["column"]]) if row[signal["column"]] else None
            if value is not None and (not math.isfinite(value) or not signal["domain"][0] <= value <= signal["domain"][1]):
                raise ValueError("Value outside the displayed scale")
            if signal["id"] == "hospital" and row["location_name"] != "Texas":
                raise ValueError("Unexpected hospital geography")
            if signal["id"] != "hospital" and not row["geography"].startswith("US"):
                raise ValueError("Unexpected covariate geography")
            if signal["id"] == "wastewater" and value is not None and int(row["site_count"]) < 10:
                raise ValueError("Insufficient wastewater sites")
            points.append({"date": row["date"], "value": value})
        if any((date.fromisoformat(b["date"]) - date.fromisoformat(a["date"])).days != 7 for a, b in zip(points, points[1:])):
            raise ValueError("Expected one row per calendar week")
        if points[0]["date"] != provenance["start"] or points[-1]["date"] != provenance["end"]:
            raise ValueError("Signal does not span the selected period")
        panels.append({**{key: value for key, value in signal.items() if key != "file"}, "points": points})
    return {"slide": 20, "start": provenance["start"], "end": provenance["end"], "panels": panels}


def render(data):
    template = (ROOT / "src/slide-20.template.html").read_text()
    if template.count("/*__SLIDE_DATA__*/") != 1:
        raise ValueError("Expected one data marker")
    return template.replace("/*__SLIDE_DATA__*/", json.dumps(data, separators=(",", ":"), ensure_ascii=False, allow_nan=False))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source-root", type=Path)
    args = parser.parse_args()
    if args.source_root:
        import_sources(args.source_root)
    data = chart_data()
    write_json(DATA / "slide-20.json", data)
    (ROOT / "docs/slide-20.html").write_text(render(data))
    print(f"Built Slide 20: {len(data['panels'])} signals, {data['start']} to {data['end']}")


if __name__ == "__main__":
    main()
