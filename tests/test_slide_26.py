import json
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


class Slide26Results(unittest.TestCase):
    def test_full_curve_and_displayed_comparisons(self):
        data = json.loads((ROOT / "data/slide-26/slide-26.json").read_text())
        self.assertEqual(data["candidate_weeks"], list(range(36, 53)) + list(range(1, 13)))
        self.assertEqual(len(data["mean_visits"]), 29)
        self.assertEqual(data["candidate_weeks"][min(range(29), key=data["mean_visits"].__getitem__)], 47)
        for week, expected in [(44, 189.16985896908475), (47, 54.66781854260972), (48, 54.717128240967805)]:
            j = data["candidate_weeks"].index(week)
            self.assertAlmostEqual(data["mean_visits"][j], expected, places=10)
        self.assertEqual([round(data["mean_visits"][data["candidate_weeks"].index(w)]) for w in data["highlight_weeks"]], [55, 55])

    def test_regret_is_a_constant_shift_of_slide_25_remaining_burden(self):
        previous = json.loads((ROOT / "data/slide-25/slide-25.json").read_text())
        current = json.loads((ROOT / "data/slide-26/slide-26.json").read_text())
        self.assertEqual(previous["candidate_weeks"], current["candidate_weeks"])
        self.assertEqual(previous["best_index"], current["best_index"])
        shifts = [remaining - regret / 10000 for remaining, regret in zip(previous["mean_remaining"], current["mean_visits"])]
        self.assertGreater(shifts[0], 0)
        self.assertLess(max(shifts) - min(shifts), 1e-12)


if __name__ == "__main__":
    unittest.main()
