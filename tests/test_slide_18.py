"""Verify the conceptual Slide 18 illustration and reproducible output."""
import json
import math
from pathlib import Path
from statistics import NormalDist
import sys
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
import build_slide_18 as BUILD


class ModelProgressionTests(unittest.TestCase):
    def test_schematic_distribution(self):
        data = BUILD.illustration()
        self.assertIn("schematic", data["kind"])
        self.assertIn("transformed scale", data["distribution"])
        curve = data["curve"]
        self.assertEqual(len(curve), 141)
        self.assertEqual((curve[0]["z"], curve[-1]["z"]), (-3.5, 3.5))
        for point, mirror in zip(curve, reversed(curve)):
            self.assertAlmostEqual(point["density"], NormalDist().pdf(point["z"]))
            self.assertAlmostEqual(point["density"], mirror["density"])
        self.assertEqual(max(curve, key=lambda point: point["density"])["z"], 0)
        self.assertAlmostEqual(curve[70]["density"], 1 / math.sqrt(2 * math.pi))

    def test_quantile_count_matches_slide_15(self):
        slide15 = json.loads((ROOT / "data" / "forecast-scores" / "slide-15.json").read_text())
        self.assertEqual(BUILD.illustration()["quantile_count"], slide15["quantile_count"])
        self.assertEqual(BUILD.illustration()["quantile_count"], 23)

    def test_generated_artifacts(self):
        data = BUILD.illustration()
        self.assertEqual(json.loads((BUILD.DATA / "slide-18.json").read_text()), data)
        html = (ROOT / "docs" / "slide-18.html").read_text()
        self.assertEqual(html, BUILD.render(data))
        self.assertNotIn("/*__ILLUSTRATION__*/", html)
        self.assertNotIn("—", html)
        self.assertNotIn("<h1", html)
        self.assertIn("prefers-reduced-motion", html)
        self.assertIn("not observed data or measured forecast performance", html)
        self.assertIn('value="2">2 · Fit the center', html)
        self.assertIn('value="3">3 · Fit the spread', html)
        self.assertIn("Squared-error loss", html)
        self.assertIn("Negative log-likelihood", html)
        self.assertIn("Keep the fitted center fixed", html)


if __name__ == "__main__":
    unittest.main()
