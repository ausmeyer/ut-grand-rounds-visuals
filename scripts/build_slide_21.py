#!/usr/bin/env python3
"""Build the paired Texas wastewater-lag forecast using the slide 19 renderer."""
import argparse
from pathlib import Path

from build_slide_19 import ROOT, WASTEWATER_MODEL, chart_data, import_sources, render, write_json

DATA = ROOT / "data" / "slide-21"


def build_data():
    return chart_data(DATA, WASTEWATER_MODEL, 21, "MIGHTE-Base + wastewater lags")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source-root", type=Path)
    args = parser.parse_args()
    if args.source_root:
        import_sources(args.source_root, DATA, WASTEWATER_MODEL)
    data = build_data()
    write_json(DATA / "slide-21.json", data)
    (ROOT / "docs" / "slide-21.html").write_text(render(data))
    print("Built Slide 21: Texas wastewater lags; forecasts per horizon: "
          + ", ".join(str(len(group["points"])) for group in data["series"]))


if __name__ == "__main__":
    main()
