#!/usr/bin/env python3
"""Theme system tests for Mir’ah light/dark/system preference."""
from __future__ import annotations

import re
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PUBLIC = ROOT / "public"
SCRIPTS = ROOT / "scripts"


class ThemeGeneratorTests(unittest.TestCase):
    def test_shared_theme_module_exports(self):
        import sys

        sys.path.insert(0, str(SCRIPTS))
        import miraah_theme as theme

        self.assertIn("miraahTheme", theme.STORAGE_KEY)
        self.assertIn("data-theme", theme.NO_FLASH_SCRIPT)
        self.assertIn("miraahTheme", theme.NO_FLASH_SCRIPT)
        self.assertIn('data-theme="light"', theme.THEME_CSS)
        self.assertIn('data-theme="dark"', theme.THEME_CSS)
        self.assertIn("--bg:", theme.THEME_CSS)
        self.assertIn("--map-ocean:", theme.THEME_CSS)
        self.assertIn("themeBtn", theme.theme_control_html())
        self.assertIn("initThemeControls", theme.THEME_JS)
        self.assertIn("الوضع الفاتح", theme.THEME_JS)
        self.assertIn("Use device setting", theme.THEME_JS)


class ThemeHtmlTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.index = (PUBLIC / "index.html").read_text(encoding="utf-8")
        cls.dashboard = (PUBLIC / "dashboard.html").read_text(encoding="utf-8")
        cls.passport = (PUBLIC / "passport" / "index.html").read_text(encoding="utf-8")
        cls.malta = (PUBLIC / "passport" / "malta" / "index.html").read_text(encoding="utf-8")
        cls.attr = (PUBLIC / "passport" / "image-attributions.html").read_text(encoding="utf-8")
        cls.passport_js = (PUBLIC / "passport" / "assets" / "passport.js").read_text(encoding="utf-8")

    def test_dashboard_byte_identical(self):
        self.assertEqual(
            (PUBLIC / "index.html").read_bytes(),
            (PUBLIC / "dashboard.html").read_bytes(),
        )

    def test_no_flash_script_before_body(self):
        for label, html in (
            ("home", self.index),
            ("passport", self.passport),
            ("malta", self.malta),
            ("attr", self.attr),
        ):
            with self.subTest(label):
                head = html.split("</head>", 1)[0]
                self.assertIn("miraahTheme", head)
                self.assertIn("data-theme", head)
                self.assertLess(head.find("<script>"), head.find("<body") if "<body" in head else len(head))
                # script appears before stylesheet content paints meaningfully
                self.assertIn("localStorage.getItem(k)", head)
                self.assertIn("prefers-color-scheme", head)

    def test_theme_tokens_present(self):
        self.assertIn("--bg:", self.index)
        self.assertIn('data-theme="light"', self.index)
        css = (PUBLIC / "passport" / "assets" / "passport.css").read_text(encoding="utf-8")
        self.assertIn("--bg:", css)
        self.assertIn('data-theme="light"', css)
        self.assertIn("--map-ocean:", css)

    def test_header_toggle_on_all_pages(self):
        for label, html in (
            ("home", self.index),
            ("passport", self.passport),
            ("malta", self.malta),
            ("attr", self.attr),
        ):
            with self.subTest(label):
                self.assertIn('id="themeBtn"', html)
                self.assertIn('id="themeMenu"', html)
                self.assertIn("data-theme-pref", html)
                self.assertIn("icon-sun", html)
                self.assertIn("icon-moon", html)
                # no emoji icons
                self.assertNotIn("☀️", html)
                self.assertNotIn("🌙", html)

    def test_shared_storage_key(self):
        for blob in (self.index, self.passport_js, self.attr):
            self.assertIn("miraahTheme", blob)

    def test_labels_ar_en(self):
        for blob in (self.index, self.passport_js, self.attr):
            self.assertIn("الوضع الفاتح", blob)
            self.assertIn("الوضع الداكن", blob)
            self.assertIn("استخدام إعداد الجهاز", blob)
            self.assertIn("Light mode", blob)
            self.assertIn("Dark mode", blob)
            self.assertIn("Use device setting", blob)

    def test_theme_change_hooks(self):
        self.assertIn("onMiraahThemeChange", self.index)
        self.assertIn("refreshChartColors", self.index)
        self.assertIn("onMiraahThemeChange", self.passport_js)
        self.assertIn("refreshMapColors", self.passport_js)

    def test_default_system_preference_in_boot(self):
        # Boot defaults preference to system when unset
        self.assertIn("p='system'", self.index)
        self.assertIn("prefers-color-scheme", self.index)

    def test_dynamic_theme_color(self):
        self.assertIn("theme-color", self.index)
        self.assertIn("#e8eef6", self.index)  # light meta color in JS
        self.assertIn("#07111f", self.index)  # dark meta color

    def test_logo_present_both_modes(self):
        self.assertIn("/assets/brand/miraah-app-icon.svg", self.index)
        self.assertIn("/assets/brand/miraah-app-icon.svg", self.malta)

    def test_no_external_theme_assets(self):
        banned = ("fonts.googleapis.com", "cdn.jsdelivr", "unpkg.com")
        for html in (self.index, self.passport, self.malta, self.attr):
            low = html.lower()
            for b in banned:
                self.assertNotIn(b, low)

    def test_indexing_unchanged(self):
        self.assertIn('content="index, follow"', self.index)
        self.assertIn('content="noindex, follow"', self.passport)
        self.assertIn('content="noindex, follow"', self.malta)

    def test_generators_source_wired(self):
        dash = (SCRIPTS / "render_dashboard.py").read_text(encoding="utf-8")
        passport = (SCRIPTS / "render_passport_pages.py").read_text(encoding="utf-8")
        self.assertIn("import miraah_theme as theme", dash)
        self.assertIn("import miraah_theme as theme", passport)
        self.assertIn("theme.NO_FLASH_SCRIPT", dash)
        self.assertIn("theme.NO_FLASH_SCRIPT", passport)
        self.assertIn("theme.THEME_CSS", dash)
        self.assertIn("theme.THEME_JS", passport)


class ThemeLogicUnitTests(unittest.TestCase):
    """Pure JS logic mirrored in Python for preference resolution."""

    def effective(self, pref: str, system_dark: bool) -> str:
        if pref not in ("light", "dark", "system"):
            pref = "system"
        if pref == "system":
            return "dark" if system_dark else "light"
        return pref

    def test_system_light_resolution(self):
        self.assertEqual(self.effective("system", False), "light")

    def test_system_dark_resolution(self):
        self.assertEqual(self.effective("system", True), "dark")

    def test_explicit_light(self):
        self.assertEqual(self.effective("light", True), "light")

    def test_explicit_dark(self):
        self.assertEqual(self.effective("dark", False), "dark")

    def test_corrupt_fallback(self):
        self.assertEqual(self.effective("nope", True), "dark")
        self.assertEqual(self.effective("", False), "light")


if __name__ == "__main__":
    unittest.main()
