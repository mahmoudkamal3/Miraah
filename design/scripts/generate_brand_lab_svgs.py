#!/usr/bin/env python3
"""Generate Mir'ah brand-lab SVG concepts with clean UTF-8 (no illegal XML controls)."""
from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[1] / "brand-lab" / "concepts"
AP = "&#8217;"
NAME = f"Mir{AP}ah"
FONT = "system-ui, -apple-system, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif"

# True soft M with inner counters (negative valleys). clipPaths add a reflective gap.
# Distinct from <> wedges, pause bars, and code brackets.
M_FULL = (
    "M12 51.5V12.5h10.5"
    "C26.5 18.5 29.5 27 32 36"
    "C34.5 27 37.5 18.5 41.5 12.5H52V51.5H42.5V29"
    "C38.5 36.5 35 43 32 48"
    "C29 43 25.5 36.5 21.5 29V51.5H12Z"
)


def write(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    data = content.strip() + "\n"
    for ch in data:
        o = ord(ch)
        if o < 32 and o not in (9, 10, 13):
            raise ValueError(f"Illegal XML control U+{o:04X} in {path}")
    path.write_text(data, encoding="utf-8", newline="\n")
    print("wrote", path.relative_to(ROOT.parent))


def rm_mark() -> str:
    return f'''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 64 64" role="img" aria-label="{NAME} Reflected M mark">
  <defs>
    <linearGradient id="rmL" x1="8" y1="8" x2="32" y2="56" gradientUnits="userSpaceOnUse">
      <stop offset="0%" stop-color="#4AE0C0"/>
      <stop offset="100%" stop-color="#2B9FFF"/>
    </linearGradient>
    <linearGradient id="rmR" x1="32" y1="8" x2="56" y2="56" gradientUnits="userSpaceOnUse">
      <stop offset="0%" stop-color="#38D6B0"/>
      <stop offset="100%" stop-color="#1A6FD4"/>
    </linearGradient>
    <clipPath id="rmGapL"><rect width="31.2" height="64"/></clipPath>
    <clipPath id="rmGapR"><rect x="32.8" width="31.2" height="64"/></clipPath>
  </defs>
  <path fill="url(#rmL)" clip-path="url(#rmGapL)" d="{M_FULL}"/>
  <path fill="url(#rmR)" clip-path="url(#rmGapR)" d="{M_FULL}"/>
</svg>'''


def rm_mono() -> str:
    return f'''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 64 64" role="img" aria-label="{NAME} Reflected M monochrome">
  <defs>
    <clipPath id="rmGapL"><rect width="31.2" height="64"/></clipPath>
    <clipPath id="rmGapR"><rect x="32.8" width="31.2" height="64"/></clipPath>
  </defs>
  <path fill="#07111F" clip-path="url(#rmGapL)" d="{M_FULL}"/>
  <path fill="#07111F" clip-path="url(#rmGapR)" d="{M_FULL}" opacity=".9"/>
</svg>'''


def rm_icon() -> str:
    return f'''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 64 64" role="img" aria-label="{NAME} Reflected M app icon">
  <defs>
    <linearGradient id="rmBg" x1="8" y1="4" x2="56" y2="60" gradientUnits="userSpaceOnUse">
      <stop offset="0%" stop-color="#102744"/>
      <stop offset="100%" stop-color="#07111F"/>
    </linearGradient>
    <linearGradient id="rmL" x1="12" y1="12" x2="32" y2="52" gradientUnits="userSpaceOnUse">
      <stop offset="0%" stop-color="#4AE0C0"/>
      <stop offset="100%" stop-color="#2B9FFF"/>
    </linearGradient>
    <linearGradient id="rmR" x1="32" y1="12" x2="52" y2="52" gradientUnits="userSpaceOnUse">
      <stop offset="0%" stop-color="#38D6B0"/>
      <stop offset="100%" stop-color="#1A6FD4"/>
    </linearGradient>
    <clipPath id="rmGapL"><rect width="31.2" height="64"/></clipPath>
    <clipPath id="rmGapR"><rect x="32.8" width="31.2" height="64"/></clipPath>
  </defs>
  <rect width="64" height="64" rx="14" fill="url(#rmBg)"/>
  <path fill="url(#rmL)" clip-path="url(#rmGapL)" d="{M_FULL}"/>
  <path fill="url(#rmR)" clip-path="url(#rmGapR)" d="{M_FULL}"/>
</svg>'''


def dm_mark() -> str:
    return f'''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 64 64" role="img" aria-label="{NAME} Data Mirror mark">
  <defs>
    <linearGradient id="dmL" x1="8" y1="12" x2="30" y2="52" gradientUnits="userSpaceOnUse">
      <stop offset="0%" stop-color="#4AE0C0"/>
      <stop offset="100%" stop-color="#2B9FFF"/>
    </linearGradient>
    <linearGradient id="dmR" x1="34" y1="12" x2="56" y2="52" gradientUnits="userSpaceOnUse">
      <stop offset="0%" stop-color="#38D6B0"/>
      <stop offset="100%" stop-color="#1A6FD4"/>
    </linearGradient>
  </defs>
  <path fill="url(#dmL)" d="M28.5 32c0 8.2-5.4 14.2-14 16.2-1.3.3-2.5-.7-2.5-2V17.8c0-1.3 1.2-2.3 2.5-2 8.6 2 14 8 14 16.2z"/>
  <path fill="url(#dmR)" d="M35.5 32c0 8.2 5.4 14.2 14 16.2 1.3.3 2.5-.7 2.5-2V17.8c0-1.3-1.2-2.3-2.5-2-8.6 2-14 8-14 16.2z"/>
  <circle cx="32" cy="32" r="5.2" fill="#7EE7D0"/>
  <circle cx="32" cy="32" r="2.2" fill="#07111F" opacity=".28"/>
</svg>'''


def dm_mono() -> str:
    return f'''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 64 64" role="img" aria-label="{NAME} Data Mirror monochrome">
  <path fill="#07111F" d="M28.5 32c0 8.2-5.4 14.2-14 16.2-1.3.3-2.5-.7-2.5-2V17.8c0-1.3 1.2-2.3 2.5-2 8.6 2 14 8 14 16.2z"/>
  <path fill="#07111F" d="M35.5 32c0 8.2 5.4 14.2 14 16.2 1.3.3 2.5-.7 2.5-2V17.8c0-1.3-1.2-2.3-2.5-2-8.6 2-14 8-14 16.2z"/>
  <circle cx="32" cy="32" r="5.2" fill="#07111F" opacity=".55"/>
  <circle cx="32" cy="32" r="2.2" fill="#07111F" opacity=".2"/>
</svg>'''


def dm_icon() -> str:
    return f'''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 64 64" role="img" aria-label="{NAME} Data Mirror app icon">
  <defs>
    <linearGradient id="dmBg" x1="8" y1="4" x2="56" y2="60" gradientUnits="userSpaceOnUse">
      <stop offset="0%" stop-color="#102744"/>
      <stop offset="100%" stop-color="#07111F"/>
    </linearGradient>
    <linearGradient id="dmL" x1="10" y1="14" x2="30" y2="50" gradientUnits="userSpaceOnUse">
      <stop offset="0%" stop-color="#4AE0C0"/>
      <stop offset="100%" stop-color="#2B9FFF"/>
    </linearGradient>
    <linearGradient id="dmR" x1="34" y1="14" x2="54" y2="50" gradientUnits="userSpaceOnUse">
      <stop offset="0%" stop-color="#38D6B0"/>
      <stop offset="100%" stop-color="#1A6FD4"/>
    </linearGradient>
  </defs>
  <rect width="64" height="64" rx="14" fill="url(#dmBg)"/>
  <path fill="url(#dmL)" d="M28.5 32c0 8.2-5.4 14.2-14 16.2-1.3.3-2.5-.7-2.5-2V17.8c0-1.3 1.2-2.3 2.5-2 8.6 2 14 8 14 16.2z"/>
  <path fill="url(#dmR)" d="M35.5 32c0 8.2 5.4 14.2 14 16.2 1.3.3 2.5-.7 2.5-2V17.8c0-1.3-1.2-2.3-2.5-2-8.6 2-14 8-14 16.2z"/>
  <circle cx="32" cy="32" r="5.2" fill="#9AF0DC"/>
  <circle cx="32" cy="32" r="2.2" fill="#07111F" opacity=".35"/>
</svg>'''


def mp_mark() -> str:
    return f'''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 64 64" role="img" aria-label="{NAME} Mirror Portal mark">
  <defs>
    <linearGradient id="mpGlass" x1="18" y1="8" x2="46" y2="56" gradientUnits="userSpaceOnUse">
      <stop offset="0%" stop-color="#4AE0C0"/>
      <stop offset="40%" stop-color="#2B9FFF"/>
      <stop offset="100%" stop-color="#1A6FD4"/>
    </linearGradient>
    <linearGradient id="mpShine" x1="24" y1="14" x2="40" y2="50" gradientUnits="userSpaceOnUse">
      <stop offset="0%" stop-color="#E8FFF8" stop-opacity=".95"/>
      <stop offset="45%" stop-color="#7EE7D0" stop-opacity=".55"/>
      <stop offset="100%" stop-color="#2B9FFF" stop-opacity="0"/>
    </linearGradient>
  </defs>
  <rect x="18" y="8" width="28" height="48" rx="10" fill="url(#mpGlass)"/>
  <path fill="url(#mpShine)" d="M26 12h8c1.1 0 2 .9 2 2v36c0 1.1-.9 2-2 2h-8c-1.1 0-2-.9-2-2V14c0-1.1.9-2 2-2z"/>
  <ellipse cx="32" cy="32" rx="4" ry="7" fill="#07111F" opacity=".22"/>
</svg>'''


def mp_mono() -> str:
    return f'''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 64 64" role="img" aria-label="{NAME} Mirror Portal monochrome">
  <rect x="18" y="8" width="28" height="48" rx="10" fill="#07111F"/>
  <path fill="#07111F" opacity=".35" d="M26 12h8c1.1 0 2 .9 2 2v36c0 1.1-.9 2-2 2h-8c-1.1 0-2-.9-2-2V14c0-1.1.9-2 2-2z"/>
  <ellipse cx="32" cy="32" rx="4" ry="7" fill="#FFFFFF" opacity=".35"/>
</svg>'''


def mp_icon() -> str:
    return f'''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 64 64" role="img" aria-label="{NAME} Mirror Portal app icon">
  <defs>
    <linearGradient id="mpBg" x1="8" y1="4" x2="56" y2="60" gradientUnits="userSpaceOnUse">
      <stop offset="0%" stop-color="#102744"/>
      <stop offset="100%" stop-color="#07111F"/>
    </linearGradient>
    <linearGradient id="mpGlass" x1="18" y1="10" x2="46" y2="54" gradientUnits="userSpaceOnUse">
      <stop offset="0%" stop-color="#4AE0C0"/>
      <stop offset="45%" stop-color="#2B9FFF"/>
      <stop offset="100%" stop-color="#1A6FD4"/>
    </linearGradient>
    <linearGradient id="mpShine" x1="24" y1="14" x2="40" y2="50" gradientUnits="userSpaceOnUse">
      <stop offset="0%" stop-color="#E8FFF8" stop-opacity=".95"/>
      <stop offset="50%" stop-color="#7EE7D0" stop-opacity=".5"/>
      <stop offset="100%" stop-color="#2B9FFF" stop-opacity="0"/>
    </linearGradient>
  </defs>
  <rect width="64" height="64" rx="14" fill="url(#mpBg)"/>
  <rect x="18" y="8" width="28" height="48" rx="10" fill="url(#mpGlass)"/>
  <path fill="url(#mpShine)" d="M26 12h8c1.1 0 2 .9 2 2v36c0 1.1-.9 2-2 2h-8c-1.1 0-2-.9-2-2V14c0-1.1.9-2 2-2z"/>
  <ellipse cx="32" cy="32" rx="4" ry="7" fill="#07111F" opacity=".28"/>
</svg>'''


def lockup(mark_inner: str, lang: str, theme: str, gid: str) -> str:
    text_fill = "#ECF4FF" if theme == "dark" else "#07111F"
    if lang == "ar":
        text = (
            f'<text x="252" y="45" text-anchor="end" fill="{text_fill}" '
            f'font-family="{FONT}" font-size="32" font-weight="700">مرآة</text>'
        )
        g = f'<g transform="translate(8 4)">{mark_inner}</g>'
        label = "مرآة"
    else:
        text = (
            f'<text x="78" y="45" fill="{text_fill}" font-family="{FONT}" '
            f'font-size="30" font-weight="700" letter-spacing="-0.02em">Mir{AP}ah</text>'
        )
        g = f'<g transform="translate(4 4)">{mark_inner}</g>'
        label = NAME
    return f'''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 280 72" role="img" aria-label="{label}">
  <defs>
    <linearGradient id="{gid}L" x1="8" y1="8" x2="32" y2="56" gradientUnits="userSpaceOnUse">
      <stop offset="0%" stop-color="#4AE0C0"/>
      <stop offset="100%" stop-color="#2B9FFF"/>
    </linearGradient>
    <linearGradient id="{gid}R" x1="32" y1="8" x2="56" y2="56" gradientUnits="userSpaceOnUse">
      <stop offset="0%" stop-color="#38D6B0"/>
      <stop offset="100%" stop-color="#1A6FD4"/>
    </linearGradient>
    <linearGradient id="{gid}G" x1="10" y1="10" x2="54" y2="54" gradientUnits="userSpaceOnUse">
      <stop offset="0%" stop-color="#4AE0C0"/>
      <stop offset="50%" stop-color="#2B9FFF"/>
      <stop offset="100%" stop-color="#1A6FD4"/>
    </linearGradient>
    <clipPath id="{gid}CL"><rect width="31.2" height="64"/></clipPath>
    <clipPath id="{gid}CR"><rect x="32.8" width="31.2" height="64"/></clipPath>
  </defs>
  {g}
  {text}
</svg>'''


def rm_inner(gid: str) -> str:
    return (
        f'<path fill="url(#{gid}L)" clip-path="url(#{gid}CL)" d="{M_FULL}"/>'
        f'<path fill="url(#{gid}R)" clip-path="url(#{gid}CR)" d="{M_FULL}"/>'
    )


def dm_inner(gid: str) -> str:
    return (
        f'<path fill="url(#{gid}L)" d="M28.5 32c0 8.2-5.4 14.2-14 16.2-1.3.3-2.5-.7-2.5-2V17.8c0-1.3 1.2-2.3 2.5-2 8.6 2 14 8 14 16.2z"/>'
        f'<path fill="url(#{gid}R)" d="M35.5 32c0 8.2 5.4 14.2 14 16.2 1.3.3 2.5-.7 2.5-2V17.8c0-1.3-1.2-2.3-2.5-2-8.6 2-14 8-14 16.2z"/>'
        f'<circle cx="32" cy="32" r="5.2" fill="#7EE7D0"/>'
        f'<circle cx="32" cy="32" r="2.2" fill="#07111F" opacity=".28"/>'
    )


def mp_inner(gid: str) -> str:
    return (
        f'<rect x="18" y="8" width="28" height="48" rx="10" fill="url(#{gid}G)"/>'
        f'<path fill="#E8FFF8" opacity=".75" d="M26 12h8c1.1 0 2 .9 2 2v36c0 1.1-.9 2-2 2h-8c-1.1 0-2-.9-2-2V14c0-1.1.9-2 2-2z"/>'
        f'<ellipse cx="32" cy="32" rx="4" ry="7" fill="#07111F" opacity=".22"/>'
    )


def emit_concept(folder: str, mark: str, mono: str, icon: str, inner_fn) -> None:
    base = ROOT / folder
    write(base / "mark.svg", mark)
    write(base / "mark-mono.svg", mono)
    write(base / "app-icon.svg", icon)
    for lang in ("ar", "en"):
        for theme in ("dark", "light"):
            suffix = "" if theme == "dark" else "-light"
            gid = f"{folder[:2]}{lang}{theme}"
            write(base / f"lockup-{lang}{suffix}.svg", lockup(inner_fn(gid), lang, theme, gid))


def main() -> None:
    emit_concept("01-reflected-m", rm_mark(), rm_mono(), rm_icon(), rm_inner)
    emit_concept("02-data-mirror", dm_mark(), dm_mono(), dm_icon(), dm_inner)
    emit_concept("03-mirror-portal", mp_mark(), mp_mono(), mp_icon(), mp_inner)
    print("done: 21 SVG files")


if __name__ == "__main__":
    main()
