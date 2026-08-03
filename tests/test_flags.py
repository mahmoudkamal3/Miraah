#!/usr/bin/env python3
"""Tests for local Mir’ah SVG flag assets and UI wiring."""
from __future__ import annotations

import json
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PUBLIC = ROOT / "public"
SCRIPTS = ROOT / "scripts"
FLAGS = PUBLIC / "assets" / "flags"


class FlagAssetTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        import sys

        sys.path.insert(0, str(SCRIPTS))
        import miraah_flags as flags

        cls.flags = flags
        cls.index = json.loads(
            (PUBLIC / "data" / "passports" / "index.json").read_text(encoding="utf-8")
        )
        sample = json.loads(
            (PUBLIC / "data" / "passports" / "by-code" / "MLT.json").read_text(
                encoding="utf-8"
            )
        )
        cls.destinations = sample["destinations"]

    def test_license_and_source_docs(self):
        self.assertTrue((FLAGS / "LICENSE").is_file())
        self.assertTrue((FLAGS / "SOURCE.txt").is_file())
        src = (FLAGS / "SOURCE.txt").read_text(encoding="utf-8")
        self.assertIn("flag-icons", src)
        self.assertIn("7.5.0", src)
        self.assertIn("MIT", src)

    def test_fallback_exists(self):
        self.assertTrue((FLAGS / "_fallback.svg").is_file())
        self.assertNotIn("JPN", (FLAGS / "_fallback.svg").read_text(encoding="utf-8"))

    def test_all_passport_and_destination_flags_exist(self):
        codes = self.flags.required_iso2_codes(
            self.index["passports"], self.destinations
        )
        missing = self.flags.missing_flag_codes(codes)
        self.assertEqual(missing, [], f"Missing flags: {missing}")
        self.assertGreaterEqual(len(codes), 199)

    def test_key_countries_resolve(self):
        mapping = {
            "MLT": "mt",
            "JPN": "jp",
            "SGP": "sg",
            "ARE": "ae",
            "AZE": "az",
            "XKX": "xk",
            "PSE": "ps",
            "TWN": "tw",
            "HKG": "hk",
            "MAC": "mo",
            "VAT": "va",
        }
        by_iso3 = {p["iso3"]: p for p in self.index["passports"]}
        for iso3, iso2 in mapping.items():
            with self.subTest(iso3=iso3):
                self.assertIn(iso3, by_iso3)
                self.assertEqual(by_iso3[iso3]["iso2"].lower(), iso2)
                self.assertTrue(self.flags.flag_exists(iso2))
                url = self.flags.flag_url(iso2)
                self.assertTrue(url.startswith("/assets/flags/"))
                self.assertTrue(url.endswith(f"{iso2}.svg"))


class FlagHtmlWiringTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.home = (PUBLIC / "index.html").read_text(encoding="utf-8")
        cls.passport_js = (PUBLIC / "passport" / "assets" / "passport.js").read_text(
            encoding="utf-8"
        )
        cls.passport_css = (PUBLIC / "passport" / "assets" / "passport.css").read_text(
            encoding="utf-8"
        )
        cls.azerbaijan = (
            PUBLIC / "passport" / "azerbaijan" / "index.html"
        ).read_text(encoding="utf-8")
        cls.malta = (PUBLIC / "passport" / "malta" / "index.html").read_text(
            encoding="utf-8"
        )

    def test_homepage_cards_use_flags_not_iso_artwork(self):
        self.assertIn("/assets/flags/", self.home)
        self.assertIn("flag-stage", self.home)
        self.assertIn("miraah-flag", self.home)
        # Leading cards should not use ISO3 as the main artwork text node pattern
        self.assertNotRegex(
            self.home,
            r'class="pass-illus"[^>]*>\s*[A-Z]{3}\s*<',
        )
        self.assertIn("flagWithNameHtml", self.home)
        self.assertIn("MIRAAH_FLAG_BASE", self.home)

    def test_destination_table_uses_flag_helper(self):
        self.assertIn("flagWithNameHtml(d.iso2,label,'xs')", self.passport_js)
        self.assertIn("flagImgHtml", self.passport_js)
        self.assertNotIn("flagEmoji", self.passport_js)
        self.assertIn(".miraah-flag", self.passport_css)
        self.assertIn(".flag-xs", self.passport_css)
        self.assertIn(".flag-hero", self.passport_css)

    def test_detail_identity_panel(self):
        self.assertIn('id="passportIdentity"', self.azerbaijan)
        self.assertIn("renderIdentity", self.passport_js)
        self.assertIn("flagImgHtml(p.iso2,label,'hero'", self.passport_js)
        # Nested pages still use root-relative flag URLs
        self.assertIn("/assets/flags/", self.passport_js)
        self.assertNotIn("../assets/flags/", self.passport_js)

    def test_no_emoji_flag_generator(self):
        self.assertNotIn("fromCodePoint", self.passport_js)
        self.assertNotIn("127397", self.passport_js)

    def test_root_relative_paths_documented(self):
        for html in (self.home, self.malta, self.azerbaijan):
            self.assertIn("/assets/flags/", html if "/assets/flags/" in html else self.passport_js)

    def test_scores_unchanged_sample(self):
        malta = json.loads(
            (PUBLIC / "data" / "passports" / "by-code" / "MLT.json").read_text(
                encoding="utf-8"
            )
        )
        self.assertEqual(malta["mobilityScore"], 159)


if __name__ == "__main__":
    unittest.main()
