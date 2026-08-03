#!/usr/bin/env python3
"""Validate Mir'ah brand-lab assets: existence, XML parse, viewBox, HTTP 200."""
from __future__ import annotations

import argparse
import re
import sys
import urllib.error
import urllib.request
import xml.etree.ElementTree as ET
from pathlib import Path

LAB = Path(__file__).resolve().parents[1] / "brand-lab"
CONCEPTS = ["01-reflected-m", "02-data-mirror", "03-mirror-portal"]
FILES = [
    "mark.svg",
    "mark-mono.svg",
    "app-icon.svg",
    "lockup-ar.svg",
    "lockup-en.svg",
    "lockup-ar-light.svg",
    "lockup-en-light.svg",
]


def illegal_controls(text: str) -> list[str]:
    bad = []
    for i, ch in enumerate(text):
        o = ord(ch)
        if o < 32 and o not in (9, 10, 13):
            bad.append(f"U+{o:04X}@{i}")
    return bad


def collect_refs(html: str) -> list[str]:
    refs = re.findall(r'''(?:src|href)=["'](concepts/[^"']+\.svg)["']''', html)
    # Also dynamic JS template paths used by the board
    for c in CONCEPTS:
        for f in FILES:
            refs.append(f"concepts/{c}/{f}")
        refs.append(f"concepts/{c}/app-icon.svg")
        refs.append(f"concepts/{c}/mark.svg")
    # unique preserve order
    seen = set()
    out = []
    for r in refs:
        if r not in seen:
            seen.add(r)
            out.append(r)
    return out


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--base-url", default="http://127.0.0.1:8767", help="Local brand-lab server")
    ap.add_argument("--skip-http", action="store_true")
    args = ap.parse_args()

    errors: list[str] = []
    checks = 0
    passed = 0

    index = LAB / "index.html"
    if not index.exists():
        print("FAIL: index.html missing")
        return 1

    # Expected 21 concept files
    expected_paths = [LAB / "concepts" / c / f for c in CONCEPTS for f in FILES]
    for path in expected_paths:
        checks += 1
        rel = path.relative_to(LAB).as_posix()
        if not path.exists():
            errors.append(f"missing file: {rel}")
            continue
        text = path.read_text(encoding="utf-8")
        bad = illegal_controls(text)
        if bad:
            errors.append(f"illegal XML controls in {rel}: {', '.join(bad[:5])}")
            continue
        try:
            root = ET.fromstring(text)
        except ET.ParseError as e:
            errors.append(f"SVG parse error {rel}: {e}")
            continue
        vb = root.attrib.get("viewBox")
        if not vb:
            errors.append(f"missing viewBox: {rel}")
            continue
        passed += 1

    # HTML references exist
    html = index.read_text(encoding="utf-8")
    for ref in collect_refs(html):
        checks += 1
        path = LAB / ref
        if path.exists():
            passed += 1
        else:
            errors.append(f"board references missing asset: {ref}")

    # HTTP checks
    if not args.skip_http:
        urls = ["/"] + [f"/concepts/{c}/{f}" for c in CONCEPTS for f in FILES]
        for url in urls:
            checks += 1
            full = args.base_url.rstrip("/") + url
            try:
                with urllib.request.urlopen(full, timeout=5) as resp:
                    code = getattr(resp, "status", None) or resp.getcode()
                    body = resp.read()
                    if code != 200:
                        errors.append(f"HTTP {code} for {url}")
                        continue
                    if url.endswith(".svg"):
                        # re-parse bytes
                        try:
                            ET.fromstring(body.decode("utf-8"))
                        except Exception as e:
                            errors.append(f"HTTP body not valid SVG {url}: {e}")
                            continue
                    passed += 1
            except urllib.error.URLError as e:
                errors.append(f"HTTP failed {url}: {e}")
            except Exception as e:
                errors.append(f"HTTP error {url}: {e}")

    print(f"Asset checks: {passed}/{checks} passed")
    print(f"Broken images: {len(errors)}")
    if errors:
        print("--- failures ---")
        for e in errors:
            print(" -", e)
        return 1
    print("OK: all brand-lab assets valid")
    return 0


if __name__ == "__main__":
    sys.exit(main())
