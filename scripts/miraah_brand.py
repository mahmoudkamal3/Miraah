#!/usr/bin/env python3
"""Canonical Mir’ah brand constants and HTML head helpers (Reflected M)."""
from __future__ import annotations

CANONICAL_ORIGIN = "https://miraah.mirapp.workers.dev/"
THEME_COLOR = "#07111f"
BACKGROUND_COLOR = "#07111f"

# Root-relative asset paths
MARK_SVG = "/assets/brand/miraah-mark.svg"
MARK_MONO_SVG = "/assets/brand/miraah-mark-mono.svg"
LOGO_EN_SVG = "/assets/brand/miraah-logo-en.svg"
LOGO_AR_SVG = "/assets/brand/miraah-logo-ar.svg"
APP_ICON_SVG = "/assets/brand/miraah-app-icon.svg"
FAVICON_SVG = "/favicon.svg"
FAVICON_16 = "/favicon-16x16.png"
FAVICON_32 = "/favicon-32x32.png"
APPLE_TOUCH = "/apple-touch-icon.png"
ICON_192 = "/icon-192.png"
ICON_512 = "/icon-512.png"
SOCIAL_CARD = "/assets/brand/miraah-social-card.png"
MANIFEST = "/site.webmanifest"

BRAND_AR = "مرآة"
BRAND_EN = "Mir\u2019ah"  # Mir’ah
HOME_ARIA_AR = "العودة إلى الصفحة الرئيسية"
HOME_ARIA_EN = "Back to homepage"

# Continuous soft M with inner counters (single silhouette).
M_PATH = (
    "M12 51.5V12.5h10.5"
    "C26.5 18.5 29.5 27 32 36"
    "C34.5 27 37.5 18.5 41.5 12.5H52V51.5H42.5V29"
    "C38.5 36.5 35 43 32 48"
    "C29 43 25.5 36.5 21.5 29V51.5H12Z"
)


def brand_head_links(*, social_card_abs: str | None = None) -> str:
    """Favicon, theme-color, manifest, and social image meta tags."""
    og_image = social_card_abs or f"{CANONICAL_ORIGIN.rstrip('/')}{SOCIAL_CARD}"
    return (
        f'<meta name="theme-color" content="{THEME_COLOR}">'
        f'<link rel="icon" href="{FAVICON_SVG}" type="image/svg+xml">'
        f'<link rel="icon" type="image/png" sizes="16x16" href="{FAVICON_16}">'
        f'<link rel="icon" type="image/png" sizes="32x32" href="{FAVICON_32}">'
        f'<link rel="apple-touch-icon" sizes="180x180" href="{APPLE_TOUCH}">'
        f'<link rel="manifest" href="{MANIFEST}">'
        f'<meta property="og:image" content="{og_image}">'
        f'<meta property="og:image:width" content="1200">'
        f'<meta property="og:image:height" content="630">'
        f'<meta name="twitter:card" content="summary_large_image">'
        f'<meta name="twitter:image" content="{og_image}">'
    )


def brand_mark_img(*, size_css: str = "44px", alt: str = "") -> str:
    return (
        f'<img class="logo-mark" src="{MARK_SVG}" width="44" height="44" '
        f'alt="{alt}" decoding="async">'
    )


def brand_header_anchor(*, lang_default: str = "ar") -> str:
    """Header brand link. Title/subtitle filled by JS; mark is always Reflected M."""
    aria = HOME_ARIA_AR if lang_default == "ar" else HOME_ARIA_EN
    return (
        f'<a class="brand" href="/" aria-label="{aria}" id="brandHome">'
        f'<span class="logo">{brand_mark_img()}</span>'
        f'<span class="brand-text"><h1 id="brandTitle"></h1>'
        f'<p id="brandSubtitle"></p></span></a>'
    )


def json_ld_logo_abs() -> str:
    return f"{CANONICAL_ORIGIN.rstrip('/')}{APP_ICON_SVG}"
