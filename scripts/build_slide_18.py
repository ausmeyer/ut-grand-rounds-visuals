#!/usr/bin/env python3
"""Build the three-view model progression schematic for Slide 18."""

import json
import math
from pathlib import Path

from build_forecast_scores import QUANTILES

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data" / "slide-18"


def illustration():
    return {
        "slide": 18,
        "kind": "schematic, not observed data or measured model performance",
        "distribution": "standard normal on an illustrative transformed scale",
        "quantile_count": len(QUANTILES),
        "curve": [{"z": round(-3.5 + i * .05, 2),
                   "density": math.exp(-.5 * (-3.5 + i * .05) ** 2) / math.sqrt(2 * math.pi)}
                  for i in range(141)],
    }


def render(data):
    template = (ROOT / "src" / "slide-18.template.html").read_text()
    if template.count("/*__ILLUSTRATION__*/") != 1:
        raise ValueError("Expected one illustration marker")
    return template.replace("/*__ILLUSTRATION__*/", json.dumps(data, separators=(",", ":")))


def main():
    data = illustration()
    DATA.mkdir(parents=True, exist_ok=True)
    (DATA / "slide-18.json").write_text(json.dumps(data, indent=2) + "\n")
    (ROOT / "docs" / "slide-18.html").write_text(render(data))
    print("Built Slide 18: model progression, center fit, and spread fit, three views.")


if __name__ == "__main__":
    main()
