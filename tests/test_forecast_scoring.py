"""Independently check state/DC WIS, matching, exclusions, and relative skill."""
from itertools import islice
import json
import math
from pathlib import Path
import sys
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
import forecast_scoring as SCORE
from build_slide_19 import rows


def interval_wis(y, quantiles):
    weighted = .5 * abs(y - quantiles[.5])
    for lower in SCORE.LEVELS[:11]:
        alpha = 2 * lower
        lo, hi = quantiles[lower], quantiles[round(1 - lower, 3)]
        interval_score = hi - lo + 2 / alpha * (max(lo - y, 0) + max(y - hi, 0))
        weighted += alpha / 2 * interval_score
    return weighted / 11.5


class StateScoreTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.data = {}
        cls.forecasts = {}
        cls.truth = {}
        for slide in [19, 21]:
            directory = ROOT / "data" / f"slide-{slide}"
            cls.data[slide] = json.loads((directory / f"slide-{slide}.json").read_text())
            cls.truth[slide] = {(r["location"], r["date"]): float(r["total_hosp"])
                                for r in rows(directory / "scoring-truth-source.csv")}
            cls.forecasts[slide] = {}
            for kind in ["scoring", "baseline"]:
                identity = SCORE.BASELINE if kind == "baseline" else cls.data[slide]["model_id"]
                cls.forecasts[slide][kind] = SCORE.distributions(rows(directory / f"{kind}-source.csv.gz"), identity, cls.truth[slide])

    def test_wis_against_interval_score_definition(self):
        for slide, data in self.data.items():
            truth = self.truth[slide]
            for forecasts in self.forecasts[slide].values():
                for key, quantiles in forecasts.items():
                    self.assertTrue(math.isclose(SCORE.wis(truth[(key[3], key[2])], quantiles),
                                                 interval_wis(truth[(key[3], key[2])], quantiles), rel_tol=1e-12, abs_tol=1e-12))

    def test_identical_state_keys_and_independent_relative_skill(self):
        means = {}
        for slide, data in self.data.items():
            truth = self.truth[slide]
            model, baseline = self.forecasts[slide]["scoring"], self.forecasts[slide]["baseline"]
            self.assertEqual(data["scores"], SCORE.horizon_scores(model, baseline, truth))
            self.assertEqual(len(model), 318 * 51)
            self.assertEqual(len(baseline), 194 * 51)
            self.assertEqual([s["n"] for s in data["scores"]], [2550, 2499, 2448, 2397])
            for score in data["scores"]:
                horizon = score["horizon"]
                keys = sorted(k for k in baseline if k[0] == horizon)
                self.assertEqual(score["reference_dates"], sorted({k[1] for k in keys}))
                self.assertEqual(set(score["locations"]), SCORE.LOCATIONS)
                self.assertEqual(len(score["locations"]), 51)
                self.assertIn("11", score["locations"])
                self.assertNotIn("US", score["locations"])
                self.assertNotIn("72", score["locations"])
                self.assertNotIn("78", score["locations"])
                self.assertNotIn("2025-01-25", score["reference_dates"])
                for identity, forecasts in [(data["model_id"], model), (SCORE.BASELINE, baseline)]:
                    mean = math.fsum(interval_wis(truth[(k[3], k[2])], forecasts[k]) for k in keys) / len(keys)
                    means[(identity, horizon)] = mean
                    column = "baseline_mean_wis" if identity == SCORE.BASELINE else "mean_wis"
                    self.assertAlmostEqual(score[column], mean, places=10)
        for a, b in zip(self.data[19]["scores"], self.data[21]["scores"]):
            self.assertEqual(a["reference_dates"], b["reference_dates"])
            self.assertEqual(a["baseline_mean_wis"], b["baseline_mean_wis"])
        models = [self.data[s]["model_id"] for s in [19, 21]] + [SCORE.BASELINE]
        self.assertEqual(self.forecasts[19]["baseline"], self.forecasts[21]["baseline"])
        for horizon in range(4):
            theta = {m: math.prod(means[(m, horizon)] / means[(other, horizon)]
                                 for other in models) ** (1 / len(models)) for m in models}
            for data in self.data.values():
                self.assertAlmostEqual(data["scores"][horizon]["rwis"],
                                       theta[data["model_id"]] / theta[SCORE.BASELINE], places=12)

    def test_missing_duplicate_and_crossed_quantiles_rejected(self):
        data = self.data[19]
        truth = self.truth[19]
        sample = list(islice(rows(ROOT / "data/slide-19/scoring-source.csv.gz"), 23))
        with self.assertRaisesRegex(ValueError, "all 23 quantiles"):
            SCORE.distributions(sample[1:], data["model_id"], truth)
        with self.assertRaisesRegex(ValueError, "Duplicate scoring quantile"):
            SCORE.distributions(sample + [sample[0]], data["model_id"], truth)
        with self.assertRaisesRegex(ValueError, "Crossed scoring quantiles"):
            SCORE.distributions([{**sample[0], "value": "1000000"}] + sample[1:], data["model_id"], truth)
        for excluded in ["US", "72", "78"]:
            with self.subTest(excluded=excluded), self.assertRaisesRegex(ValueError, "Invalid state/DC"):
                SCORE.distributions([{**sample[0], "location": excluded}], data["model_id"], truth)

    def test_ratio_of_mean_scores_not_mean_of_weekly_ratios(self):
        baseline, model, truth = {}, {}, {}
        for h in range(4):
            for location in SCORE.LOCATIONS:
                for stamp, denominator, numerator in [("a", 1, 1), ("b", 10, 100)]:
                    truth[(location, stamp)] = 0
                    baseline[(h, stamp, stamp, location)] = {q: denominator for q in SCORE.LEVELS}
                    model[(h, stamp, stamp, location)] = {q: numerator for q in SCORE.LEVELS}
        for score in SCORE.horizon_scores(model, baseline, truth):
            self.assertAlmostEqual(score["rwis"], 101 / 11)
            self.assertNotAlmostEqual(score["rwis"], (1 + 10) / 2)

    def test_pool_raw_scores_not_state_relative_scores(self):
        baseline, model, truth = {}, {}, {}
        for h in range(4):
            for location in SCORE.LOCATIONS:
                truth[(location, "a")] = 0
                baseline[(h, "a", "a", location)] = {q: 1 if location == "01" else 10 for q in SCORE.LEVELS}
                model[(h, "a", "a", location)] = {q: 1 if location == "01" else 100 for q in SCORE.LEVELS}
        for score in SCORE.horizon_scores(model, baseline, truth):
            self.assertAlmostEqual(score["rwis"], (1 + 50 * 100) / (1 + 50 * 10))
            self.assertNotAlmostEqual(score["rwis"], (1 + 50 * 10) / 51)


if __name__ == "__main__":
    unittest.main()
