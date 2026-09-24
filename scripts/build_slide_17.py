#!/usr/bin/env python3
"""Build Slide 17 from archived Texas reconstruction and observation rows."""

import argparse
import csv
from datetime import date, timedelta
import hashlib
import json
import math
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data" / "slide-17"
START, END = "2009-09-01", "2022-10-01"
SHIFT = timedelta(days=728)
SOURCE_PATHS = {
    "reconstructed": "flusight_2023/imputed_and_stitched_hosp.csv",
    "observed": "flusight_2022/Flusight-forecast-data/data-truth/truth-Incident Hospitalizations.csv",
}


def sha256(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def read_rows(path):
    with path.open(newline="") as stream:
        return list(csv.DictReader(stream))


def write_json(path, value):
    path.write_text(json.dumps(value, indent=2, ensure_ascii=False) + "\n")


def import_sources(source_root):
    """Retain original selected rows, including the model's shifted date index."""
    DATA.mkdir(parents=True, exist_ok=True)
    manifest = []
    for kind, relative in SOURCE_PATHS.items():
        original = source_root / relative
        selected = []
        for row in read_rows(original):
            if row["location_name"] != "Texas":
                continue
            if kind == "reconstructed":
                if row["pred_hosp"] in ("", "NA"):
                    continue
                calendar_date = (date.fromisoformat(row["date"]) - SHIFT).isoformat()
                if not START <= calendar_date <= "2019-06-30":
                    continue
            elif not "2020-01-11" <= row["date"] <= END:
                continue
            selected.append(row)
        snapshot = DATA / f"{kind}-source.csv"
        with snapshot.open("w", newline="") as stream:
            writer = csv.DictWriter(stream, fieldnames=list(selected[0]), lineterminator="\n")
            writer.writeheader()
            writer.writerows(selected)
        manifest.append({"kind": kind, "source_path": relative,
                         "source_sha256": sha256(original),
                         "snapshot": snapshot.name, "snapshot_sha256": sha256(snapshot),
                         "rows": len(selected)})
    write_json(DATA / "sources.json", manifest)


def example():
    manifest = json.loads((DATA / "sources.json").read_text())
    series = {}
    for source in manifest:
        snapshot = DATA / source["snapshot"]
        if sha256(snapshot) != source["snapshot_sha256"]:
            raise ValueError(f"Changed source snapshot: {snapshot.name}")
        rows = read_rows(snapshot)
        if len(rows) != source["rows"]:
            raise ValueError("Source row count changed")
        points = []
        for row in rows:
            if row["location_name"] != "Texas":
                raise ValueError("Expected Texas only")
            stamp = date.fromisoformat(row["date"])
            if source["kind"] == "reconstructed":
                stamp -= SHIFT
                value = float(row["total_hosp"])
                rate_count = float(row["pred_hosp"]) * float(row["population"]) / 100000
                if abs(value - rate_count) > .500001 or stamp > date(2019, 6, 30):
                    raise ValueError("Reconstruction date or rate-to-count mismatch")
            else:
                value = float(row["value"])
            if not math.isfinite(value) or value < 0 or not START <= stamp.isoformat() <= END:
                raise ValueError("Invalid chart row")
            points.append({"date": stamp.isoformat(), "value": value})
        points.sort(key=lambda point: point["date"])
        dates = [date.fromisoformat(point["date"]) for point in points]
        if any((b - a).days != 7 for a, b in zip(dates, dates[1:])):
            raise ValueError("Expected unique weekly source rows")
        series[source["kind"]] = points
    maximum = max(point["value"] for points in series.values() for point in points)
    return {"slide": 17, "location": "Texas", "start": START, "end": END,
            "axis_max": math.ceil(maximum / 500) * 500, "tick_step": 500,
            "units": "Weekly influenza hospital admissions",
            "citation": {"label": "Meyer et al. · Epidemics · 2025",
                         "url": "https://doi.org/10.1016/j.epidem.2025.100816"},
            "provenance": {"date_shift_undone_days": SHIFT.days,
                           "reconstruction": "Saved normalized-ILI reconstruction from the published-method project; not a new fit or a frozen October 2022 data vintage.",
                           "observations": "Archived reported admission counts, including pandemic-era observations. Not all displayed observations were retained for model training."},
            **series}


def render(data):
    template = (ROOT / "src" / "slide-17.template.html").read_text()
    if template.count("/*__SLIDE_DATA__*/") != 1:
        raise ValueError("Expected one data marker")
    return template.replace("/*__SLIDE_DATA__*/", json.dumps(data, ensure_ascii=False, separators=(",", ":")))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--import-sources", type=Path, metavar="SANTILLANA_LAB_DIRECTORY")
    args = parser.parse_args()
    if args.import_sources:
        import_sources(args.import_sources)
    data = example()
    write_json(DATA / "slide-17.json", data)
    (ROOT / "docs" / "slide-17.html").write_text(render(data))
    print(f"Built Slide 17: {len(data['observed'])} observed and {len(data['reconstructed'])} reconstructed Texas weeks.")


if __name__ == "__main__":
    main()
