#!/usr/bin/env python3
"""Build national NSSP and NHSN seasonal series from official CDC extracts."""

from __future__ import annotations

import csv
from datetime import date, datetime, timedelta
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
PROJECT_ROOT = ROOT.parent
RAW = PROJECT_ROOT / "data" / "raw"
PROCESSED = PROJECT_ROOT / "data" / "processed"


def parse_date(value: str) -> date:
    return datetime.fromisoformat(value.replace("Z", "+00:00")).date()


def mmwr_coordinates(week_ending: date) -> tuple[int, int]:
    """Return MMWR year/week for a Saturday week-ending date."""
    midpoint = week_ending - timedelta(days=3)
    iso = midpoint.isocalendar()
    return iso.year, iso.week


def seasonal_coordinates(mmwr_year: int, mmwr_week: int) -> tuple[str, int, float] | None:
    if 36 <= mmwr_week <= 52:
        start = mmwr_year
        axis = float(mmwr_week - 35)
    elif mmwr_week == 53:
        start = mmwr_year
        axis = 17.5
    elif 1 <= mmwr_week <= 22:
        start = mmwr_year - 1
        axis = float(mmwr_week + 17)
    else:
        return None
    return f"{start}/{str(start + 1)[-2:]}", start, axis


def write_series(
    source: Path,
    output: Path,
    *,
    system: str,
    metric: str,
    date_field: str,
    location_field: str,
    location_value: str,
    value_field: str,
) -> None:
    rows = []
    with source.open(newline="", encoding="utf-8-sig") as handle:
        for row in csv.DictReader(handle):
            if row[location_field] != location_value or not row.get(value_field):
                continue
            week_ending = parse_date(row[date_field])
            mmwr_year, mmwr_week = mmwr_coordinates(week_ending)
            seasonal = seasonal_coordinates(mmwr_year, mmwr_week)
            if seasonal is None:
                continue
            season, season_start_year, week_axis = seasonal
            rows.append({
                "system": system,
                "metric": metric,
                "state": "United States",
                "season": season,
                "season_start_year": season_start_year,
                "mmwr_year": mmwr_year,
                "mmwr_week": mmwr_week,
                "week_axis": f"{week_axis:g}",
                "value": f"{float(row[value_field]):g}",
            })

    rows.sort(key=lambda row: (row["season_start_year"], float(row["week_axis"])))
    fields = [
        "system", "metric", "state", "season", "season_start_year",
        "mmwr_year", "mmwr_week", "week_axis", "value",
    ]
    with output.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        writer.writerows(rows)
    print(f"Wrote {output.relative_to(PROJECT_ROOT)} ({len(rows)} rows)")


def main() -> None:
    # CDC Data dataset rdmq-nq56, filtered to geography = United States.
    write_series(
        RAW / "nssp_national_flu_ed_raw.csv",
        PROCESSED / "nssp_national_seasons.csv",
        system="NSSP",
        metric="Percent of emergency department visits with influenza diagnosis",
        date_field="week_end",
        location_field="geography",
        location_value="United States",
        value_field="percent_visits_influenza",
    )

    # CDC Data dataset vdzy-6i9v; the downloaded extract already includes USA.
    write_series(
        RAW / "nhsn_flu_admissions_raw.csv",
        PROCESSED / "nhsn_national_seasons.csv",
        system="NHSN",
        metric="Confirmed influenza hospital admissions per 100,000",
        date_field="weekendingdate",
        location_field="jurisdiction",
        location_value="USA",
        value_field="totalconfflunewadmper100k",
    )


if __name__ == "__main__":
    main()
