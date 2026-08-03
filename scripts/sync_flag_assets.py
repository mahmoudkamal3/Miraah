#!/usr/bin/env python3
"""Sync local Mir’ah flag SVGs from the flag-icons package (MIT).

Source: lipis/flag-icons v7.5.0 — https://github.com/lipis/flag-icons
Copies only ISO2 codes used by the passport dataset into public/assets/flags/.
"""
from __future__ import annotations

import json
import shutil
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

import miraah_flags as flags  # noqa: E402

SOURCE_DIR = ROOT / "node_modules" / "flag-icons" / "flags" / "4x3"
LICENSE_SRC = ROOT / "node_modules" / "flag-icons" / "LICENSE"
NOTICE = flags.FLAGS_DIR / "SOURCE.txt"
INDEX = ROOT / "public" / "data" / "passports" / "index.json"
BY_CODE = ROOT / "public" / "data" / "passports" / "by-code"


def collect_iso2() -> set[str]:
    codes: set[str] = set()
    index = json.loads(INDEX.read_text(encoding="utf-8"))
    for p in index.get("passports", []):
        iso2 = (p.get("iso2") or "").strip().lower()
        if iso2:
            codes.add(iso2)
    # Destinations share the same ISO universe; sample one detail file for safety.
    for path in sorted(BY_CODE.glob("*.json"))[:3]:
        payload = json.loads(path.read_text(encoding="utf-8"))
        for d in payload.get("destinations", []):
            iso2 = (d.get("iso2") or "").strip().lower()
            if iso2:
                codes.add(iso2)
    # Always include mapped aliases
    for dest in flags.ISO2_ALIASES.values():
        codes.add(dest.lower())
    return codes


def write_fallback() -> None:
    flags.FLAGS_DIR.mkdir(parents=True, exist_ok=True)
    # Neutral Mir’ah mark-style fallback (not an emoji, not ISO letters).
    svg = """<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 640 480" role="img" aria-label="Flag unavailable">
  <rect width="640" height="480" fill="#0d1b2e"/>
  <rect x="24" y="24" width="592" height="432" rx="28" fill="#12243a" stroke="#2b9fff" stroke-width="8"/>
  <path fill="#38d6b0" d="M180 360V120h78c28 42 48 100 66 166 18-66 38-124 66-166h78v240h-70V210c-28 56-52 104-74 140-22-36-46-84-74-140v150H180z"/>
</svg>
"""
    flags.FALLBACK_PATH.write_text(svg, encoding="utf-8", newline="\n")


def main() -> int:
    codes = collect_iso2() if INDEX.is_file() else set()
    if not SOURCE_DIR.is_dir():
        # Allow generators to run when assets were already synced previously.
        existing_ok = bool(codes) and not flags.missing_flag_codes(
            [flags.resolve_iso2(c) for c in codes]
        )
        if existing_ok and flags.FALLBACK_PATH.is_file():
            print(
                f"codes_requested={len(codes)}\ncopied=0\nmissing=[]\n"
                f"out={flags.FLAGS_DIR.relative_to(ROOT)}\n"
                "note=skipped sync (flag-icons not installed; local assets present)"
            )
            return 0
        raise SystemExit(
            "Missing node_modules/flag-icons. Run: npm install --no-save flag-icons@7.5.0"
        )
    if not INDEX.is_file():
        raise SystemExit("Missing passport index.json")

    flags.FLAGS_DIR.mkdir(parents=True, exist_ok=True)
    write_fallback()

    copied = 0
    missing: list[str] = []
    for code in sorted(codes):
        mapped = flags.resolve_iso2(code)
        src = SOURCE_DIR / f"{mapped}.svg"
        dest = flags.FLAGS_DIR / f"{mapped}.svg"
        # Also copy under original code if alias differs
        if not src.is_file():
            missing.append(code)
            continue
        shutil.copyfile(src, dest)
        if mapped != code:
            shutil.copyfile(src, flags.FLAGS_DIR / f"{code}.svg")
        copied += 1

    if LICENSE_SRC.is_file():
        shutil.copyfile(LICENSE_SRC, flags.FLAGS_DIR / "LICENSE")
    NOTICE.write_text(
        "Flag SVGs sourced from flag-icons (lipis/flag-icons) v7.5.0.\n"
        "License: MIT — see LICENSE in this directory.\n"
        "Upstream: https://github.com/lipis/flag-icons\n"
        "Only ISO2 codes used by Mir’ah Passport Power are copied into this folder.\n"
        "_fallback.svg is a Mir’ah-designed placeholder (not from flag-icons).\n",
        encoding="utf-8",
    )

    print(f"codes_requested={len(codes)}")
    print(f"copied={copied}")
    print(f"missing={missing}")
    print(f"out={flags.FLAGS_DIR.relative_to(ROOT)}")
    if missing:
        raise SystemExit(f"Missing flag assets for: {missing}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
