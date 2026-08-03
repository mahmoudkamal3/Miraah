#!/usr/bin/env python3
"""Generate canonical Mir’ah Reflected M brand assets (SVG + PNG)."""
from __future__ import annotations

import json
import shutil
import subprocess
import tempfile
from pathlib import Path

from PIL import Image

ROOT = Path(__file__).resolve().parents[1]
PUBLIC = ROOT / "public"
BRAND = PUBLIC / "assets" / "brand"
LAB = ROOT / "design" / "brand-lab" / "concepts" / "01-reflected-m"

import sys

sys.path.insert(0, str(ROOT / "scripts"))
from miraah_brand import (  # noqa: E402
    BACKGROUND_COLOR,
    BRAND_AR,
    M_PATH,
    THEME_COLOR,
)

AP = "&#8217;"
NAME = f"Mir{AP}ah"
FONT = "system-ui, -apple-system, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif"


def find_browser() -> str:
    candidates = [
        Path(r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe"),
        Path(r"C:\Program Files\Microsoft\Edge\Application\msedge.exe"),
        Path(r"C:\Program Files\Google\Chrome\Application\chrome.exe"),
    ]
    for c in candidates:
        if c.exists():
            return str(c)
    raise SystemExit("No Edge/Chrome found for SVG rasterization")


def write_svg(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    data = content.strip() + "\n"
    for ch in data:
        o = ord(ch)
        if o < 32 and o not in (9, 10, 13):
            raise ValueError(f"Illegal control in {path}: U+{o:04X}")
    path.write_text(data, encoding="utf-8", newline="\n")
    print("svg", path.relative_to(ROOT))


def mark_svg() -> str:
    # Continuous M silhouette. Perceptible reflection via center light stop + soft left wash.
    # No clip gap, no pause bar, no disconnected halves.
    return f'''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 64 64" role="img" aria-label="{NAME} mark">
  <defs>
    <linearGradient id="rmGrad" x1="8" y1="8" x2="56" y2="56" gradientUnits="userSpaceOnUse">
      <stop offset="0%" stop-color="#4AE0C0"/>
      <stop offset="42%" stop-color="#38D6B0"/>
      <stop offset="50%" stop-color="#9AF0DC"/>
      <stop offset="58%" stop-color="#2B9FFF"/>
      <stop offset="100%" stop-color="#1A6FD4"/>
    </linearGradient>
    <clipPath id="rmLeftWash"><rect x="0" y="0" width="32" height="64"/></clipPath>
  </defs>
  <path fill="url(#rmGrad)" d="{M_PATH}"/>
  <path fill="#E8FFF8" opacity=".22" clip-path="url(#rmLeftWash)" d="{M_PATH}"/>
</svg>'''


def mark_mono_svg() -> str:
    return f'''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 64 64" role="img" aria-label="{NAME} mark monochrome">
  <path fill="#07111F" d="{M_PATH}"/>
</svg>'''


def app_icon_svg() -> str:
    return f'''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 64 64" role="img" aria-label="{NAME} app icon">
  <defs>
    <linearGradient id="rmBg" x1="8" y1="4" x2="56" y2="60" gradientUnits="userSpaceOnUse">
      <stop offset="0%" stop-color="#102744"/>
      <stop offset="100%" stop-color="#07111F"/>
    </linearGradient>
    <linearGradient id="rmGrad" x1="10" y1="10" x2="54" y2="54" gradientUnits="userSpaceOnUse">
      <stop offset="0%" stop-color="#4AE0C0"/>
      <stop offset="42%" stop-color="#38D6B0"/>
      <stop offset="50%" stop-color="#9AF0DC"/>
      <stop offset="58%" stop-color="#2B9FFF"/>
      <stop offset="100%" stop-color="#1A6FD4"/>
    </linearGradient>
    <clipPath id="rmLeftWash"><rect x="0" y="0" width="32" height="64"/></clipPath>
  </defs>
  <rect width="64" height="64" rx="14" fill="url(#rmBg)"/>
  <path fill="url(#rmGrad)" d="{M_PATH}"/>
  <path fill="#E8FFF8" opacity=".22" clip-path="url(#rmLeftWash)" d="{M_PATH}"/>
</svg>'''


def logo_svg(*, lang: str) -> str:
    if lang == "ar":
        text = (
            f'<text x="252" y="45" text-anchor="end" fill="#ECF4FF" '
            f'font-family="{FONT}" font-size="32" font-weight="700">{BRAND_AR}</text>'
        )
        g = '<g transform="translate(8 4)">'
        label = BRAND_AR
    else:
        text = (
            f'<text x="78" y="45" fill="#ECF4FF" font-family="{FONT}" '
            f'font-size="30" font-weight="700" letter-spacing="-0.02em">{NAME}</text>'
        )
        g = '<g transform="translate(4 4)">'
        label = NAME
    mark = (
        f'<defs>'
        f'<linearGradient id="lg" x1="8" y1="8" x2="56" y2="56" gradientUnits="userSpaceOnUse">'
        f'<stop offset="0%" stop-color="#4AE0C0"/>'
        f'<stop offset="42%" stop-color="#38D6B0"/>'
        f'<stop offset="50%" stop-color="#9AF0DC"/>'
        f'<stop offset="58%" stop-color="#2B9FFF"/>'
        f'<stop offset="100%" stop-color="#1A6FD4"/>'
        f'</linearGradient>'
        f'<clipPath id="lw"><rect width="32" height="64"/></clipPath>'
        f'</defs>'
        f'<path fill="url(#lg)" d="{M_PATH}"/>'
        f'<path fill="#E8FFF8" opacity=".22" clip-path="url(#lw)" d="{M_PATH}"/>'
    )
    return f'''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 280 72" role="img" aria-label="{label}">
  {g}{mark}</g>
  {text}
</svg>'''


def social_card_svg() -> str:
    # Self-contained 1200x630 card as SVG, then rasterized.
    return f'''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 1200 630" width="1200" height="630" role="img" aria-label="{NAME} social card">
  <defs>
    <linearGradient id="bg" x1="0" y1="0" x2="1200" y2="630" gradientUnits="userSpaceOnUse">
      <stop offset="0%" stop-color="#0a1628"/>
      <stop offset="55%" stop-color="#07111F"/>
      <stop offset="100%" stop-color="#0c1f3a"/>
    </linearGradient>
    <linearGradient id="glow" x1="200" y1="80" x2="900" y2="560" gradientUnits="userSpaceOnUse">
      <stop offset="0%" stop-color="#38D6B0" stop-opacity=".18"/>
      <stop offset="50%" stop-color="#2B9FFF" stop-opacity=".12"/>
      <stop offset="100%" stop-color="#07111F" stop-opacity="0"/>
    </linearGradient>
    <linearGradient id="rmGrad" x1="0" y1="0" x2="64" y2="64" gradientUnits="userSpaceOnUse">
      <stop offset="0%" stop-color="#4AE0C0"/>
      <stop offset="42%" stop-color="#38D6B0"/>
      <stop offset="50%" stop-color="#9AF0DC"/>
      <stop offset="58%" stop-color="#2B9FFF"/>
      <stop offset="100%" stop-color="#1A6FD4"/>
    </linearGradient>
    <clipPath id="lw"><rect width="32" height="64"/></clipPath>
  </defs>
  <rect width="1200" height="630" fill="url(#bg)"/>
  <circle cx="980" cy="90" r="220" fill="url(#glow)"/>
  <circle cx="160" cy="540" r="180" fill="#38D6B0" opacity=".08"/>
  <g transform="translate(120 175) scale(4.2)">
    <path fill="url(#rmGrad)" d="{M_PATH}"/>
    <path fill="#E8FFF8" opacity=".22" clip-path="url(#lw)" d="{M_PATH}"/>
  </g>
  <text x="430" y="265" fill="#ECF4FF" font-family="{FONT}" font-size="72" font-weight="750">{BRAND_AR}</text>
  <text x="430" y="345" fill="#ECF4FF" font-family="{FONT}" font-size="56" font-weight="700" letter-spacing="-0.02em">{NAME}</text>
  <text x="430" y="420" fill="#9BB4D0" font-family="{FONT}" font-size="28" font-weight="500">قارن الدول بالأرقام</text>
  <text x="430" y="465" fill="#8FA6BF" font-family="{FONT}" font-size="24" font-weight="500">Compare countries through data</text>
  <rect x="120" y="560" width="120" height="4" rx="2" fill="#38D6B0"/>
  <rect x="250" y="560" width="80" height="4" rx="2" fill="#2B9FFF" opacity=".7"/>
</svg>'''


def rasterize_svg(browser: str, svg_path: Path, out_png: Path, width: int, height: int, *, bg: str | None) -> None:
    """Render SVG to PNG via headless Chromium at exact pixel size."""
    # Inline SVG to avoid file:// CORS issues with <img src>.
    svg_text = svg_path.read_text(encoding="utf-8")
    # Ensure root svg fills the frame.
    if 'width="' not in svg_text.split(">", 1)[0]:
        svg_text = svg_text.replace("<svg ", f'<svg width="{width}" height="{height}" ', 1)
    bg_css = bg if bg is not None else "#00000000"
    html = f"""<!doctype html>
<html><head><meta charset="utf-8"><style>
  html,body{{margin:0;padding:0;width:{width}px;height:{height}px;overflow:hidden;background:{bg_css};}}
  svg{{display:block;width:{width}px;height:{height}px;}}
</style></head>
<body>{svg_text}</body></html>"""
    with tempfile.TemporaryDirectory() as td:
        td_path = Path(td)
        html_path = td_path / "frame.html"
        shot_path = td_path / "shot.png"
        html_path.write_text(html, encoding="utf-8")
        cmd = [
            browser,
            "--headless=new",
            "--disable-gpu",
            "--hide-scrollbars",
            "--force-device-scale-factor=1",
            f"--window-size={width},{height}",
            f"--screenshot={shot_path}",
            html_path.resolve().as_uri(),
        ]
        subprocess.run(cmd, check=True, capture_output=True)
        if not shot_path.exists():
            raise SystemExit(f"Screenshot failed for {svg_path}")
        im = Image.open(shot_path).convert("RGBA")
        # Edge may capture slightly larger; crop to requested size from top-left.
        if im.size != (width, height):
            im = im.crop((0, 0, width, height))
        if bg is None:
            # Chroma-key near-white / near-gray page chrome to transparency for mark favicons.
            pixels = im.load()
            for y in range(height):
                for x in range(width):
                    r, g, b, a = pixels[x, y]
                    if r > 245 and g > 245 and b > 245:
                        pixels[x, y] = (r, g, b, 0)
        out_png.parent.mkdir(parents=True, exist_ok=True)
        im.save(out_png, format="PNG", optimize=True)
        print("png", out_png.relative_to(ROOT), f"{width}x{height}", out_png.stat().st_size)


def write_manifest() -> None:
    manifest = {
        "name": "Mir’ah",
        "short_name": "Mir’ah",
        "description": "Compare countries through data",
        "start_url": "/",
        "scope": "/",
        "display": "standalone",
        "background_color": BACKGROUND_COLOR,
        "theme_color": THEME_COLOR,
        "lang": "ar",
        "dir": "rtl",
        "icons": [
            {
                "src": "/icon-192.png",
                "sizes": "192x192",
                "type": "image/png",
                "purpose": "any",
            },
            {
                "src": "/icon-512.png",
                "sizes": "512x512",
                "type": "image/png",
                "purpose": "any",
            },
        ],
    }
    path = PUBLIC / "site.webmanifest"
    path.write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print("manifest", path.relative_to(ROOT))


def sync_lab_selected() -> None:
    """Keep brand-lab Concept 1 in sync with production mark; mark as selected."""
    for name, content in [
        ("mark.svg", mark_svg()),
        ("mark-mono.svg", mark_mono_svg()),
        ("app-icon.svg", app_icon_svg()),
        ("lockup-en.svg", logo_svg(lang="en")),
        ("lockup-ar.svg", logo_svg(lang="ar")),
    ]:
        write_svg(LAB / name, content)
    note = LAB / "SELECTED.md"
    note.write_text(
        "# Selected: Reflected M\n\n"
        "Official Mir’ah brand mark as of integration.\n"
        "Production assets live in `public/assets/brand/` and root favicons.\n"
        "Do not ship Data Mirror or Mirror Portal to production.\n",
        encoding="utf-8",
    )


def main() -> None:
    browser = find_browser()
    BRAND.mkdir(parents=True, exist_ok=True)

    mark = BRAND / "miraah-mark.svg"
    mono = BRAND / "miraah-mark-mono.svg"
    app = BRAND / "miraah-app-icon.svg"
    logo_en = BRAND / "miraah-logo-en.svg"
    logo_ar = BRAND / "miraah-logo-ar.svg"
    social_svg = BRAND / "miraah-social-card.svg"

    write_svg(mark, mark_svg())
    write_svg(mono, mark_mono_svg())
    write_svg(app, app_icon_svg())
    write_svg(logo_en, logo_svg(lang="en"))
    write_svg(logo_ar, logo_svg(lang="ar"))
    write_svg(social_svg, social_card_svg())

    # Favicon SVG = mark (transparent)
    shutil.copyfile(mark, PUBLIC / "favicon.svg")
    print("svg", (PUBLIC / "favicon.svg").relative_to(ROOT))

    # Raster icons from app-icon (navy tile) for sharp small sizes
    rasterize_svg(browser, app, PUBLIC / "favicon-16x16.png", 16, 16, bg=BACKGROUND_COLOR)
    rasterize_svg(browser, app, PUBLIC / "favicon-32x32.png", 32, 32, bg=BACKGROUND_COLOR)
    rasterize_svg(browser, app, PUBLIC / "apple-touch-icon.png", 180, 180, bg=BACKGROUND_COLOR)
    rasterize_svg(browser, app, PUBLIC / "icon-192.png", 192, 192, bg=BACKGROUND_COLOR)
    rasterize_svg(browser, app, PUBLIC / "icon-512.png", 512, 512, bg=BACKGROUND_COLOR)
    rasterize_svg(
        browser,
        social_svg,
        BRAND / "miraah-social-card.png",
        1200,
        630,
        bg=BACKGROUND_COLOR,
    )

    write_manifest()
    sync_lab_selected()
    print("done")


if __name__ == "__main__":
    main()
