"""Check the plotted Texas observations and all five saved forecast quantiles."""
import csv
from datetime import date, timedelta
import json
from pathlib import Path
import sys
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
import build_slide_19 as BUILD


class TexasForecastTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.data = json.loads((BUILD.DATA / "slide-19.json").read_text())
        with (BUILD.DATA / "forecast-source.csv").open() as stream:
            cls.forecasts = list(csv.DictReader(stream))
        with (BUILD.DATA / "truth-source.csv").open() as stream:
            cls.truth = list(csv.DictReader(stream))

    def test_observations_are_source_values(self):
        actual = {point["date"]: point["value"] for point in self.data["observed"]}
        self.assertEqual(actual, {row["date"]: float(row["total_hosp"]) for row in self.truth})
        self.assertEqual({row["location_name"] for row in self.truth}, {"Texas"})
        self.assertEqual(len(actual), 82)
        self.assertEqual((self.data["start"], self.data["end"]), ("2024-10-05", "2026-04-25"))

    def test_every_quantile_matches_its_original_row(self):
        fields = {0.05: "q05", 0.25: "q25", 0.50: "median", 0.75: "q75", 0.95: "q95"}
        source = {(int(row["horizon"]), row["target_end_date"], float(row["output_type_id"])): float(row["value"])
                  for row in self.forecasts}
        plotted = {(group["horizon"], point["date"], quantile): point[field]
                   for group in self.data["series"] for point in group["points"] for quantile, field in fields.items()}
        self.assertEqual(plotted, source)
        self.assertEqual(len(source), len(self.forecasts))
        self.assertEqual([len(group["points"]) for group in self.data["series"]], [81, 80, 79, 78])
        self.assertEqual(self.data["intervals"], {"50": [.25, .75], "90": [.05, .95]})

    def test_horizons_and_cutoffs(self):
        for group in self.data["series"]:
            horizon = group["horizon"]
            self.assertIn(horizon, range(4))
            for point in group["points"]:
                reference = date.fromisoformat(point["reference_date"])
                self.assertEqual(date.fromisoformat(point["date"]), reference + timedelta(weeks=horizon))
                self.assertEqual(date.fromisoformat(point["data_cutoff"]), reference - timedelta(weeks=1))
                self.assertLess(point["data_cutoff"], point["date"])
                self.assertLessEqual(point["date"], self.data["end"])

    def test_complete_weekly_coverage_including_january_25(self):
        for group in self.data["series"]:
            points = group["points"]
            first = date(2024, 10, 12) + timedelta(weeks=group["horizon"])
            self.assertEqual([p["date"] for p in points],
                             [(first + timedelta(weeks=i)).isoformat() for i in range(81 - group["horizon"])])
            self.assertEqual(points[-1]["date"], self.data["end"])
            self.assertEqual(sum(p["reference_date"] == "2025-01-25" for p in points), 1)
        with (BUILD.DATA / "intervals-source.csv").open() as stream:
            intervals = {(int(r["horizon"]), r["target_end_date"]): r for r in csv.DictReader(stream)}
        for group in self.data["series"]:
            for point in group["points"]:
                row = intervals[(group["horizon"], point["date"])]
                for field, column in [("q25", "lower_50"), ("median", "median"), ("q75", "upper_50")]:
                    self.assertAlmostEqual(point[field], float(row[column]))

    def test_no_added_covariates_and_honest_scope(self):
        provenance = json.loads((BUILD.DATA / "sources.json").read_text())
        self.assertEqual(provenance["model_config"]["model_id"], BUILD.MODEL)
        self.assertNotIn("external_covariates", provenance["model_config"])
        self.assertEqual(provenance["model_config"]["feature_recipe"]["spatial_mode"], "none")
        self.assertEqual(self.data["season_bags"], 20)
        self.assertFalse(provenance["as_of_data"]["enabled"])
        self.assertTrue(provenance["completion"]["complete"])
        self.assertEqual(provenance["completion"]["origins"], 82)
        self.assertTrue(all("outputs/visualization_rolling_revised/" in f["source_path"]
                            for f in provenance["files"] if f["kind"] != "baseline"))
        self.assertEqual({row["location"] for row in self.forecasts}, {"48"})
        self.assertEqual({row["model_id"] for row in self.forecasts}, {BUILD.MODEL + "_revised_visualization"})

    def test_intervals_and_shared_axis(self):
        for group in self.data["series"]:
            for point in group["points"]:
                values = [point[field] for field in ["q05", "q25", "median", "q75", "q95"]]
                self.assertEqual(values, sorted(values))
                self.assertGreaterEqual(values[0], 0)
                self.assertLessEqual(values[-1], self.data["axis_max"])
        self.assertEqual(self.data["axis_max"], 14000)

    def test_reproducible_build(self):
        self.assertEqual(self.data, BUILD.chart_data())
        html = (ROOT / "docs" / "slide-19.html").read_text()
        self.assertEqual(html, BUILD.render(self.data))
        self.assertNotIn("/*__SLIDE_DATA__*/", html)
        self.assertNotIn("—", html)
        self.assertNotIn("<h1", html)


if __name__ == "__main__":
    unittest.main()
