"""Offline data and reproducibility checks for the forecasting introduction."""
import gzip
import hashlib
import importlib.util
import json
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location("forecasting_intro", ROOT / "scripts/build_forecasting_intro.py")
BUILD = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(BUILD)


class ForecastingIntroTests(unittest.TestCase):
    def test_pinned_input_hashes(self):
        for source in json.loads((BUILD.DATA / "sources.json").read_text()):
            suffix = ".parquet.gz" if source["url"].endswith(".parquet") else ".gz"
            raw = gzip.decompress((BUILD.DATA / "sources" / (source["name"] + suffix)).read_bytes())
            self.assertEqual(hashlib.sha256(raw).hexdigest(), source["sha256"], source["name"])

    def test_example_is_vintage_correct_and_matches_archive(self):
        data = BUILD.forecast_example()
        self.assertEqual(len(data["models"]), 35)
        self.assertEqual(len(data["observed"]), 10)
        self.assertEqual(data["observed"][-1], {"date": "2024-12-07", "value": 493.0})
        self.assertTrue(all(p["date"] < data["issue_date"] for p in data["observed"]))
        self.assertEqual([p["median"] for p in data["ensemble"]], [584, 692, 769, 804])
        self.assertEqual([p["lower"] for p in data["ensemble"]], [296, 300, 307, 262])
        self.assertEqual([p["upper"] for p in data["ensemble"]], [858, 1095, 1434, 1727])
        self.assertTrue(all(len(m["points"]) == 4 for m in data["models"]))
        self.assertTrue(all(not m["id"].startswith("FluSight-") for m in data["models"]))
        self.assertIn("UMass-trends_ensemble", [m["id"] for m in data["models"]])

    def test_unique_model_weeks_and_reference_exclusion(self):
        paths = ["model-output/Team-model/2025-01-04-Team-model.csv", "model-output/Team-model/2025-01-04-Team-model.parquet",
                 "model-output/Team-model/2025-01-11-Team-model.csv", "model-output/Team-model/2025-07-05-Team-model.csv",
                 "model-output/FluSight-ensemble/2025-01-04-FluSight-ensemble.csv",
                 "model-output/FluSight-baseline/2025-01-04-FluSight-baseline.csv",
                 "model-output/Flusight-ensemble/2025-01-04-Flusight-ensemble.csv",
                 "model-output/Other-ensemble/2025-01-04-Other-ensemble.csv",
                 "model-output/Team-model/metadata-Team-model.txt"]
        tree = {"tree": [{"path": p, "type": "blob"} for p in paths]}
        result = BUILD.model_weeks(tree, "model-output", ["2025-01-04", "2025-01-11"])
        self.assertEqual(result, {"Other-ensemble": ["2025-01-04"], "Team-model": ["2025-01-04", "2025-01-11"]})
        with self.assertRaises(ValueError):
            BUILD.model_weeks({"tree": [], "truncated": True}, "model-output", [])

    def test_season_counts_and_denominators(self):
        data = BUILD.participation()["seasons"]
        self.assertEqual([s["models"] for s in data], [23, 21, 34, 43, 49])
        self.assertEqual([s["scheduled_weeks"] for s in data], [24, 31, 31, 28, 28])
        self.assertEqual([s["minimum_weeks"] for s in data], [12, 16, 16, 14, 14])
        self.assertIn("2022–23", [s["season"] for s in data])
        for season in json.loads((BUILD.DATA / "participation-audit.json").read_text()):
            for model in season["models"]:
                self.assertEqual(model["count"], len(set(model["weeks"])))
                self.assertEqual(model["included"], model["count"] * 2 >= len(season["scheduled_weeks"]))

    def test_generated_pages_match_sources(self):
        for number in (12, 13):
            data = json.loads((BUILD.DATA / f"slide-{number}.json").read_text())
            source = (ROOT / "src" / f"slide-{number}.template.html").read_text()
            expected = source.replace("/*__SLIDE_DATA__*/", json.dumps(data, ensure_ascii=False, separators=(",", ":")))
            self.assertEqual(expected, (ROOT / "docs" / f"slide-{number}.html").read_text())
            self.assertNotIn("—", source)


if __name__ == "__main__":
    unittest.main()
