#!/usr/bin/env python3
"""Tests for gated passport-cover review / dual license-deployment status."""

from __future__ import annotations

import json
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

import passport_cover_config as cfg  # noqa: E402
import render_passport_pages as pages  # noqa: E402

COMPETITOR_DOMAINS = (
    "passportindex.org",
    "visaindex.com",
    "henleyglobal.com",
    "henley-partners.com",
    "pinterest.com",
    "pinimg.com",
)


class PassportCoverReviewGateTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.manifest_path = ROOT / "source-data" / "passport-covers" / "manifest.json"
        cls.covers_path = ROOT / "public" / "data" / "passports" / "covers.json"
        if not cls.manifest_path.is_file():
            raise unittest.SkipTest("manifest missing")
        cls.manifest = json.loads(cls.manifest_path.read_text(encoding="utf-8"))
        cls.entries = cls.manifest["entries"]
        cls.covers = (
            json.loads(cls.covers_path.read_text(encoding="utf-8"))
            if cls.covers_path.is_file()
            else {"covers": {}, "count": 0}
        )
        cls.js = pages.JS

    def test_exactly_199_manifest_entries(self) -> None:
        self.assertEqual(len(self.entries), 199)

    def test_gate_is_false(self) -> None:
        self.assertFalse(cfg.REAL_PASSPORT_COVERS_ENABLED)
        self.assertIn("REAL_PASSPORT_COVERS_ENABLED=false", self.js)

    def test_no_public_real_cover_references_while_gated(self) -> None:
        self.assertEqual(self.covers.get("count"), 0)
        self.assertEqual(self.covers.get("covers"), {})
        public_webps = list((ROOT / "public" / "assets" / "passports").glob("*.webp"))
        self.assertEqual(public_webps, [])
        # JS must not emit public cover URLs when gate is off
        self.assertIn("REAL_PASSPORT_COVERS_ENABLED=false", self.js)
        compact = self.js.replace(" ", "").replace("\n", "")
        self.assertIn("if(!REAL_PASSPORT_COVERS_ENABLED)returnnull", compact)

    def test_unresolved_deployment_cannot_appear_publicly(self) -> None:
        for entry in self.entries:
            if entry.get("deploymentStatus") in {
                "emblem_review_required",
                "editorial_review_required",
                "blocked",
            }:
                self.assertIsNone(entry.get("localFile"))
            if entry.get("emblemRightsReviewRequired"):
                self.assertNotEqual(entry.get("deploymentStatus"), "cleared")

    def test_visually_approved_require_review_flag(self) -> None:
        for entry in self.entries:
            if (
                entry.get("imageLicenseStatus") == "approved"
                and entry.get("currentnessConfidence") == "high"
                and entry.get("displayDecision") == "staged_photo"
            ):
                self.assertTrue(entry.get("visuallyReviewed"), entry["iso3"])
                self.assertTrue(entry.get("currentnessEvidenceUrl"), entry["iso3"])

    def test_no_competitor_domains_as_sources(self) -> None:
        for entry in self.entries:
            for field in (
                "commonsPageUrl",
                "originalFileUrl",
                "sourcePage",
                "currentnessEvidenceUrl",
                "attributionText",
            ):
                val = (entry.get(field) or "").lower()
                for domain in COMPETITOR_DOMAINS:
                    self.assertNotIn(domain, val, f"{entry['iso3']} {field}")
            for cand in entry.get("candidates") or []:
                url = (cand.get("originalFileUrl") or "").lower()
                page = (cand.get("commonsPageUrl") or "").lower()
                for domain in COMPETITOR_DOMAINS:
                    self.assertNotIn(domain, url)
                    self.assertNotIn(domain, page)
                if url:
                    self.assertTrue(
                        "wikimedia.org" in url or "wikipedia.org" in url,
                        url,
                    )
                # Competitor strings may appear only on rejected/ineligible candidates.
                author = str(cand.get("author") or "").lower()
                for domain in COMPETITOR_DOMAINS:
                    if domain in author:
                        self.assertFalse(cand.get("eligible"))
                        self.assertNotEqual(entry.get("displayDecision"), "staged_photo")

    def test_no_personal_data_page_as_display_photo(self) -> None:
        for entry in self.entries:
            if entry.get("objectClass") == "identity_or_data_page":
                self.assertNotEqual(entry.get("displayDecision"), "staged_photo")
                self.assertIsNone(entry.get("localFile"))

    def test_fallback_strings_present(self) -> None:
        self.assertIn("not an official reproduction", self.js)
        self.assertIn("تصميم توضيحي من مرآة — ليس صورة رسمية", self.js)
        self.assertIn("ليس صورة رسمية", self.js)
        self.assertIn("emblemSvg", self.js)
        self.assertIn("gold-type", self.js)

    def test_scores_and_dashboard_unchanged(self) -> None:
        malta = json.loads(
            (ROOT / "public" / "data" / "passports" / "by-code" / "MLT.json").read_text(
                encoding="utf-8"
            )
        )
        self.assertEqual(malta["mobilityScore"], 159)
        self.assertEqual(malta["rank"], 6)
        a = (ROOT / "public" / "index.html").read_bytes()
        b = (ROOT / "public" / "dashboard.html").read_bytes()
        self.assertEqual(a, b)

    def test_review_tool_outside_public(self) -> None:
        tool = ROOT / "source-data" / "passport-covers" / "review" / "tool" / "index.html"
        readme = ROOT / "source-data" / "passport-covers" / "review" / "tool" / "README.md"
        # Tool may be built later in the pass; if present, must not live under public/
        if tool.is_file():
            self.assertTrue(readme.is_file())
            self.assertNotIn("public", str(tool.relative_to(ROOT)).split("\\")[0])
            text = tool.read_text(encoding="utf-8")
            self.assertIn("NOT FOR DEPLOY", text)


if __name__ == "__main__":
    unittest.main()
