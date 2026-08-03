#!/usr/bin/env python3
"""Tests for passport-cover licensing pipeline and UI integration."""

from __future__ import annotations

import hashlib
import json
import re
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

import audit_passport_covers as covers  # noqa: E402
import render_passport_pages as pages  # noqa: E402

COMPETITOR_DOMAINS = (
    "passportindex.org",
    "visaindex.com",
    "henleyglobal.com",
    "henley-partners.com",
    "pinterest.com",
    "pinimg.com",
)

ALLOWED_LICENSE = re.compile(
    r"^(public domain|pd\b|cc0|cc[\s\-]?zero|cc[\s\-]?by(?![\s\-]?nc)(?![\s\-]?nd))",
    re.I,
)


class PassportCoverPipelineTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.manifest_path = ROOT / "source-data" / "passport-covers" / "manifest.json"
        cls.index_path = ROOT / "public" / "data" / "passports" / "index.json"
        if not cls.index_path.is_file():
            raise unittest.SkipTest("passport index missing")
        cls.index = json.loads(cls.index_path.read_text(encoding="utf-8"))
        cls.passports = cls.index["passports"]
        if cls.manifest_path.is_file():
            cls.manifest = json.loads(cls.manifest_path.read_text(encoding="utf-8"))
            cls.entries = cls.manifest.get("entries") or []
        else:
            cls.manifest = None
            cls.entries = []
        covers_path = ROOT / "public" / "data" / "passports" / "covers.json"
        cls.covers = (
            json.loads(covers_path.read_text(encoding="utf-8"))
            if covers_path.is_file()
            else {"covers": {}}
        )
        cls.js = pages.JS
        cls.css = pages.CSS

    def test_exactly_199_passports_in_index(self) -> None:
        self.assertEqual(len(self.passports), 199)

    def test_manifest_has_exactly_199_entries_when_present(self) -> None:
        if not self.entries:
            self.skipTest("manifest not generated yet")
        self.assertEqual(len(self.entries), 199)
        iso3 = {e["iso3"] for e in self.entries}
        expected = {p["iso3"] for p in self.passports}
        self.assertEqual(iso3, expected)

    def test_approved_assets_have_local_files_and_attribution(self) -> None:
        if not self.entries:
            self.skipTest("manifest not generated yet")
        import passport_cover_config as cover_cfg

        hashes: dict[str, str] = {}
        for entry in self.entries:
            # Legacy status==approved OR dual imageLicenseStatus with staged asset
            licensed = entry.get("imageLicenseStatus") == "approved" or entry.get("status") == "approved"
            if not licensed:
                continue
            # While public gate is off, files may only exist under staged/, never public localFile.
            if not cover_cfg.REAL_PASSPORT_COVERS_ENABLED:
                self.assertIsNone(entry.get("localFile"), entry["iso3"])
                for key in ("author", "licenseName", "attributionText", "commonsPageUrl"):
                    # Some license-approved legacy rows may lack full attribution until visual package completes.
                    if entry.get("currentnessConfidence") == "high" and entry.get("visuallyReviewed"):
                        self.assertTrue(entry.get(key), f"{entry['iso3']} missing {key}")
                self.assertTrue(
                    ALLOWED_LICENSE.search(entry.get("licenseName") or "")
                    or (entry.get("licenseName") or "").lower().startswith("public domain")
                    or (entry.get("licenseName") or "").lower() in {"pd", "cc0"},
                    entry.get("licenseName"),
                )
                continue
            local = entry.get("localFile")
            self.assertTrue(local, entry["iso3"])
            path = ROOT / "public" / local.lstrip("/")
            self.assertTrue(path.is_file(), f"missing {path}")
            self.assertLessEqual(path.stat().st_size, covers.MAX_DERIV_BYTES)
            raw = path.read_bytes()
            digest = hashlib.sha256(raw).hexdigest()
            self.assertEqual(entry.get("fileHash"), digest)
            if digest in hashes and hashes[digest] != entry["iso3"]:
                self.fail(
                    f"duplicate hash {digest} mapped to {hashes[digest]} and {entry['iso3']}"
                )
            hashes[digest] = entry["iso3"]
            for key in (
                "commonsPageUrl",
                "originalFileUrl",
                "author",
                "licenseName",
                "attributionText",
            ):
                self.assertTrue(entry.get(key), f"{entry['iso3']} missing {key}")
            self.assertTrue(
                ALLOWED_LICENSE.search(entry["licenseName"] or ""),
                entry["licenseName"],
            )
            self.assertTrue(entry.get("emblemRightsReviewRequired"))
            res = entry.get("resolution") or {}
            self.assertGreaterEqual(res.get("width") or 0, covers.MIN_WIDTH)
            self.assertGreaterEqual(res.get("height") or 0, covers.MIN_HEIGHT)

    def test_runtime_covers_json_only_lists_existing_local_files(self) -> None:
        for iso3, meta in (self.covers.get("covers") or {}).items():
            path = ROOT / "public" / meta["localFile"].lstrip("/")
            self.assertTrue(path.is_file(), iso3)
            self.assertFalse(meta["localFile"].startswith("http"))
            blob = json.dumps(meta).lower()
            for domain in COMPETITOR_DOMAINS:
                self.assertNotIn(domain, blob)

    def test_no_external_runtime_image_urls_in_passport_js(self) -> None:
        self.assertIn("cover.localFile", self.js)
        self.assertIn('loading="lazy"', self.js)
        self.assertNotIn("upload.wikimedia.org", self.js)
        self.assertNotIn("passportindex.org", self.js)
        for domain in COMPETITOR_DOMAINS:
            self.assertNotIn(domain, self.js)

    def test_fallback_and_attribution_ui_strings(self) -> None:
        self.assertIn("miraahIllustration", self.js)
        self.assertIn("Mir\\u2019ah illustration", self.js)
        self.assertIn("تصميم توضيحي من مرآة", self.js)
        self.assertIn("ليس صورة رسمية", self.js)
        self.assertIn("imageAttr", self.js)
        self.assertIn("coverAttribution", self.js)
        self.assertIn("methodImageAttrBody", self.js)
        self.assertIn("passport-fallback-note", self.css)
        self.assertIn("object-fit:contain", self.css)

    def test_selected_cover_only_loads_via_img_tag(self) -> None:
        # Landing must not preload every cover; img is created only in renderPassportBook.
        self.assertIn("function renderPassportBook", self.js)
        self.assertIn("<img src=", self.js)
        self.assertNotIn("preload", self.js.lower())

    def test_attributions_page_exists_when_generated(self) -> None:
        path = ROOT / "public" / "passport" / "image-attributions.html"
        if not path.is_file():
            self.skipTest("attributions page not generated yet")
        text = path.read_text(encoding="utf-8")
        self.assertIn("Passport cover image attributions", text)
        self.assertIn("التزامات الترخيص", text)
        self.assertIn("Mir’ah illustration", text)
        self.assertIn("رسم توضيحي من مرآة", text)
        for domain in COMPETITOR_DOMAINS:
            self.assertNotIn(domain, text.lower())

    def test_license_helper_allowlist(self) -> None:
        ok, _ = covers.license_allowed("CC BY-SA 4.0")
        self.assertTrue(ok)
        ok, _ = covers.license_allowed("CC BY 3.0")
        self.assertTrue(ok)
        ok, _ = covers.license_allowed("CC0")
        self.assertTrue(ok)
        ok, reason = covers.license_allowed("CC BY-NC 4.0")
        self.assertFalse(ok)
        self.assertTrue(reason)
        ok, _ = covers.license_allowed("All rights reserved")
        self.assertFalse(ok)

    def test_scores_unchanged_sample(self) -> None:
        malta = json.loads(
            (ROOT / "public" / "data" / "passports" / "by-code" / "MLT.json").read_text(
                encoding="utf-8"
            )
        )
        self.assertEqual(malta["mobilityScore"], 159)
        self.assertEqual(malta["rank"], 6)

    def test_dashboard_byte_identical(self) -> None:
        a = (ROOT / "public" / "index.html").read_bytes()
        b = (ROOT / "public" / "dashboard.html").read_bytes()
        self.assertEqual(a, b)

    def test_claim_coverage_honesty(self) -> None:
        if not self.entries:
            self.skipTest("manifest not generated yet")
        approved = sum(1 for e in self.entries if e.get("status") == "approved")
        # Never imply full coverage unless truly complete and files exist.
        if approved < 199:
            audit = (ROOT / "source-data" / "passport-covers" / "AUDIT.md").read_text(
                encoding="utf-8"
            )
            self.assertNotIn("199/199", audit)


if __name__ == "__main__":
    unittest.main()
