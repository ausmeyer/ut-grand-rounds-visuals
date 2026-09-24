"""Verify the chart against archived source rows, on the original calendar."""
import csv
from datetime import date, timedelta
import hashlib
import json
from pathlib import Path
import sys
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
import build_slide_17 as BUILD


class ReconstructionTests(unittest.TestCase):
    def test_source_snapshots(self):
        for source in json.loads((BUILD.DATA / "sources.json").read_text()):
            raw = (BUILD.DATA / source["snapshot"]).read_bytes()
            self.assertEqual(hashlib.sha256(raw).hexdigest(), source["snapshot_sha256"])
            self.assertEqual(len(list(csv.DictReader(raw.decode().splitlines()))), source["rows"])

    def test_every_reconstruction_row_and_date(self):
        data = BUILD.example()
        rows = BUILD.read_rows(BUILD.DATA / "reconstructed-source.csv")
        self.assertEqual(len(data["reconstructed"]), 456)
        for row, point in zip(rows, data["reconstructed"]):
            self.assertEqual(row["location_name"], "Texas")
            self.assertEqual((date.fromisoformat(row["date"]) - date.fromisoformat(point["date"])).days, 728)
            self.assertEqual(point["value"], float(row["total_hosp"]))
            self.assertEqual(point["value"], round(float(row["pred_hosp"]) * 29527941 / 100000))
        self.assertEqual(data["reconstructed"][0], {"date": "2010-10-09", "value": 74})
        self.assertEqual(data["reconstructed"][-1]["date"], "2019-06-29")
        self.assertEqual(max(data["reconstructed"], key=lambda point: point["value"]),
                         {"date": "2018-01-27", "value": 2321})

    def test_all_observations_preserved(self):
        points = BUILD.example()["observed"]
        rows = BUILD.read_rows(BUILD.DATA / "observed-source.csv")
        self.assertEqual(len(points), 143)
        self.assertEqual(points, [{"date": row["date"], "value": float(row["value"])} for row in rows])
        self.assertEqual(points[0]["date"], "2020-01-11")
        self.assertEqual(points[-1]["date"], "2022-10-01")
        self.assertEqual(max(point["value"] for point in points), 663)

    def test_calendar_range_and_no_filled_gaps(self):
        data = BUILD.example()
        self.assertEqual((data["start"], data["end"]), ("2009-09-01", "2022-10-01"))
        self.assertEqual(data["axis_max"], 2500)
        for key in ("observed", "reconstructed"):
            dates = [date.fromisoformat(point["date"]) for point in data[key]]
            self.assertEqual(len(set(dates)), len(dates))
            self.assertTrue(all((b - a).days == 7 for a, b in zip(dates, dates[1:])))
            self.assertTrue(all(0 <= point["value"] < data["axis_max"] for point in data[key]))
        self.assertLess(data["reconstructed"][-1]["date"], data["observed"][0]["date"])

    def test_full_history_extension_uses_reported_counts(self):
        data = BUILD.example()
        rows = BUILD.read_rows(BUILD.DATA / "extended-source.csv")
        self.assertTrue(all(row["jurisdiction"] == "TX" for row in rows))
        expected = [{"date": row["weekendingdate"][:10], "value": float(row["totalconfflunewadm"])} for row in rows]
        self.assertEqual(data["extended"], sorted(expected, key=lambda point: point["date"]))
        self.assertEqual(len(data["extended"]), 195)
        self.assertEqual(data["extended"][0], {"date": "2022-10-08", "value": 213})
        self.assertEqual(data["extended"][-1], {"date": "2026-06-27", "value": 73})
        self.assertEqual(max(point["value"] for point in data["extended"]), 4729)
        self.assertEqual((data["full_end"], data["full_axis_max"], data["full_tick_step"]), ("2026-07-01", 5000, 1000))
        self.assertTrue(all(data["end"] < point["date"] <= data["full_end"] for point in data["extended"]))
        retained = [point for point in data["observed"] if point["date"] >= data["retained_observed_start"]]
        full_observed = retained + data["extended"]
        self.assertEqual(len(full_observed), 261)
        dates = [date.fromisoformat(point["date"]) for point in full_observed]
        self.assertTrue(all((b - a).days == 7 for a, b in zip(dates, dates[1:])))

    def test_generated_artifacts(self):
        data = BUILD.example()
        self.assertEqual(json.loads((BUILD.DATA / "slide-17.json").read_text()), data)
        html = (ROOT / "docs" / "slide-17.html").read_text()
        self.assertEqual(html, BUILD.render(data))
        self.assertNotIn("—", html)
        self.assertIn("Reconstructed from ILINet", html)
        self.assertIn("A longer training history provides more context for the model to forecast.", html)
        self.assertNotIn("<h1", html)

    def test_stitched_sequence_matches_original_model_index(self):
        data = BUILD.example()
        self.assertEqual(data["training_shift_days"], 728)
        self.assertEqual(data["retained_observed_start"], "2021-07-01")
        shifted = [{"date": (date.fromisoformat(point["date"]) + timedelta(days=728)).isoformat(),
                    "value": point["value"]} for point in data["reconstructed"]]
        rows = BUILD.read_rows(BUILD.DATA / "reconstructed-source.csv")
        self.assertEqual(shifted, [{"date": row["date"], "value": float(row["total_hosp"])} for row in rows])
        retained = [point for point in data["observed"] if point["date"] >= data["retained_observed_start"]]
        self.assertEqual(len(retained), 66)
        self.assertEqual(shifted[-1], {"date": "2021-06-26", "value": 50})
        self.assertEqual(retained[0], {"date": "2021-07-03", "value": 58})
        dates = [date.fromisoformat(point["date"]) for point in shifted + retained]
        self.assertEqual(len(dates), 522)
        self.assertTrue(all((b - a).days == 7 for a, b in zip(dates, dates[1:])))


if __name__ == "__main__":
    unittest.main()
