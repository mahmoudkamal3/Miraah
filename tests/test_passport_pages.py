#!/usr/bin/env python3
"""Tests for passport page rendering, SEO, sitemap, and dashboard regression."""

from __future__ import annotations

import json
import sys
import unittest
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.request import urlopen

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

import render_passport_pages as pages  # noqa: E402


FORBIDDEN_RANK_CLAIMS = [
    "Global rank",
    "global rank",
    "الترتيب العالمي",
    "Passport rank",
    "ترتيب جواز السفر",
    "official rank",
    "Henley",
    "IATA",
]


class PassportPagesTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        index_path = ROOT / "public" / "data" / "passports" / "index.json"
        if not index_path.is_file():
            raise unittest.SkipTest("passport data not generated")
        cls.index = json.loads(index_path.read_text(encoding="utf-8"))
        cls.passports = cls.index["passports"]
        cls.js = (ROOT / "public" / "passport" / "assets" / "passport.js").read_text(
            encoding="utf-8"
        )
        cls.css = (ROOT / "public" / "passport" / "assets" / "passport.css").read_text(
            encoding="utf-8"
        )

    def test_all_passport_detail_files_exist_for_slugs(self) -> None:
        missing = []
        for passport in self.passports:
            path = ROOT / "public" / "passport" / passport["slug"] / "index.html"
            if not path.is_file():
                missing.append(passport["slug"])
        self.assertEqual(missing, [])
        self.assertEqual(len(self.passports), 199)

    def test_js_uses_root_relative_passport_links(self) -> None:
        self.assertIn("/passport/${encodeURIComponent(p.slug)}/", self.js)
        self.assertNotIn("./${p.slug}", self.js)
        self.assertNotIn("`./${", self.js)

    def test_no_unqualified_global_rank_or_iata_claims(self) -> None:
        landing = (ROOT / "public" / "passport" / "index.html").read_text(encoding="utf-8")
        sample = self.passports[0]
        page = (
            ROOT / "public" / "passport" / sample["slug"] / "index.html"
        ).read_text(encoding="utf-8")
        blob = "\n".join([landing, page, self.js, pages.JS, pages.CSS])
        for claim in FORBIDDEN_RANK_CLAIMS:
            self.assertNotIn(claim, blob)

    def test_visible_source_wording(self) -> None:
        self.assertIn("Passport Index Data", self.js)
        self.assertIn("Source and methodology details", self.js)
        self.assertIn("تفاصيل المصدر والمنهجية", self.js)
        self.assertIn("Experimental data; verify with an embassy or airline before travel.", self.js)
        self.assertIn("بيانات تجريبية؛ تحقّق من السفارة أو شركة الطيران قبل السفر.", self.js)
        self.assertIn("imorte/passport-index-data", self.js)
        self.assertIn("not produced by Mir", self.js)

    def test_coverage_and_methodology_wording(self) -> None:
        self.assertIn("Experimental Mir\\u2019ah rank", self.js)
        self.assertIn("Mir\\u2019ah Mobility Score", self.js)
        self.assertIn(
            "Calculated across 199 passports and 198 travel destinations", self.js
        )
        self.assertIn("ترتيب مرآة التجريبي", self.js)
        self.assertIn("درجة التنقل في مرآة", self.js)
        self.assertIn("محسوب بين 199 جواز سفر وعبر 198 وجهة سفر", self.js)
        self.assertIn("Showing ${x} of ${y} destinations", self.js)
        self.assertIn("عرض ${x} من ${y} وجهة", self.js)
        self.assertIn("passport-book", self.css)
        self.assertIn("clamp(", self.css)
        self.assertIn("tabular-nums", self.css)
        self.assertNotIn("Interactive SVG world map is planned", self.js)
        self.assertNotIn("Interactive SVG world map is planned", pages.JS)

    def test_arabic_region_translations(self) -> None:
        self.assertIn("شرق آسيا والمحيط الهادئ", self.js)
        self.assertIn("أوروبا وآسيا الوسطى", self.js)
        self.assertIn("الشرق الأوسط وشمال أفريقيا", self.js)
        self.assertIn("REGION_LABELS", self.js)

    def test_home_excluded_from_filters(self) -> None:
        self.assertIn("CAT_FILTER_ORDER", self.js)
        self.assertIn("d.status!=='home'", self.js.replace(" ", ""))
        # home still in category order for cards
        self.assertIn("'home'", self.js)

    def test_generated_routes_use_noindex(self) -> None:
        landing_html = (ROOT / "public" / "passport" / "index.html").read_text(
            encoding="utf-8"
        )
        self.assertIn('name="robots" content="noindex, follow"', landing_html)
        malta = (
            ROOT / "public" / "passport" / "malta" / "index.html"
        ).read_text(encoding="utf-8")
        self.assertIn('name="robots" content="noindex, follow"', malta)
        self.assertIn(
            'rel="canonical" href="https://miraah.mirapp.workers.dev/passport/malta/"',
            malta,
        )

    def test_sitemap_excludes_passport_routes(self) -> None:
        sitemap = (ROOT / "public" / "sitemap.xml").read_text(encoding="utf-8")
        self.assertIn("https://miraah.mirapp.workers.dev/</loc>", sitemap)
        self.assertNotIn("/passport/", sitemap)
        self.assertEqual(sitemap.count("<url>"), 1)

    def test_homepage_remains_index_follow(self) -> None:
        home = (ROOT / "public" / "index.html").read_text(encoding="utf-8")
        self.assertIn('name="robots" content="index, follow"', home)

    def test_dashboard_files_remain_byte_identical(self) -> None:
        a = (ROOT / "public" / "index.html").read_bytes()
        b = (ROOT / "public" / "dashboard.html").read_bytes()
        self.assertEqual(a, b)

    def test_score_and_category_invariants_for_all_passports(self) -> None:
        by_code = ROOT / "public" / "data" / "passports" / "by-code"
        for path in by_code.glob("*.json"):
            payload = json.loads(path.read_text(encoding="utf-8"))
            totals = payload["categoryTotals"]
            self.assertEqual(sum(totals.values()), 199, path.name)
            mobility = (
                totals["visa_free"] + totals["visa_on_arrival"] + totals["eta"]
            )
            self.assertEqual(mobility, payload["mobilityScore"], path.name)

    def test_malta_invariant_unchanged(self) -> None:
        malta = json.loads(
            (ROOT / "public" / "data" / "passports" / "by-code" / "MLT.json").read_text(
                encoding="utf-8"
            )
        )
        totals = malta["categoryTotals"]
        self.assertEqual(totals["visa_free"], 123)
        self.assertEqual(totals["visa_on_arrival"], 25)
        self.assertEqual(totals["eta"], 11)
        self.assertEqual(malta["mobilityScore"], 159)
        self.assertEqual(sum(totals.values()), 199)
        self.assertEqual(malta["slug"], "malta")
        self.assertEqual(malta["rank"], 6)

    def test_filter_counts_match_category_totals(self) -> None:
        for code in ("MLT", "SGP", "EGY"):
            payload = json.loads(
                (ROOT / "public" / "data" / "passports" / "by-code" / f"{code}.json").read_text(
                    encoding="utf-8"
                )
            )
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
            self.assertEqual(travel + totals["home"], 199)
            self.assertEqual(travel, 198)
            counted = {
                status: 0
                for status in (
                    "visa_free",
                    "visa_on_arrival",
                    "eta",
                    "evisa",
                    "visa_required",
                    "no_admission",
                    "home",
                )
            }
            for dest in payload["destinations"]:
                counted[dest["status"]] += 1
            self.assertEqual(counted, totals)


if __name__ == "__main__":
    unittest.main()
