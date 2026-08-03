#!/usr/bin/env python3
"""Brand identity integration tests for Mir’ah Reflected M."""
from __future__ import annotations

import json
import re
import unittest
import xml.etree.ElementTree as ET
from pathlib import Path

from PIL import Image

ROOT = Path(__file__).resolve().parents[1]
PUBLIC = ROOT / "public"
BRAND = PUBLIC / "assets" / "brand"


class BrandAssetsTests(unittest.TestCase):
    def test_canonical_svgs_exist_and_parse(self):
        for name in (
            "miraah-mark.svg",
            "miraah-mark-mono.svg",
            "miraah-logo-en.svg",
            "miraah-logo-ar.svg",
            "miraah-app-icon.svg",
        ):
            path = BRAND / name
            self.assertTrue(path.exists(), name)
            text = path.read_text(encoding="utf-8")
            self.assertIn("viewBox", text)
            ET.fromstring(text)
            # No illegal XML controls
            for ch in text:
                o = ord(ch)
                if o < 32 and o not in (9, 10, 13):
                    self.fail(f"illegal control in {name}")

    def test_no_alt_concepts_in_production(self):
        banned = ("data-mirror", "mirror-portal", "02-data-mirror", "03-mirror-portal")
        for path in list(PUBLIC.rglob("*.html")) + list(PUBLIC.rglob("*.svg")) + list(
            PUBLIC.rglob("*.js")
        ) + list(PUBLIC.rglob("*.css")) + list(PUBLIC.rglob("*.webmanifest")):
            text = path.read_text(encoding="utf-8", errors="ignore").lower()
            for b in banned:
                self.assertNotIn(b, text, f"{path} contains {b}")

    def test_favicon_and_icon_sizes(self):
        expected = {
            PUBLIC / "favicon-16x16.png": (16, 16),
            PUBLIC / "favicon-32x32.png": (32, 32),
            PUBLIC / "apple-touch-icon.png": (180, 180),
            PUBLIC / "icon-192.png": (192, 192),
            PUBLIC / "icon-512.png": (512, 512),
            BRAND / "miraah-social-card.png": (1200, 630),
        }
        for path, size in expected.items():
            self.assertTrue(path.exists(), path.name)
            im = Image.open(path)
            self.assertEqual(im.size, size, path.name)

    def test_favicon_svg_is_reflected_m(self):
        fav = (PUBLIC / "favicon.svg").read_text(encoding="utf-8")
        mark = (BRAND / "miraah-mark.svg").read_text(encoding="utf-8")
        self.assertIn("viewBox", fav)
        ET.fromstring(fav)
        self.assertIn("M12 51.5", fav)
        self.assertEqual(fav, mark)

    def test_manifest_valid(self):
        data = json.loads((PUBLIC / "site.webmanifest").read_text(encoding="utf-8"))
        self.assertEqual(data["name"], "Mir’ah")
        self.assertEqual(data["short_name"], "Mir’ah")
        self.assertEqual(data["start_url"], "/")
        self.assertEqual(data["display"], "standalone")
        self.assertEqual(data["background_color"], "#07111f")
        self.assertEqual(data["theme_color"], "#07111f")
        sizes = {i["sizes"] for i in data["icons"]}
        self.assertIn("192x192", sizes)
        self.assertIn("512x512", sizes)

    def test_no_generic_globe_favicon(self):
        self.assertFalse((PUBLIC / "globe.svg").exists())
        fav = (PUBLIC / "favicon.svg").read_text(encoding="utf-8")
        self.assertNotIn("earth", fav.lower())
        self.assertNotIn("globe", fav.lower())


class BrandHtmlIntegrationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.index = (PUBLIC / "index.html").read_text(encoding="utf-8")
        cls.dashboard = (PUBLIC / "dashboard.html").read_text(encoding="utf-8")
        cls.passport = (PUBLIC / "passport" / "index.html").read_text(encoding="utf-8")
        cls.malta = (PUBLIC / "passport" / "malta" / "index.html").read_text(encoding="utf-8")

    def test_index_dashboard_byte_identical(self):
        self.assertEqual(
            (PUBLIC / "index.html").read_bytes(),
            (PUBLIC / "dashboard.html").read_bytes(),
        )

    def test_favicon_links_on_all_routes(self):
        for label, html in (
            ("home", self.index),
            ("passport", self.passport),
            ("malta", self.malta),
        ):
            with self.subTest(label):
                self.assertIn('href="/favicon.svg"', html)
                self.assertIn('href="/favicon-16x16.png"', html)
                self.assertIn('href="/favicon-32x32.png"', html)
                self.assertIn('href="/apple-touch-icon.png"', html)
                self.assertIn('href="/site.webmanifest"', html)
                self.assertIn('name="theme-color"', html)

    def test_brand_header_mark_and_home_link(self):
        for label, html in (
            ("home", self.index),
            ("passport", self.passport),
            ("malta", self.malta),
        ):
            with self.subTest(label):
                self.assertIn('id="brandHome"', html)
                self.assertIn('href="/"', html)
                self.assertIn("/assets/brand/miraah-app-icon.svg", html)
                self.assertIn("العودة إلى الصفحة الرئيسية", html)
                # No text-letter logo glyph as brand mark
                self.assertNotRegex(html, r'class="logo">[مM]<')
                self.assertNotIn('class="logo">م<', html)

    def test_no_magnifying_glass_as_brand_mark(self):
        # Search control icons may remain; brand logo must not be ⌕
        for html in (self.index, self.passport, self.malta):
            self.assertNotRegex(html, r'class="logo"[^>]*>\s*⌕')
            self.assertIn("logo-mark", html)

    def test_brand_strings_in_js(self):
        self.assertIn("brand:'مرآة'", self.index)
        self.assertIn("Mir\\u2019ah", self.index)
        passport_js = (PUBLIC / "passport" / "assets" / "passport.js").read_text(encoding="utf-8")
        self.assertIn("brand:'مرآة'", passport_js)
        self.assertIn("Mir\\u2019ah", passport_js)

    def test_og_twitter_jsonld(self):
        for label, html in (
            ("home", self.index),
            ("passport", self.passport),
            ("malta", self.malta),
        ):
            with self.subTest(label):
                self.assertIn(
                    "https://miraah.mirapp.workers.dev/assets/brand/miraah-social-card.png",
                    html,
                )
                self.assertIn("og:image", html)
                self.assertIn("twitter:image", html)
                self.assertIn("application/ld+json", html)
                self.assertIn("/assets/brand/miraah-app-icon.svg", html)

    def test_robots_unchanged_policy(self):
        self.assertIn('content="index, follow"', self.index)
        self.assertIn('content="noindex, follow"', self.passport)
        self.assertIn('content="noindex, follow"', self.malta)

    def test_no_external_font_or_image_cdn(self):
        banned = ("fonts.googleapis.com", "fonts.gstatic.com", "cdn.jsdelivr", "unpkg.com")
        for html in (self.index, self.passport, self.malta):
            low = html.lower()
            for b in banned:
                self.assertNotIn(b, low)

    def test_generated_routes_resolve_brand_assets(self):
        assets = [
            PUBLIC / "favicon.svg",
            PUBLIC / "favicon-16x16.png",
            PUBLIC / "favicon-32x32.png",
            PUBLIC / "apple-touch-icon.png",
            PUBLIC / "icon-192.png",
            PUBLIC / "icon-512.png",
            PUBLIC / "site.webmanifest",
            BRAND / "miraah-mark.svg",
            BRAND / "miraah-app-icon.svg",
            BRAND / "miraah-social-card.png",
        ]
        for a in assets:
            self.assertTrue(a.exists(), a)

        routes = [
            PUBLIC / "index.html",
            PUBLIC / "dashboard.html",
            PUBLIC / "passport" / "index.html",
            PUBLIC / "passport" / "malta" / "index.html",
            PUBLIC / "passport" / "image-attributions.html",
        ]
        for path in routes:
            text = path.read_text(encoding="utf-8")
            self.assertIn("/favicon.svg", text, path)


if __name__ == "__main__":
    unittest.main()
