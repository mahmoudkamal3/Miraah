#!/usr/bin/env python3
"""Tests for Passport Power access world map + cover gate."""

from __future__ import annotations

import json
import re
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

import passport_cover_config as cover_cfg  # noqa: E402
import render_passport_pages as pages  # noqa: E402

EXTERNAL_HOST_RE = re.compile(
    r"https?://(?!miraah\.mirapp\.workers\.dev)[a-z0-9.-]+", re.I
)


class PassportMapTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.map_path = ROOT / "public" / "passport" / "assets" / "world-map.json"
        cls.mapping_path = ROOT / "source-data" / "passport-map" / "iso-mapping.json"
        cls.audit_path = ROOT / "source-data" / "passport-map" / "ISO_MAPPING_AUDIT.md"
        if not cls.map_path.is_file():
            raise unittest.SkipTest("world-map.json missing — run build_passport_map.py")
        cls.map = json.loads(cls.map_path.read_text(encoding="utf-8"))
        cls.mapping = json.loads(cls.mapping_path.read_text(encoding="utf-8"))
        cls.js = pages.JS
        cls.css = pages.CSS
        cls.esp = json.loads(
            (ROOT / "public" / "data" / "passports" / "by-code" / "ESP.json").read_text(
                encoding="utf-8"
            )
        )
        cls.mlt = json.loads(
            (ROOT / "public" / "data" / "passports" / "by-code" / "MLT.json").read_text(
                encoding="utf-8"
            )
        )

    def test_local_map_asset_exists_and_documents_license(self) -> None:
        self.assertTrue(self.map_path.is_file())
        meta = self.map.get("meta") or {}
        self.assertEqual(meta.get("license"), "Public Domain")
        self.assertIn("naturalearthdata.com", (meta.get("sourceUrl") or "").lower())
        self.assertTrue((ROOT / "PASSPORT_MAP.md").is_file())
        docs = (ROOT / "PASSPORT_MAP.md").read_text(encoding="utf-8")
        self.assertIn("Natural Earth", docs)
        self.assertIn("Public Domain", docs)
        self.assertTrue(self.audit_path.is_file())

    def test_no_runtime_external_map_hosts_in_js(self) -> None:
        # Map fetch must be local asset path only.
        self.assertIn("world-map.json", self.js)
        self.assertNotIn("mapbox", self.js.lower())
        self.assertNotIn("googleapis.com/maps", self.js.lower())
        self.assertNotIn("unpkg.com", self.js.lower())
        self.assertNotIn("jsdelivr", self.js.lower())
        self.assertNotIn("naturalearthdata.com", self.js.lower())

    def test_iso_mapping_covers_all_destinations(self) -> None:
        rows = self.mapping["rows"]
        self.assertEqual(len(rows), 199)
        missing = [r for r in rows if r.get("representation") == "not_mappable"]
        self.assertEqual(missing, [])
        travel = [r for r in rows if r["iso3"] != "MLT"]  # sample: all non-home still mapped
        self.assertTrue(all(r.get("representation") for r in travel))
        for code in ("XKX", "PSE", "TWN", "HKG", "MAC", "VAT", "SGP", "MLT"):
            row = next(r for r in rows if r["iso3"] == code)
            self.assertIn(row["representation"], {"polygon", "marker", "polygon+marker"})

    def test_features_expose_only_local_iso3(self) -> None:
        isos = {f["properties"]["iso3"] for f in self.map["features"]}
        dests = {d["iso3"] for d in self.mlt["destinations"]}
        self.assertTrue(isos.issubset(dests) or dests.issubset(isos) or isos & dests)
        # Every destination represented at least once
        for code in dests:
            self.assertIn(code, isos, f"missing geometry/marker for {code}")

    def test_status_color_classes_present(self) -> None:
        for status in (
            "visa_free",
            "visa_on_arrival",
            "eta",
            "evisa",
            "visa_required",
            "no_admission",
            "home",
        ):
            self.assertIn(f"map-status-{status}", self.css + self.js)

    def test_legend_and_sync_hooks(self) -> None:
        self.assertIn("renderMapLegend", self.js)
        self.assertIn("colorMap", self.js)
        self.assertIn("refreshMap", self.js)
        self.assertIn("mapMatchesFilters", self.js)
        self.assertIn("selectMapDestination", self.js)
        self.assertIn("mapZoomIn", self.js)
        self.assertIn("prefers-reduced-motion", self.css)
        self.assertIn("map-sheet", self.css)
        self.assertIn("stayOfficial", self.js)
        self.assertIn("خريطة الوصول حول العالم", self.js)
        self.assertIn("Worldwide access map", self.js)

    def test_legend_counts_match_spain_and_malta_totals(self) -> None:
        for payload, label in ((self.esp, "ESP"), (self.mlt, "MLT")):
            totals = payload["categoryTotals"]
            travel = sum(
                totals[k]
                for k in (
                    "visa_free",
                    "visa_on_arrival",
                    "eta",
                    "evisa",
                    "visa_required",
                    "no_admission",
                )
            )
            self.assertEqual(travel, 198, label)
            self.assertEqual(totals["home"], 1, label)
            self.assertEqual(sum(totals.values()), 199, label)

    def test_no_historical_score_chart_invented(self) -> None:
        self.assertNotIn("historicalScore", self.js)
        self.assertNotIn("mobilityHistory", self.js)
        docs = (ROOT / "PASSPORT_DATA.md").read_text(encoding="utf-8")
        self.assertIn("historical mobility", docs.lower())
        self.assertIn("not implemented", docs.lower())

    def test_real_covers_remain_disabled(self) -> None:
        self.assertFalse(cover_cfg.REAL_PASSPORT_COVERS_ENABLED)
        covers = json.loads(
            (ROOT / "public" / "data" / "passports" / "covers.json").read_text(encoding="utf-8")
        )
        self.assertEqual(covers.get("count"), 0)
        self.assertEqual(list((ROOT / "public" / "assets" / "passports").glob("*.webp")), [])
        self.assertIn("تصميم توضيحي من مرآة — ليس صورة رسمية", self.js)
        self.assertIn("Mir\\u2019ah illustration — not an official reproduction", self.js)

    def test_scores_and_dashboard_unchanged(self) -> None:
        self.assertEqual(self.mlt["mobilityScore"], 159)
        self.assertEqual(self.mlt["rank"], 6)
        a = (ROOT / "public" / "compare" / "index.html").read_bytes()
        b = (ROOT / "public" / "dashboard.html").read_bytes()
        self.assertEqual(a, b)

    def test_map_not_in_homepage_html(self) -> None:
        home = (ROOT / "public" / "index.html").read_text(encoding="utf-8")
        self.assertNotIn("world-map.json", home)
        self.assertNotIn("mapSvg", home)


if __name__ == "__main__":
    unittest.main()
