"""Verify every added signal and wastewater forecast against its source rows."""
import csv
from datetime import date, timedelta
import json
from pathlib import Path
import sys
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
import build_slide_19 as FORECAST
import build_slide_20 as SIGNALS
import build_slide_21 as WASTEWATER


class SignalTests(unittest.TestCase):
    def test_every_signal_value_and_calendar_date(self):
        data = SIGNALS.chart_data()
        self.assertEqual(len(data["panels"]), 4)
        for panel in data["panels"]:
            with (SIGNALS.DATA / f"{panel['id']}-source.csv").open() as stream:
                source = list(csv.DictReader(stream))
            expected = [{"date": row["date"], "value": float(row[panel["column"]]) if row[panel["column"]] else None} for row in source]
            self.assertEqual(panel["points"], expected)
            self.assertEqual(len(expected), 82)
            for a, b in zip(expected, expected[1:]):
                self.assertEqual((date.fromisoformat(b["date"]) - date.fromisoformat(a["date"])).days, 7)
            self.assertEqual(expected[0]["date"], data["start"])
            self.assertEqual(expected[-1]["date"], data["end"])
            for point in expected:
                self.assertLessEqual(panel["domain"][0], point["value"])
                self.assertGreaterEqual(panel["domain"][1], point["value"])

    def test_sources_and_units(self):
        data = SIGNALS.chart_data()
        self.assertEqual([p["geography"] for p in data["panels"]], ["Texas", "United States", "National equal-site median", "United States"])
        self.assertEqual(data["panels"][2]["unit"], "log₁₀ normalized RNA")
        with (SIGNALS.DATA / "wastewater-source.csv").open() as stream:
            for row in csv.DictReader(stream):
                self.assertGreaterEqual(int(row["site_count"]), 10)
                self.assertEqual(float(row["log10_pseudocount"]), .00001)
        truth = json.loads((ROOT / "data/slide-19/slide-19.json").read_text())
        self.assertEqual(data["panels"][0]["points"], truth["observed"])

    def test_reproducible_build(self):
        data = SIGNALS.chart_data()
        self.assertEqual(data, json.loads((SIGNALS.DATA / "slide-20.json").read_text()))
        html = (ROOT / "docs/slide-20.html").read_text()
        self.assertEqual(html, SIGNALS.render(data))
        self.assertNotIn("—", html)
        self.assertNotIn("<h1", html)


class WastewaterForecastTests(unittest.TestCase):
    def test_every_quantile_from_the_paired_source(self):
        data = WASTEWATER.build_data()
        with (WASTEWATER.DATA / "forecast-source.csv").open() as stream:
            rows = list(csv.DictReader(stream))
        source = {(int(row["horizon"]), row["target_end_date"], float(row["output_type_id"])): float(row["value"]) for row in rows}
        plotted = {(group["horizon"], point["date"], quantile): point[field]
                   for group in data["series"] for point in group["points"] for quantile, field in FORECAST.QUANTILES.items()}
        self.assertEqual(source, plotted)
        self.assertEqual(len(source), len(rows))
        self.assertEqual({r["model_id"] for r in rows}, {FORECAST.WASTEWATER_MODEL})
        for group in data["series"]:
            for point in group["points"]:
                reference = date.fromisoformat(point["reference_date"])
                self.assertEqual(date.fromisoformat(point["date"]), reference + timedelta(weeks=group["horizon"]))
                self.assertEqual(date.fromisoformat(point["data_cutoff"]), reference - timedelta(weeks=1))
                values = [point[field] for field in FORECAST.QUANTILES.values()]
                self.assertEqual(values, sorted(values))
                self.assertGreaterEqual(values[0], 0)
                self.assertLessEqual(values[-1], data["axis_max"])

    def test_comparable_configuration_observations_and_axes(self):
        base = json.loads((ROOT / "data/slide-19/sources.json").read_text())
        ww = json.loads((WASTEWATER.DATA / "sources.json").read_text())
        self.assertEqual(base["runtime"], ww["runtime"])
        self.assertEqual(base["evaluation_period"], ww["evaluation_period"])
        self.assertEqual(base["as_of_data"], ww["as_of_data"])
        for key in ["paired_seed_offset", "fit_config_profile", "fit_algorithm", "scale_parameterization", "feature_recipe"]:
            self.assertEqual(base["model_config"][key], ww["model_config"][key])
        self.assertEqual(ww["model_config"]["external_covariates"]["columns"], FORECAST.WASTEWATER_COLUMNS)
        base_data, data = FORECAST.chart_data(), WASTEWATER.build_data()
        for key in ["start", "end", "axis_max", "tick_step", "observed", "season_bags", "intervals"]:
            self.assertEqual(base_data[key], data[key])
        self.assertEqual(data["season_bags"], 20)
        for b, w in zip(base_data["series"], data["series"]):
            self.assertEqual([p["date"] for p in b["points"]], [p["date"] for p in w["points"]])

    def test_reproducible_build(self):
        data = WASTEWATER.build_data()
        self.assertEqual(data, json.loads((WASTEWATER.DATA / "slide-21.json").read_text()))
        self.assertEqual((ROOT / "docs/slide-21.html").read_text(), FORECAST.render(data))
        self.assertEqual(data["slide"], 21)


if __name__ == "__main__":
    unittest.main()
