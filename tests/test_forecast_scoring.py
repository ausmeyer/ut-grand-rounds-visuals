"""Independently check full-quantile Texas WIS, matching, and relative skill."""
import csv
import json
import math
from pathlib import Path
import sys
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
import forecast_scoring as SCORE


def interval_wis(y, quantiles):
    weighted = .5 * abs(y - quantiles[.5])
    for lower in SCORE.LEVELS[:11]:
        alpha = 2 * lower
        lo, hi = quantiles[lower], quantiles[round(1 - lower, 3)]
        interval_score = hi - lo + 2 / alpha * (max(lo - y, 0) + max(y - hi, 0))
        weighted += alpha / 2 * interval_score
    return weighted / 11.5


class TexasScoreTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.data = {}
        cls.rows = {}
        for slide in [19, 21]:
            directory = ROOT / "data" / f"slide-{slide}"
            cls.data[slide] = json.loads((directory / f"slide-{slide}.json").read_text())
            cls.rows[slide] = {}
            for kind in ["scoring", "baseline"]:
                with (directory / f"{kind}-source.csv").open() as stream:
                    cls.rows[slide][kind] = list(csv.DictReader(stream))

    def test_wis_against_interval_score_definition(self):
        for slide, data in self.data.items():
            truth = {p["date"]: p["value"] for p in data["observed"]}
            for kind, identity in [("scoring", data["model_id"]), ("baseline", SCORE.BASELINE)]:
                forecasts = SCORE.distributions(self.rows[slide][kind], identity, truth)
                for key, quantiles in forecasts.items():
                    self.assertTrue(math.isclose(SCORE.wis(truth[key[2]], quantiles),
                                                 interval_wis(truth[key[2]], quantiles), rel_tol=1e-12, abs_tol=1e-12))

    def test_identical_texas_keys_and_independent_relative_skill(self):
        means = {}
        for slide, data in self.data.items():
            truth = {p["date"]: p["value"] for p in data["observed"]}
            model = SCORE.distributions(self.rows[slide]["scoring"], data["model_id"], truth)
            baseline = SCORE.distributions(self.rows[slide]["baseline"], SCORE.BASELINE, truth)
            self.assertEqual(data["scores"], SCORE.horizon_scores(model, baseline, truth))
            self.assertEqual(len(self.rows[slide]["scoring"]), 318 * 23)
            self.assertEqual(len(self.rows[slide]["baseline"]), 194 * 23)
            self.assertEqual([s["n"] for s in data["scores"]], [50, 49, 48, 47])
            for score in data["scores"]:
                horizon = score["horizon"]
                keys = sorted(k for k in baseline if k[0] == horizon)
                self.assertEqual(score["reference_dates"], [k[1] for k in keys])
                self.assertNotIn("2025-01-25", score["reference_dates"])
                for identity, forecasts in [(data["model_id"], model), (SCORE.BASELINE, baseline)]:
                    mean = math.fsum(interval_wis(truth[k[2]], forecasts[k]) for k in keys) / len(keys)
                    means[(identity, horizon)] = mean
                    column = "baseline_mean_wis" if identity == SCORE.BASELINE else "mean_wis"
                    self.assertAlmostEqual(score[column], mean, places=10)
        for a, b in zip(self.data[19]["scores"], self.data[21]["scores"]):
            self.assertEqual(a["reference_dates"], b["reference_dates"])
            self.assertEqual(a["baseline_mean_wis"], b["baseline_mean_wis"])
        models = [self.data[s]["model_id"] for s in [19, 21]] + [SCORE.BASELINE]
        for horizon in range(4):
            theta = {m: math.prod(means[(m, horizon)] / means[(other, horizon)]
                                 for other in models) ** (1 / len(models)) for m in models}
            for data in self.data.values():
                self.assertAlmostEqual(data["scores"][horizon]["rwis"],
                                       theta[data["model_id"]] / theta[SCORE.BASELINE], places=12)

    def test_missing_duplicate_and_crossed_quantiles_rejected(self):
        data = self.data[19]
        truth = {p["date"]: p["value"] for p in data["observed"]}
        rows = self.rows[19]["scoring"]
        with self.assertRaisesRegex(ValueError, "all 23 quantiles"):
            SCORE.distributions(rows[1:], data["model_id"], truth)
        with self.assertRaisesRegex(ValueError, "Duplicate scoring quantile"):
            SCORE.distributions(rows + [rows[0]], data["model_id"], truth)
        with self.assertRaisesRegex(ValueError, "Crossed scoring quantiles"):
            SCORE.distributions([{**rows[0], "value": "1000000"}] + rows[1:], data["model_id"], truth)

    def test_ratio_of_mean_scores_not_mean_of_weekly_ratios(self):
        baseline, model, truth = {}, {}, {"a": 0, "b": 0}
        for h in range(4):
            for stamp, denominator, numerator in [("a", 1, 1), ("b", 10, 100)]:
                baseline[(h, stamp, stamp)] = {q: denominator for q in SCORE.LEVELS}
                model[(h, stamp, stamp)] = {q: numerator for q in SCORE.LEVELS}
        for score in SCORE.horizon_scores(model, baseline, truth):
            self.assertAlmostEqual(score["rwis"], 101 / 11)
            self.assertNotAlmostEqual(score["rwis"], (1 + 10) / 2)


if __name__ == "__main__":
    unittest.main()
