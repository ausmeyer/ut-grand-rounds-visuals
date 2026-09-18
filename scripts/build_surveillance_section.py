#!/usr/bin/env python3
"""Build slides 5–11 from the downloaded influenza surveillance extracts."""

from __future__ import annotations

import csv
import json
import math
import statistics
from collections import defaultdict
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
PROJECT_ROOT = ROOT.parent
PROCESSED = PROJECT_ROOT / "data" / "processed"
SYSTEM_TEMPLATE = ROOT / "src" / "surveillance-system.template.html"
MATRIX_TEMPLATE = ROOT / "src" / "slide-10.template.html"
OVERLAY_TEMPLATE = ROOT / "src" / "slide-11.template.html"

CONFIG_MARKER = "/*__SLIDE_CONFIG__*/"
DATA_MARKER = "/*__SLIDE_DATA__*/"

STATE_NAMES = {
    "Alabama", "Alaska", "Arizona", "Arkansas", "California", "Colorado",
    "Connecticut", "Delaware", "Florida", "Georgia", "Hawaii", "Idaho",
    "Illinois", "Indiana", "Iowa", "Kansas", "Kentucky", "Louisiana",
    "Maine", "Maryland", "Massachusetts", "Michigan", "Minnesota",
    "Mississippi", "Missouri", "Montana", "Nebraska", "Nevada",
    "New Hampshire", "New Jersey", "New Mexico", "New York",
    "North Carolina", "North Dakota", "Ohio", "Oklahoma", "Oregon",
    "Pennsylvania", "Rhode Island", "South Carolina", "South Dakota",
    "Tennessee", "Texas", "Utah", "Vermont", "Virginia", "Washington",
    "West Virginia", "Wisconsin", "Wyoming", "District of Columbia",
}


SYSTEMS = [
    {
        "id": "ilinet",
        "slide": 5,
        "name": "ILINet",
        "fullName": "U.S. Outpatient Influenza-like Illness Surveillance Network",
        "color": "#2677a8",
        "image": "assets/slide-04-clinic.webp",
        "imageAlt": "A monochrome illustration of an outpatient clinic",
        "observation": "Percent of outpatient visits meeting the influenza-like illness definition",
        "signal": "% outpatient visits for ILI",
        "unit": "% outpatient visits for ILI",
        "mainFile": "ilinet_national_seasons.csv",
        "geoFile": "ilinet_state_seasons.csv",
        "mainLocation": "United States",
        "geoHighlight": "Texas",
        "focusSeason": "2024/25",
        "coverage": "≈4,000 providers in the full network",
        "ageSummary": "5 age groups",
        "ageDetail": "0–4 · 5–24 · 25–49 · 50–64 · ≥65 years",
        "timeliness": "Weekly",
        "change": "2021/22 · ILI definition no longer excludes another known cause",
        "limitation": "ILI includes other respiratory pathogens; reporting providers change.",
        "source": "https://www.cdc.gov/fluview/overview/index.html",
        "networkSince": "National archive begins in 1997/98; state histories can be shorter.",
    },
    {
        "id": "nssp",
        "slide": 6,
        "name": "NSSP",
        "fullName": "National Syndromic Surveillance Program",
        "color": "#0a6670",
        "image": "assets/slide-04-ed.webp",
        "imageAlt": "A monochrome illustration of an emergency department",
        "observation": "Percent of ED visits assigned an influenza discharge diagnosis",
        "signal": "% ED visits with influenza diagnosis",
        "unit": "% ED visits with influenza diagnosis",
        "mainFile": "nssp_national_seasons.csv",
        "geoFile": "nssp_state_seasons.csv",
        "mainLocation": "United States",
        "geoHighlight": "Texas",
        "focusSeason": "2024/25",
        "coverage": "≈85% of U.S. EDs in the full network",
        "ageSummary": "4 FluView age groups",
        "ageDetail": "0–4 · 5–17 · 18–64 · ≥65 years",
        "timeliness": "Weekly public reports; ED feeds often <24 h",
        "change": "The public influenza curve uses the standardized CDC Influenza DD v1 definition.",
        "limitation": "Testing, care-seeking, and diagnostic coding shape the signal.",
        "source": "https://www.cdc.gov/nssp/php/onboarding-resources/companion-guide-ed-data-respiratory-illness.html",
        "networkSince": "BioSense/NSSP: 2003–2026. Current public influenza series: 2022–2026.",
        "historySubtitle": "The platform broadened from bioterrorism early warning to all-hazards situational awareness, and its data became richer.",
        "historyTakeaway": [
            "NSSP is still syndromic surveillance infrastructure.",
            "The influenza curve shown here is diagnosis-based rather than a symptom-only syndrome.",
        ],
        "historyTimeline": [
            {
                "year": "2003",
                "title": "BioSense launches",
                "lines": ["Early warning after the 2001 attacks", "Prediagnostic + diagnostic feeds"],
            },
            {
                "year": "2011",
                "title": "BioSense 2.0",
                "lines": ["Shared, collaborative platform", "More civilian ED data"],
            },
            {
                "year": "2014",
                "title": "Becomes NSSP",
                "lines": ["State and local practitioners lead", "All-hazards situational awareness"],
            },
            {
                "year": "2020",
                "title": "Influenza DD v1",
                "lines": ["Standardized influenza definition", "Discharge diagnoses + clinical terms"],
            },
        ],
    },
    {
        "id": "nhsn",
        "slide": 7,
        "name": "NHSN",
        "fullName": "National Healthcare Safety Network Hospital Respiratory Data",
        "color": "#d97706",
        "image": "assets/slide-04-hospital.webp",
        "imageAlt": "A monochrome illustration of an inpatient hospital",
        "observation": "New admissions with laboratory-confirmed influenza per 100,000 people",
        "signal": "Influenza admissions per 100,000 people",
        "unit": "admissions per 100,000",
        "mainFile": "nhsn_national_seasons.csv",
        "geoFile": "nhsn_state_seasons.csv",
        "mainLocation": "United States",
        "geoHighlight": "Texas",
        "focusSeason": "2024/25",
        "coverage": "Required hospital reporting nationally",
        "ageSummary": "6 age groups + unknown",
        "ageDetail": "0–4 · 5–17 · 18–49 · 50–64 · 65–74 · ≥75 years",
        "timeliness": "Weekly",
        "change": "HRD requirements began Nov 2024; the 6 age groups apply to that framework.",
        "limitation": "Reporting requirements changed; completeness and revisions affect recent data.",
        "source": "https://www.cdc.gov/nhsn/psc/hospital-respiratory-reporting.html",
        "networkSince": "Hospital Respiratory Data (HRD): 2024–2026. Earlier reporting included.",
    },
    {
        "id": "flusurv",
        "slide": 8,
        "name": "FluSurv-NET",
        "fullName": "Influenza Hospitalization Surveillance Network",
        "color": "#c66a2b",
        "image": "assets/slide-04-hospital.webp",
        "imageAlt": "A monochrome illustration of a hospital participating in a surveillance catchment",
        "observation": "Laboratory-confirmed influenza hospitalizations among residents of defined catchments",
        "signal": "Influenza hospitalizations per 100,000 catchment residents",
        "unit": "hospitalizations per 100,000",
        "mainFile": "flusurv_state_seasons.csv",
        "geoFile": "flusurv_state_seasons.csv",
        "mainLocation": "FluSurv-NET",
        "aggregateLabel": "all EIP and IHSP sites combined",
        "geoHighlight": "California",
        "focusSeason": "2024/25",
        "coverage": "Full network: >90 counties in 14 states",
        "ageSummary": "5 broad age groups",
        "ageDetail": "0–4 · 5–17 · 18–49 · 50–64 · ≥65 years; finer splits available",
        "timeliness": "Weekly; revised for lag",
        "change": "2003 pediatric · 2005 adult · 2025 year-round surveillance",
        "limitation": "Rates describe defined catchments; national generalization is limited.",
        "source": "https://www.cdc.gov/fluview/overview/influenza-hospitalization-surveillance.html",
        "networkSince": "Children: 2003–2026; adults: 2005–2026. No 2020/21 curve in this extract.",
    },
    {
        "id": "nrevss",
        "slide": 9,
        "name": "NREVSS",
        "fullName": "National Respiratory and Enteric Virus Surveillance System",
        "color": "#7654a3",
        "image": "assets/slide-04-lab.webp",
        "imageAlt": "A monochrome illustration of a clinical virology laboratory",
        "observation": "Percent of clinical laboratory specimens positive for influenza",
        "signal": "% clinical specimens positive for influenza",
        "unit": "% clinical specimens positive",
        "mainFile": "nrevss_national_seasons.csv",
        "geoFile": "nrevss_state_seasons.csv",
        "mainLocation": "United States",
        "geoHighlight": "Texas",
        "focusSeason": "2024/25",
        "coverage": "≈300 clinical labs in the full network",
        "ageSummary": "All ages pooled",
        "ageDetail": "No age breakdown in the clinical-lab series shown",
        "timeliness": "Weekly",
        "change": "2015/16 · clinical and public-health laboratory reports separated",
        "limitation": "Testing and lab participation vary; positivity is not population incidence.",
        "source": "https://www.cdc.gov/fluview/overview/index.html",
        "networkSince": "NREVSS: 1989–2026. Separate clinical-lab reporting began in 2015/16.",
    },
]


def read_rows(filename: str) -> list[dict]:
    path = PROCESSED / filename
    if not path.exists():
        raise FileNotFoundError(f"Missing required surveillance extract: {path}")
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def finite_value(value: str | None) -> float | None:
    try:
        parsed = float(value)
    except (TypeError, ValueError):
        return None
    return parsed if math.isfinite(parsed) else None


def week_axis(row: dict) -> float | None:
    direct = finite_value(row.get("week_axis"))
    if direct is not None:
        return direct
    week = finite_value(row.get("mmwr_week"))
    if week is None:
        return None
    week = int(week)
    if 36 <= week <= 52:
        return float(week - 35)
    if week == 53:
        return 17.5
    if 1 <= week <= 22:
        return float(week + 17)
    return None


def grouped_curves(rows: list[dict], locations: set[str] | None = None) -> list[dict]:
    grouped: dict[tuple[str, str], list[tuple[float, float]]] = defaultdict(list)
    for row in rows:
        location = row.get("state", "")
        if locations is not None and location not in locations:
            continue
        season = row.get("season", "")
        x = week_axis(row)
        y = finite_value(row.get("value"))
        if not season or x is None or y is None or y < 0:
            continue
        grouped[(location, season)].append((x, y))

    curves = []
    for (location, season), points in grouped.items():
        deduped = {}
        for x, y in points:
            deduped[x] = y
        ordered = [[round(x, 2), round(y, 4)] for x, y in sorted(deduped.items())]
        if len(ordered) < 8:
            continue
        curves.append({
            "id": f"{location}-{season}".lower().replace(" ", "-").replace("/", "-"),
            "location": location,
            "season": season,
            "points": ordered,
        })
    return sorted(curves, key=lambda item: (item["season"], item["location"]))


def system_payload(spec: dict, cache: dict[str, list[dict]]) -> dict:
    main_rows = cache[spec["mainFile"]]
    geo_rows = cache[spec["geoFile"]]
    main_curves = grouped_curves(main_rows, {spec["mainLocation"]})
    focus = next(
        (curve for curve in main_curves if curve["season"] == spec["focusSeason"]),
        None,
    )
    if focus is None:
        raise ValueError(f"No {spec['focusSeason']} curve for {spec['name']} / {spec['mainLocation']}")

    geo_curves = grouped_curves(geo_rows)
    if spec["id"] == "flusurv":
        geo_curves = [curve for curve in geo_curves if curve["location"] in STATE_NAMES]
    geo_curves = [curve for curve in geo_curves if curve["season"] == spec["focusSeason"]]
    if not geo_curves:
        raise ValueError(f"No geographic curves for {spec['name']} in {spec['focusSeason']}")

    seasons = sorted({curve["season"] for curve in main_curves})
    locations = {curve["location"] for curve in geo_curves}
    if spec["id"] == "flusurv":
        geography = f"{len(locations)} state catchments"
    elif "District of Columbia" in locations:
        geography = f"{len(locations) - 1} states + DC"
    else:
        geography = f"{len(locations)} states"

    return {
        "focus": focus,
        "seasons": main_curves,
        "geography": geo_curves,
        "summary": {
            "seasonCount": len(seasons),
            "seasonRange": f"{seasons[0]}–{seasons[-1]}",
            "locationCount": len(locations),
            "geographyLabel": geography,
        },
    }


def normalized_overlay(cache: dict[str, list[dict]]) -> dict:
    by_system = []
    for spec in SYSTEMS:
        curves = grouped_curves(cache[spec["geoFile"]])
        if spec["id"] == "flusurv":
            curves = [curve for curve in curves if curve["location"] in STATE_NAMES]

        eligible = [curve for curve in curves if len(curve["points"]) >= 12]
        curves_by_season: dict[str, list[dict]] = defaultdict(list)
        for curve in eligible:
            curves_by_season[curve["season"]].append(curve)

        aggregate_curves = grouped_curves(
            cache[spec["mainFile"]],
            {spec["mainLocation"]},
        )
        aggregate_by_season = {
            curve["season"]: curve
            for curve in aggregate_curves
            if len(curve["points"]) >= 12
        }

        normalized = []
        normalized_aggregates = []
        for season, season_curves in curves_by_season.items():
            aggregate = aggregate_by_season.get(season)
            if aggregate is None:
                continue
            values = [point[1] for curve in season_curves for point in curve["points"]]
            lo, hi = min(values), max(values)
            if hi <= lo:
                continue
            for curve in season_curves:
                normalized.append({
                    "id": curve["id"],
                    "location": curve["location"],
                    "season": season,
                    "points": [[x, round((y - lo) / (hi - lo), 4)] for x, y in curve["points"]],
                })
            normalized_aggregates.append({
                "id": aggregate["id"],
                "location": aggregate["location"],
                "season": season,
                "points": [[x, round((y - lo) / (hi - lo), 4)] for x, y in aggregate["points"]],
            })

        summary = []
        minimum_summary_seasons = max(2, math.ceil(len(normalized_aggregates) / 2))
        for x in sorted({point[0] for curve in normalized_aggregates for point in curve["points"]}):
            vals = [
                point[1]
                for curve in normalized_aggregates
                for point in curve["points"]
                if point[0] == x
            ]
            if len(vals) >= minimum_summary_seasons:
                summary.append([x, round(statistics.median(vals), 4)])

        by_system.append({
            "id": spec["id"],
            "name": spec["name"],
            "color": spec["color"],
            "curves": normalized,
            "summary": summary,
            "curveCount": len(normalized),
            "locationCount": len({curve["location"] for curve in normalized}),
            "seasonCount": len({curve["season"] for curve in normalized}),
            "summarySeasonCount": len(normalized_aggregates),
            "summaryMinimumSeasons": minimum_summary_seasons,
        })
    return {"systems": by_system}


def render(template: Path, output: Path, config: dict, data: dict) -> None:
    text = template.read_text(encoding="utf-8")
    for marker in (CONFIG_MARKER, DATA_MARKER):
        if marker not in text:
            raise ValueError(f"Template {template.name} is missing {marker}")
    text = text.replace(CONFIG_MARKER, json.dumps(config, ensure_ascii=False, separators=(",", ":")))
    text = text.replace(DATA_MARKER, json.dumps(data, ensure_ascii=False, separators=(",", ":")))
    output.write_text(text, encoding="utf-8")


def main() -> None:
    required = sorted({spec["mainFile"] for spec in SYSTEMS} | {spec["geoFile"] for spec in SYSTEMS})
    cache = {filename: read_rows(filename) for filename in required}
    matrix_rows = []

    for spec in SYSTEMS:
        payload = system_payload(spec, cache)
        summary = payload["summary"]
        config = {
            **spec,
            "series": f"{summary['seasonRange']} · {summary['seasonCount']} seasons",
            "geography": f"{summary['geographyLabel']} shown ({spec['focusSeason']})",
        }
        output = ROOT / "docs" / f"slide-{spec['slide']:02d}.html"
        render(SYSTEM_TEMPLATE, output, config, payload)
        matrix_rows.append(config)
        print(f"Wrote {output.relative_to(ROOT)}")

    matrix_config = {
        "title": "Each surveillance system trades breadth, depth, and specificity",
        "rows": matrix_rows,
    }
    render(MATRIX_TEMPLATE, ROOT / "docs" / "slide-10.html", matrix_config, {})
    print("Wrote docs/slide-10.html")

    overlay_config = {
        "subtitle": "Locations share one min–max scale within each surveillance system and season; calendar weeks are not shifted.",
        "order": ["ilinet", "nssp", "nrevss", "nhsn", "flusurv"],
    }
    render(OVERLAY_TEMPLATE, ROOT / "docs" / "slide-11.html", overlay_config, normalized_overlay(cache))
    print("Wrote docs/slide-11.html")


if __name__ == "__main__":
    main()
