#!/usr/bin/env python3
"""Homepage + route-migration tests for Mir’ah platform."""
from __future__ import annotations

import re
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PUBLIC = ROOT / "public"
SCRIPTS = ROOT / "scripts"


class HomepageRouteTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.home = (PUBLIC / "index.html").read_text(encoding="utf-8")
        cls.compare = (PUBLIC / "compare" / "index.html").read_text(encoding="utf-8")
        cls.dashboard = (PUBLIC / "dashboard.html").read_text(encoding="utf-8")
        cls.passport = (PUBLIC / "passport" / "index.html").read_text(encoding="utf-8")
        cls.malta = (PUBLIC / "passport" / "malta" / "index.html").read_text(encoding="utf-8")
        cls.sitemap = (PUBLIC / "sitemap.xml").read_text(encoding="utf-8")

    def test_home_is_not_comparison_tool(self):
        self.assertIn("home-hero", self.home)
        self.assertIn("HOME_BOOT", self.home)
        self.assertIn("العالم في مرآة", self.home)
        self.assertIn("See the world in one mirror", self.home)
        self.assertNotIn("countrySearchA", self.home)
        self.assertNotIn("id=\"kpis\"", self.home)

    def test_compare_is_comparison_tool(self):
        self.assertIn("countrySearchA", self.compare)
        self.assertIn("const DATA=", self.compare)
        self.assertIn("/compare/", self.compare)
        self.assertIn('rel="canonical" href="https://miraah.mirapp.workers.dev/compare/"', self.compare)

    def test_dashboard_alias_matches_compare(self):
        self.assertEqual(
            (PUBLIC / "compare" / "index.html").read_bytes(),
            (PUBLIC / "dashboard.html").read_bytes(),
        )
        self.assertIn("/compare/", self.dashboard)
        self.assertIn("location.replace('/compare/'", self.dashboard)

    def test_home_not_byte_identical_to_dashboard(self):
        self.assertNotEqual(
            (PUBLIC / "index.html").read_bytes(),
            (PUBLIC / "dashboard.html").read_bytes(),
        )

    def test_nav_links_root_relative(self):
        for label, html in (
            ("home", self.home),
            ("compare", self.compare),
            ("passport", self.passport),
            ("malta", self.malta),
        ):
            with self.subTest(label):
                self.assertIn('href="/" id="navHome"', html)
                self.assertIn('href="/compare/" id="navCompare"', html)
                self.assertIn('href="/passport/" id="navPassport"', html)

    def test_aria_current_pages(self):
        self.assertIn('id="navHome" aria-current="page"', self.home)
        self.assertIn('id="navCompare" aria-current="page"', self.compare)
        self.assertIn('id="navPassport" aria-current="page"', self.passport)

    def test_homepage_ctas(self):
        self.assertIn('href="/compare/" id="ctaCompare"', self.home)
        self.assertIn('href="/passport/" id="ctaPassport"', self.home)

    def test_leading_passports_from_real_data(self):
        self.assertIn("/passport/united-arab-emirates/", self.home)
        self.assertIn("expRank:'Experimental Mir", self.home)
        self.assertIn("ترتيب مرآة التجريبي", self.home)
        self.assertNotIn("global ranking", self.home.lower())
        self.assertNotIn("الترتيب العالمي لجواز", self.home)

    def test_no_real_covers_enabled(self):
        self.assertNotIn("REAL_PASSPORT_COVERS_ENABLED=true", self.home.lower())
        js = (PUBLIC / "passport" / "assets" / "passport.js").read_text(encoding="utf-8")
        self.assertIn("REAL_PASSPORT_COVERS_ENABLED", js)
        self.assertRegex(js, r"REAL_PASSPORT_COVERS_ENABLED\s*=\s*false")

    def test_seo_canonicals_unique(self):
        self.assertIn('rel="canonical" href="https://miraah.mirapp.workers.dev/"', self.home)
        self.assertIn('rel="canonical" href="https://miraah.mirapp.workers.dev/compare/"', self.compare)
        self.assertIn('content="index, follow"', self.home)
        self.assertIn('content="index, follow"', self.compare)
        self.assertIn('content="noindex, follow"', self.passport)
        self.assertIn('content="noindex, follow"', self.malta)

    def test_sitemap_home_and_compare_only(self):
        self.assertIn("<loc>https://miraah.mirapp.workers.dev/</loc>", self.sitemap)
        self.assertIn("<loc>https://miraah.mirapp.workers.dev/compare/</loc>", self.sitemap)
        self.assertNotIn("/passport/", self.sitemap)

    def test_google_verification_present(self):
        ver = PUBLIC / "google8f06f6f6524f6c30.html"
        self.assertTrue(ver.is_file())
        self.assertIn("google-site-verification", ver.read_text(encoding="utf-8"))

    def test_theme_and_lang_wiring(self):
        passport_js = (PUBLIC / "passport" / "assets" / "passport.js").read_text(encoding="utf-8")
        for html in (self.home, self.compare):
            self.assertIn("miraahTheme", html)
            self.assertIn("miraahLang", html)
            self.assertIn("themeBtn", html)
            self.assertIn("data-theme", html)
        self.assertIn("miraahTheme", self.passport)
        self.assertIn("themeBtn", self.passport)
        self.assertIn("miraahLang", passport_js)
        self.assertIn("miraahTheme", passport_js)

    def test_counts_match_datasets(self):
        self.assertIn(">217<", self.home)
        self.assertIn(">12<", self.home)
        self.assertIn(">199<", self.home)
        self.assertIn(">198<", self.home)

    def test_generators_wired(self):
        home_gen = (SCRIPTS / "render_homepage.py").read_text(encoding="utf-8")
        dash = (SCRIPTS / "render_dashboard.py").read_text(encoding="utf-8")
        wb = (SCRIPTS / "update_world_bank.py").read_text(encoding="utf-8")
        self.assertIn("INDEX_OUT", home_gen)
        self.assertIn('COMPARE = ROOT / "public" / "compare"', dash)
        self.assertNotIn('INDEX = ROOT / "public" / "index.html"', dash)
        self.assertIn("HOMEPAGE", wb)
        self.assertIn("compare/index.html", wb)
        self.assertIn("Never overwrite the platform homepage", wb)


class HomepageUnitTests(unittest.TestCase):
    def test_leading_passports_helper(self):
        import sys

        sys.path.insert(0, str(SCRIPTS))
        import render_homepage as home

        sample = {
            "passports": [
                {
                    "slug": "a",
                    "iso3": "AAA",
                    "nameEn": "A",
                    "nameAr": "أ",
                    "rank": 1,
                    "mobilityScore": 10,
                    "categoryTotals": {"visa_free": 5, "visa_on_arrival": 1, "eta": 0, "evisa": 0},
                }
            ]
        }
        rows = home.leading_passports(sample, n=1)
        self.assertEqual(rows[0]["slug"], "a")
        self.assertEqual(rows[0]["visaFree"], 5)


if __name__ == "__main__":
    unittest.main()
