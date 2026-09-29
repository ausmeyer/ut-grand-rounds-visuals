#!/usr/bin/env python3
"""Build slide 26 from the frozen national, all-age manuscript results."""

import json
import math
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data" / "slide-26"


def build():
    data = json.loads((DATA / "inputs.json").read_text())
    weeks = [r["week"] for r in data["rows"]]
    assert weeks == list(range(36, 53)) + list(range(1, 13))
    assert data["n_draws"] == 5000 and data["encounters_per_week"] == 10000
    means = [r["mean_regret"] * data["encounters_per_week"] for r in data["rows"]]
    assert all(math.isfinite(x) and x >= 0 for x in means)
    best = min(range(len(means)), key=means.__getitem__)
    assert weeks[best] == 47
    assert [round(means[weeks.index(w)]) for w in [44, 47, 48]] == [189, 55, 55]
    data.update(candidate_weeks=weeks, mean_visits=means, best_index=best,
                highlight_weeks=[47, 48], y_max=math.ceil(max(means) / 200) * 200)
    (DATA / "slide-26.json").write_text(json.dumps(data, indent=2) + "\n")
    source = (ROOT / "src" / "slide-26.html").read_text()
    assert source.count("/*__SLIDE_DATA__*/") == 1
    (ROOT / "docs" / "slide-26.html").write_text(
        source.replace("/*__SLIDE_DATA__*/", json.dumps(data, separators=(",", ":"))))
    print(f"Built slide 26: {len(weeks)} dates, week {weeks[best]} minimum; weeks 44/47/48 = "
          + "/".join(f"{means[weeks.index(w)]:.3f}" for w in [44, 47, 48]) + " standardized visits.")


if __name__ == "__main__":
    build()
