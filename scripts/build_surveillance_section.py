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
        "question": "ILINet measures respiratory illness at outpatient points of care",
        "observation": "Percent of outpatient visits meeting the influenza-like illness definition",
        "unit": "% outpatient visits for ILI",
        "mainFile": "ilinet_national_seasons.csv",
        "geoFile": "ilinet_state_seasons.csv",
        "mainLocation": "United States",
        "geoHighlight": "Texas",
        "focusSeason": "2024/25",
        "series": "Public national extract: 1997/98–2025/26",
        "coverage": "≈4,000 providers; all states plus DC, PR, and USVI",
        "age": "0–4 · 5–24 · 25–49 · 50–64 · ≥65 years",
        "timeliness": "Weekly outpatient visit counts",
        "change": "2021/22 · ILI definition no longer excludes another known cause",
        "limitation": "ILI is syndromic—not laboratory-confirmed influenza—and the mix of reporting providers changes.",
        "source": "https://www.cdc.gov/fluview/overview/index.html",
        "networkSince": "Public archive shown from 1997/98",
    },
    {
        "id": "nssp",
        "slide": 6,
        "name": "NSSP",
        "fullName": "National Syndromic Surveillance Program",
        "color": "#0a6670",
        "image": "assets/slide-04-ed.webp",
        "imageAlt": "A monochrome illustration of an emergency department",
        "question": "NSSP evolved from early-warning syndromes to diagnosis-enriched surveillance",
        "observation": "Percent of ED visits assigned an influenza discharge diagnosis",
        "unit": "% ED visits with influenza diagnosis",
        "mainFile": "nssp_national_seasons.csv",
        "geoFile": "nssp_state_seasons.csv",
        "mainLocation": "United States",
        "geoHighlight": "Texas",
        "focusSeason": "2024/25",
        "series": "Downloaded extract: 2022/23–2025/26",
        "coverage": "51 jurisdictions in this extract; ≈83% of U.S. EDs nationally",
        "age": "Public products: 0–4 · 5–17 · 18–64 · ≥65 years",
        "timeliness": "Often available within 24 hours",
        "change": "The public influenza curve uses the standardized CDC Influenza DD v1 definition.",
        "limitation": "The signal still reflects who seeks ED care and how clinicians test, diagnose, and code.",
        "source": "https://www.cdc.gov/nssp/php/onboarding-resources/companion-guide-ed-data-respiratory-illness.html",
        "networkSince": "BioSense launched in 2003; the comparable influenza extract shown begins in 2022/23",
        "historySubtitle": "The platform broadened from bioterrorism early warning to all-hazards situational awareness—and its data became richer.",
        "historyTakeaway": [
            "NSSP is still syndromic surveillance infrastructure.",
            "The influenza curve shown here is diagnosis-based—not a symptom-only syndrome.",
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
        "question": "NHSN measures the operational burden arriving at U.S. hospitals",
        "observation": "New admissions with laboratory-confirmed influenza per 100,000 people",
        "unit": "admissions per 100,000",
        "mainFile": "nhsn_national_seasons.csv",
        "geoFile": "nhsn_state_seasons.csv",
        "mainLocation": "United States",
        "geoHighlight": "Texas",
        "focusSeason": "2024/25",
        "series": "Downloaded extract: 2020/21–2025/26",
        "coverage": "51 jurisdictions; required reporting from acute-care and critical-access hospitals",
        "age": "Age-stratified admissions; adult and pediatric occupancy",
        "timeliness": "Weekly facility-aggregated reporting",
        "change": "Oct–Nov 2024 · current Hospital Respiratory Data framework began",
        "limitation": "The current comparable framework is short, and facility completeness and revisions affect recent values.",
        "source": "https://www.cdc.gov/nhsn/psc/hospital-respiratory-reporting.html",
        "networkSince": "Earlier values precede the current HRD framework",
    },
    {
        "id": "flusurv",
        "slide": 8,
        "name": "FluSurv-NET",
        "fullName": "Influenza Hospitalization Surveillance Network",
        "color": "#c66a2b",
        "image": "assets/slide-04-hospital.webp",
        "imageAlt": "A monochrome illustration of a hospital participating in a surveillance catchment",
        "question": "FluSurv-NET turns hospitalizations into population-based rates",
        "observation": "Laboratory-confirmed influenza hospitalizations among residents of defined catchments",
        "unit": "hospitalizations per 100,000",
        "mainFile": "flusurv_state_seasons.csv",
        "geoFile": "flusurv_state_seasons.csv",
        "mainLocation": "FluSurv-NET",
        "geoHighlight": "California",
        "focusSeason": "2024/25",
        "series": "Network extract shown: 2009/10–2025/26",
        "coverage": ">90 counties in 14 states; ≈10% of the U.S. population",
        "age": "All ages with detailed age-specific hospitalization rates",
        "timeliness": "Weekly rates; recent weeks revised for reporting lag",
        "change": "2003 pediatric · 2005 adult · 2025 year-round surveillance",
        "limitation": "Its defined catchments support detailed rates but are not complete national coverage.",
        "source": "https://www.cdc.gov/fluview/overview/influenza-hospitalization-surveillance.html",
        "networkSince": "Pediatric surveillance 2003/04; adults 2005/06",
    },
    {
        "id": "nrevss",
        "slide": 9,
        "name": "NREVSS",
        "fullName": "National Respiratory and Enteric Virus Surveillance System",
        "color": "#7654a3",
        "image": "assets/slide-04-lab.webp",
        "imageAlt": "A monochrome illustration of a clinical virology laboratory",
        "question": "NREVSS measures how often submitted specimens test positive",
        "observation": "Percent of clinical laboratory specimens positive for influenza",
        "unit": "% clinical specimens positive",
        "mainFile": "nrevss_national_seasons.csv",
        "geoFile": "nrevss_state_seasons.csv",
        "mainLocation": "United States",
        "geoHighlight": "Texas",
        "focusSeason": "2024/25",
        "series": "Downloaded clinical-lab extract: 2016/17–2025/26",
        "coverage": "≈300 clinical laboratories across all states and several territories",
        "age": "Age reported when available; richer age detail in public-health laboratory data",
        "timeliness": "Weekly testing totals and positives",
        "change": "2015/16 · clinical and public-health laboratory reports separated",
        "limitation": "Participation and testing practices vary; percent positive is not population incidence.",
        "source": "https://www.cdc.gov/fluview/overview/index.html",
        "networkSince": "NREVSS has monitored respiratory viruses since 1989",
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

    return {
        "focus": focus,
        "seasons": main_curves,
        "geography": geo_curves,
        "summary": {
            "seasonCount": len(main_curves),
            "locationCount": len({curve["location"] for curve in geo_curves}),
        },
    }


def normalized_overlay(cache: dict[str, list[dict]]) -> dict:
    by_system = []
    for spec in SYSTEMS:
        rows = cache[spec["geoFile"]]
        curves = grouped_curves(rows)
        if spec["id"] == "flusurv":
            curves = [curve for curve in curves if curve["location"] in STATE_NAMES]

        eligible = [curve for curve in curves if len(curve["points"]) >= 12]
        curves_by_season: dict[str, list[dict]] = defaultdict(list)
        for curve in eligible:
            curves_by_season[curve["season"]].append(curve)

        normalized = []
        for season, season_curves in curves_by_season.items():
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

        medians = []
        for x in sorted({point[0] for curve in normalized for point in curve["points"]}):
            vals = [
                point[1]
                for curve in normalized
                for point in curve["points"]
                if point[0] == x
            ]
            if vals:
                medians.append([x, round(statistics.median(vals), 4)])

        by_system.append({
            "id": spec["id"],
            "name": spec["name"],
            "color": spec["color"],
            "curves": normalized,
            "median": medians,
            "curveCount": len(normalized),
            "locationCount": len({curve["location"] for curve in normalized}),
            "seasonCount": len({curve["season"] for curve in normalized}),
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

    for spec in SYSTEMS:
        output = ROOT / "docs" / f"slide-{spec['slide']:02d}.html"
        render(SYSTEM_TEMPLATE, output, spec, system_payload(spec, cache))
        print(f"Wrote {output.relative_to(ROOT)}")

    matrix_config = {
        "title": "Each surveillance system trades breadth, depth, and specificity",
        "rows": [
            {
                "name": "ILINet", "color": "#2677a8", "observes": "Outpatient ILI visits",
                "breadth": "≈4,000 providers", "history": "1997/98 archive",
                "age": "5 age groups", "speed": "Weekly",
                "limit": "Syndromic; provider mix varies",
            },
            {
                "name": "NSSP", "color": "#0a6670", "observes": "ED influenza diagnoses",
                "breadth": "≈83% of U.S. EDs", "history": "2003 network · 2022/23 extract",
                "age": "4 age groups", "speed": "Often <24 h",
                "limit": "Care-seeking and coding shape the signal",
            },
            {
                "name": "NHSN", "color": "#d97706", "observes": "Admissions and occupancy",
                "breadth": "Required hospital reporting", "history": "2020/21 extract",
                "age": "Age-stratified", "speed": "Weekly",
                "limit": "Current HRD framework begins in 2024",
            },
            {
                "name": "FluSurv-NET", "color": "#c66a2b", "observes": "Population-based hospitalizations",
                "breadth": ">90 counties · 14 states", "history": "2003/04 network",
                "age": "Detailed age rates", "speed": "Weekly + revisions",
                "limit": "Deep characterization in defined catchments",
            },
            {
                "name": "NREVSS", "color": "#7654a3", "observes": "Tests and percent positive",
                "breadth": "≈300 clinical labs", "history": "1989 network",
                "age": "When available", "speed": "Weekly",
                "limit": "Testing practice and participation vary",
            },
        ],
    }
    render(MATRIX_TEMPLATE, ROOT / "docs" / "slide-10.html", matrix_config, {})
    print("Wrote docs/slide-10.html")

    overlay_config = {
        "title": "Seasonal timing across surveillance systems",
        "subtitle": "Locations share one min–max scale within each surveillance system and season; calendar weeks are not shifted.",
        "order": ["ilinet", "nssp", "nrevss", "nhsn", "flusurv"],
    }
    render(OVERLAY_TEMPLATE, ROOT / "docs" / "slide-11.html", overlay_config, normalized_overlay(cache))
    print("Wrote docs/slide-11.html")


if __name__ == "__main__":
    main()
