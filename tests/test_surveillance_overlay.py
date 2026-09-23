import copy
import json
import sys
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
import build_surveillance_section as builder


class OverlaySeasonTests(unittest.TestCase):
    def setUp(self):
        self.cache = {}
        for spec in builder.SYSTEMS:
            for season, aggregate_value in [("2021/22", 2), ("2022/23", 11), ("2024/25", 6)]:
                for week in range(1, 13):
                    for filename, location, value in [
                        (spec["geoFile"], "California", week - 1),
                        (spec["mainFile"], spec["mainLocation"], aggregate_value),
                    ]:
                        self.cache.setdefault(filename, []).append({
                            "state": location,
                            "season": season,
                            "week_axis": str(week),
                            "value": str(value),
                        })

    def test_excludes_season_from_individual_curves_and_summary(self):
        for system in builder.normalized_overlay(self.cache)["systems"]:
            with self.subTest(system=system["id"]):
                self.assertEqual({c["season"] for c in system["curves"]}, {"2021/22", "2024/25"})
                self.assertEqual(system["curveCount"], 2)
                self.assertEqual(system["seasonCount"], 2)
                self.assertEqual(system["summarySeasonCount"], 2)
                self.assertEqual(system["summaryMinimumSeasons"], 2)
                self.assertEqual(system["summary"], [[x, round(4 / 11, 4)] for x in range(1, 13)])

    def test_other_slides_and_source_rows_keep_the_season(self):
        original = copy.deepcopy(self.cache)
        builder.normalized_overlay(self.cache)
        self.assertEqual(self.cache, original)
        for spec in builder.SYSTEMS:
            with self.subTest(system=spec["id"]):
                payload = builder.system_payload(spec, self.cache)
                self.assertIn("2022/23", {c["season"] for c in payload["seasons"]})

    def test_built_slide_excludes_season_and_counts_match(self):
        html = (ROOT / "docs" / "slide-11.html").read_text()
        data, _ = json.JSONDecoder().raw_decode(html.split("const data = ", 1)[1])
        for system in data["systems"]:
            with self.subTest(system=system["id"]):
                seasons = {c["season"] for c in system["curves"]}
                self.assertNotIn("2022/23", seasons)
                self.assertEqual(system["curveCount"], len(system["curves"]))
                self.assertEqual(system["seasonCount"], len(seasons))


if __name__ == "__main__":
    unittest.main()
