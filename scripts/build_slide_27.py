#!/usr/bin/env python3
"""Build slide 27 from frozen national mean relative-regret results."""

import json
import math
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data" / "slide-27"


def build():
    data = json.loads((DATA / "inputs.json").read_text())
    assert data["analysis"] == "gam_primary" and data["population"] == "US, all ages"
    assert data["n_draws"] == 5000 and data["metric"] == "mean_relative_regret"
    rows = {row["week"]: row for row in data["rows"]}
    assert len(rows) == len(data["rows"]) == 4 and set(rows) == {40, 44, 47, 48}
    dates = [(40, ["Early October"]),
             (44, ["Late October /", "early November"]),
             (48, ["Late November /", "early December"])]
    bars = [{"week": week, "calendar_lines": lines,
             "loss_percent": 100 * rows[week]["mean_relative_regret"]}
            for week, lines in dates]
    assert all(math.isfinite(row["loss_percent"]) and 0 <= row["loss_percent"] <= 25
               for row in bars)
    assert [round(row["loss_percent"], 1) for row in bars] == [21.8, 9.2, 2.3]
    data.update(bars=bars, axis_max=25)
    (DATA / "slide-27.json").write_text(json.dumps(data, indent=2) + "\n")
    source = (ROOT / "src" / "slide-27.html").read_text()
    assert source.count("/*__SLIDE_DATA__*/") == 1
    (ROOT / "docs" / "slide-27.html").write_text(
        source.replace("/*__SLIDE_DATA__*/", json.dumps(data, separators=(",", ":"))))
    print("Built slide 27: " + ", ".join(
        f"week {row['week']} = {row['loss_percent']:.1f}%" for row in bars))


if __name__ == "__main__":
    build()
