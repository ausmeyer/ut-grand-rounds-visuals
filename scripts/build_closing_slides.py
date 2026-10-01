#!/usr/bin/env python3
"""Build standalone slides 28–30 using their frozen, documented inputs."""

import json
import math
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def build():
    for number in (28, 29, 30):
        data = json.loads((ROOT / f"data/slide-{number}/inputs.json").read_text())
        if number == 28:
            assert data["n_draws_per_model"] == 5000
            assert [m["selected_week"] for m in data["models"]] == [47, 46, 40]
            assert data["models"][2]["hypothetical"] is True
            for model in data["models"]:
                assert len(model["mean_protection"]) == len(data["weeks_after_vaccination"]) == 197
                assert all(math.isfinite(v) and 0 <= v <= .6 for v in model["mean_protection"])
        if number == 29:
            assert data["missed_dose_probability"] is None
        if number == 30:
            assert data["synthetic"] is True and data["decision_rule_validated"] is False
            for key in ("initial", "updated"):
                scenario = data[key]
                assert len(scenario["forecast"]) == 33
                assert all(0 <= row[1] <= row[2] <= row[3] <= 1 for row in scenario["forecast"])
                assert abs(scenario["forecast"][0][2] - scenario["observations"][-1]) < 1e-12
        source = (ROOT / f"src/slide-{number}.html").read_text()
        assert source.count("/*__SLIDE_DATA__*/") == 1
        (ROOT / f"docs/slide-{number}.html").write_text(
            source.replace("/*__SLIDE_DATA__*/", json.dumps(data, separators=(",", ":"))))
        print(f"Built standalone slide {number}.")


if __name__ == "__main__":
    build()
