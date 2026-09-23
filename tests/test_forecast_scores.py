"""Check the single-week teaching example against source rows and two WIS formulas."""
import gzip
import hashlib
import json
from pathlib import Path
import sys
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
import build_forecast_scores as BUILD


class ForecastScoreTests(unittest.TestCase):
    def test_source_hashes(self):
        for source in json.loads((BUILD.DATA / "sources.json").read_text()):
            raw = gzip.decompress((BUILD.DATA / "sources" / (source["name"] + ".gz")).read_bytes())
            self.assertEqual(hashlib.sha256(raw).hexdigest(), source["sha256"])

    def test_real_forecast_and_observation(self):
        data = BUILD.example()
        self.assertEqual(data["observed"], 1169)
        self.assertEqual(data["truth_vintage"], "2025-06-18")
        for model, values in (("ensemble", [300, 512, 692, 855, 1095]), ("baseline", [23, 380, 493, 606, 965])):
            self.assertEqual([data[model][q] for q in ["0.025", "0.25", "0.5", "0.75", "0.975"]], values)
            self.assertEqual(len(data[model]), 23)
            self.assertLess(max(data[model].values()), data["axis_max"])
        self.assertEqual(data["scores"]["absolute_error"], 477)
        self.assertEqual(data["baseline"]["0.5"], 493)  # Last observation in the forecast-time vintage.

    def test_wis_independently_as_mean_quantile_loss(self):
        data = BUILD.example()
        for model in ("ensemble", "baseline"):
            losses = []
            for probability, prediction in data[model].items():
                error = data["observed"] - prediction
                losses.append(2 * (float(probability) - (error < 0)) * error)
            self.assertAlmostEqual(sum(losses) / len(losses), data["scores"][model + "_wis"], places=10)
        self.assertAlmostEqual(data["scores"]["ensemble_wis"], 319.2778260869565)
        self.assertAlmostEqual(data["scores"]["baseline_wis"], 508.77217391304356)
        self.assertAlmostEqual(data["scores"]["relative_wis"], 319.2778260869565 / 508.77217391304356)

    def test_wis_boundaries(self):
        point = {str(q): 10 for q in BUILD.QUANTILES}
        self.assertEqual(BUILD.wis(point, 10), 0)
        self.assertAlmostEqual(BUILD.wis(point, 0), 10)
        self.assertAlmostEqual(BUILD.wis(point, 20), 10)

    def test_generated_pages_and_no_early_outcome(self):
        full = BUILD.example()
        for number in (14, 15):
            data = BUILD.slide_data(number, full)
            self.assertEqual(data, json.loads((BUILD.DATA / f"slide-{number}.json").read_text()))
            html = (ROOT / "docs" / f"slide-{number}.html").read_text()
            self.assertEqual(html, BUILD.render(data))
            self.assertNotIn("—", html)
        self.assertNotIn("observed", BUILD.slide_data(14, full))
        self.assertNotIn("scores", BUILD.slide_data(14, full))

    def test_slide12_is_unchanged(self):
        self.assertEqual(hashlib.sha256((ROOT / "docs/slide-12.html").read_bytes()).hexdigest(),
                         "4740785f0d8809ac29ca897b7e5e2b7331a4374f9fe1f07e85912663ffc696cd")


if __name__ == "__main__":
    unittest.main()
