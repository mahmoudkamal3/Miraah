#!/usr/bin/env python3
"""Acquire and license-audit passport cover images from Wikimedia Commons only.

Default mode is --audit-only (no production asset writes).

Discovery is limited to the official Wikimedia Commons API. Do not scrape
Passport Index, VisaIndex, Henley, Google Images, Pinterest, blogs, or
commercial competitors.
"""

from __future__ import annotations

import argparse
import hashlib
import html
import json
import re
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
import miraah_theme as theme  # noqa: E402

import passport_locale as locale  # noqa: E402

INDEX_PATH = ROOT / "public" / "data" / "passports" / "index.json"
COVERS_ROOT = ROOT / "source-data" / "passport-covers"
MANIFEST_PATH = COVERS_ROOT / "manifest.json"
AUDIT_PATH = COVERS_ROOT / "AUDIT.md"
MANUAL_REVIEW_PATH = COVERS_ROOT / "manual-review" / "REPORT.md"
CACHE_DIR = COVERS_ROOT / "cache"
ORIGINALS_DIR = COVERS_ROOT / "originals"
THUMBS_DIR = COVERS_ROOT / "manual-review" / "thumbs"
PUBLIC_ASSETS = ROOT / "public" / "assets" / "passports"
PUBLIC_COVERS_META = ROOT / "public" / "data" / "passports" / "covers.json"
ATTRIBUTIONS_HTML = ROOT / "public" / "passport" / "image-attributions.html"

COMMONS_API = "https://commons.wikimedia.org/w/api.php"
USER_AGENT = (
    "MirahPassportCoverAudit/1.0 "
    "(https://miraah.mirapp.workers.dev/; educational research; "
    "passport-cover licensing audit for Mir'ah)"
)

MIN_INTERVAL_SEC = 0.35
REQUEST_TIMEOUT_SEC = 45
MAX_RETRIES = 4
SEARCH_LIMIT = 12
MIN_WIDTH = 220
MIN_HEIGHT = 280
MAX_DERIV_EDGE = 900
MAX_DERIV_BYTES = 280_000
WEBP_QUALITY = 82

ALLOWED_LICENSE_PATTERNS = [
    re.compile(r"^public domain$", re.I),
    re.compile(r"^pd[\s\-]", re.I),
    re.compile(r"^cc0$", re.I),
    re.compile(r"^cc[\s\-]?zero$", re.I),
    re.compile(r"^cc[\s\-]?by(?![\s\-]?nc)(?![\s\-]?nd)", re.I),
]

REJECT_LICENSE_TOKENS = (
    "all rights reserved",
    "fair use",
    "noncommercial",
    "non-commercial",
    "nc-",
    "-nc",
    " cc-nc",
    "cc by-nc",
    "cc-by-nc",
    "editorial",
    "no derivatives",
    "no-derivatives",
    "cc-by-nd",
    "cc by-nd",
    "copyrighted",
)

NEGATIVE_TITLE = re.compile(
    r"(stamp|visa\s*page|biodata|bio[\s\-]?data|identity\s*page|personal\s*data|"
    r"signature|mrz|data\s*page|inside\s*page|endorsement|entry\s*stamp|"
    r"exit\s*stamp|screenshot|composite|collage|passportindex|visa\s*index|"
    r"henley|pinterest|google\s*image|visafree|visa[\s\-_]?free|world\s*map|"
    r"\bmap\b|chart|infographic|comparison|mobility\s*score|ranking|"
    r"souvenir|novelty|prop\b|replica|message\s*page|observation\s*page|"
    r"coat\s*of\s*arms\s*only|(?<!passport\s)visa\.png|(?<!passport\s)visa\.jpg|"
    r"\bfiji\s+visa\b|\bvisa\s+sticker\b|refugee|lotshampa|beldangi|"
    r"karabakh|artsakh|nagorno)",
    re.I,
)

# Tokens that indicate the file is for a different polity than the audited ISO3.
CROSS_COUNTRY_BLOCKERS: dict[str, tuple[str, ...]] = {
    "GIN": ("bissau", "guinea-bissau", "guiné-bissau", "guine-bissau"),
    "GNB": ("conakry",),
    "ARM": ("karabakh", "artsakh", "nagorno"),
    "AZE": ("karabakh", "artsakh"),
    "COD": ("brazzaville",),
    "COG": ("kinshasa", "zaire"),
    "KOR": ("dprk", "north korea", "people's republic of korea"),
    "PRK": ("south korea", "republic of korea"),
    "WSM": ("american samoa",),
    "CHN": ("hong kong", "macau", "macao", "taiwan"),
    "BTN": ("refugee", "lotshampa", "nepal", "beldangi"),
}
DIPLOMATIC_RE = re.compile(r"(diplomatic|service\s+passport|official\s+passport|consular)", re.I)
HISTORIC_RE = re.compile(
    r"(historic|historical|obsolete|former|old\s+passport|pre[\-\s]?19|"
    r"british\s+\w+\s+passport|colonial|kingdom\s+of|empire|"
    r"soviet|ussr|yugoslavia|czechoslovakia|rhodesia|zaire|"
    r"british\s+malta|british\s+hong\s+kong|british\s+mauritius|"
    r"american\s+samoa)",
    re.I,
)
COVER_POSITIVE = re.compile(
    r"(passport\s*cover|cover\s*of\s*.*passport|biometric\s+passport|"
    r"ordinary\s+passport|passport\s+of\s+|front\s+cover|"
    r"e[\s\-]?passport|national\s+passport)",
    re.I,
)
PASSPORT_WORD = re.compile(r"\bpassports?\b", re.I)
PERSONAL_DATA_RE = re.compile(
    r"(passport\s*number|date\s*of\s*birth|personal\s*number|holder.?s\s*name|"
    r"photo\s*page|face\s*page|mr[sz]\b)",
    re.I,
)

COUNTRY_ALIASES: dict[str, list[str]] = {
    "ARE": ["UAE", "United Arab Emirates"],
    "GBR": ["United Kingdom", "British", "UK"],
    "USA": ["United States", "US", "American"],
    "CZE": ["Czechia", "Czech Republic"],
    "KOR": ["South Korea", "Republic of Korea", "Korean"],
    "PRK": ["North Korea", "DPRK"],
    "RUS": ["Russia", "Russian Federation"],
    "IRN": ["Iran", "Islamic Republic of Iran"],
    "SYR": ["Syria", "Syrian"],
    "LAO": ["Laos", "Lao"],
    "MDA": ["Moldova", "Republic of Moldova"],
    "MKD": ["North Macedonia", "Macedonia"],
    "SWZ": ["Eswatini", "Swaziland"],
    "CIV": ["Ivory Coast", "Côte d'Ivoire", "Cote d'Ivoire"],
    "COD": ["DR Congo", "Democratic Republic of the Congo", "Congo-Kinshasa"],
    "COG": ["Republic of the Congo", "Congo-Brazzaville"],
    "TWN": ["Taiwan", "Republic of China"],
    "PSE": ["Palestine", "Palestinian"],
    "VAT": ["Vatican", "Holy See"],
    "HKG": ["Hong Kong"],
    "MAC": ["Macao", "Macau"],
    "XKX": ["Kosovo"],
    "TLS": ["Timor-Leste", "East Timor"],
    "MMR": ["Myanmar", "Burma"],
    "VNM": ["Vietnam", "Viet Nam"],
    "BOL": ["Bolivia"],
    "VEN": ["Venezuela"],
    "TZA": ["Tanzania"],
    "FSM": ["Micronesia", "Federated States of Micronesia"],
    "STP": ["Sao Tome", "São Tomé"],
    "CPV": ["Cabo Verde", "Cape Verde"],
    "GNQ": ["Equatorial Guinea"],
    "GNB": ["Guinea-Bissau"],
    "CAF": ["Central African Republic"],
    "BIH": ["Bosnia", "Bosnia and Herzegovina"],
    "ATG": ["Antigua and Barbuda", "Antigua"],
    "KNA": ["Saint Kitts", "St Kitts"],
    "LCA": ["Saint Lucia", "St Lucia"],
    "VCT": ["Saint Vincent", "St Vincent"],
    "TTO": ["Trinidad and Tobago"],
    "PNG": ["Papua New Guinea"],
    "SLB": ["Solomon Islands"],
    "WSM": ["Samoa"],
    "BRN": ["Brunei"],
    "MYS": ["Malaysia"],
    "SGP": ["Singapore"],
    "NLD": ["Netherlands", "Dutch"],
    "CHE": ["Switzerland", "Swiss"],
    "DEU": ["Germany", "German"],
    "FRA": ["France", "French"],
    "ESP": ["Spain", "Spanish"],
    "ITA": ["Italy", "Italian"],
    "JPN": ["Japan", "Japanese"],
    "CHN": ["China", "Chinese"],
    "IND": ["India", "Indian"],
    "EGY": ["Egypt", "Egyptian"],
    "SAU": ["Saudi Arabia", "Saudi"],
    "TUR": ["Turkey", "Türkiye", "Turkish"],
    "UKR": ["Ukraine", "Ukrainian"],
    "POL": ["Poland", "Polish"],
    "SWE": ["Sweden", "Swedish"],
    "NOR": ["Norway", "Norwegian"],
    "DNK": ["Denmark", "Danish"],
    "FIN": ["Finland", "Finnish"],
    "IRL": ["Ireland", "Irish"],
    "NZL": ["New Zealand"],
    "AUS": ["Australia", "Australian"],
    "CAN": ["Canada", "Canadian"],
    "BRA": ["Brazil", "Brazilian"],
    "MEX": ["Mexico", "Mexican"],
    "ZAF": ["South Africa", "South African"],
    "ISR": ["Israel", "Israeli"],
    "PSE": ["Palestine", "Palestinian Authority"],
}

COMPETITOR_DOMAINS = (
    "passportindex.org",
    "visaIndex.com",
    "visaindex.com",
    "henleyglobal.com",
    "henley-partners.com",
    "pinterest.com",
    "pinimg.com",
    "google.com/imgres",
    "ggpht.com",
)

_last_request_at = 0.0


def utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def strip_html(value: str | None) -> str:
    if not value:
        return ""
    text = re.sub(r"<[^>]+>", " ", value)
    text = html.unescape(text)
    return re.sub(r"\s+", " ", text).strip()


def ensure_dirs() -> None:
    for path in (
        COVERS_ROOT,
        CACHE_DIR,
        ORIGINALS_DIR,
        THUMBS_DIR,
        PUBLIC_ASSETS,
        MANUAL_REVIEW_PATH.parent,
    ):
        path.mkdir(parents=True, exist_ok=True)


def load_passports() -> list[dict[str, Any]]:
    payload = json.loads(INDEX_PATH.read_text(encoding="utf-8"))
    passports = payload["passports"]
    if len(passports) != 199:
        raise SystemExit(f"Expected 199 passports, found {len(passports)}")
    return passports


def empty_entry(passport: dict[str, Any]) -> dict[str, Any]:
    return {
        "iso3": passport["iso3"],
        "iso2": passport["iso2"],
        "countryNameEn": passport["nameEn"],
        "countryNameAr": passport["nameAr"],
        "status": "not_found",
        "commonsFileTitle": None,
        "commonsPageUrl": None,
        "originalFileUrl": None,
        "localFile": None,
        "author": None,
        "licenseName": None,
        "licenseUrl": None,
        "attributionText": None,
        "sourcePage": "https://commons.wikimedia.org/",
        "currentOrHistoric": "unknown",
        "passportType": "unknown",
        "imageDate": None,
        "resolution": None,
        "fileHash": None,
        "reviewedAt": utc_now(),
        "reviewNotes": "",
        "emblemRightsReviewRequired": True,
        "rejectionReason": None,
        "candidates": [],
    }


def load_manifest() -> dict[str, Any]:
    if MANIFEST_PATH.is_file():
        return json.loads(MANIFEST_PATH.read_text(encoding="utf-8"))
    return {
        "generatedAt": None,
        "source": "Wikimedia Commons API only",
        "userAgent": USER_AGENT,
        "entries": [],
    }


def save_manifest(manifest: dict[str, Any]) -> None:
    manifest["generatedAt"] = utc_now()
    MANIFEST_PATH.write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )


def rate_limit() -> None:
    global _last_request_at
    elapsed = time.monotonic() - _last_request_at
    if elapsed < MIN_INTERVAL_SEC:
        time.sleep(MIN_INTERVAL_SEC - elapsed)
    _last_request_at = time.monotonic()


def api_get(params: dict[str, Any], *, cache_key: str | None = None) -> dict[str, Any]:
    ensure_dirs()
    if cache_key:
        cache_path = CACHE_DIR / f"{cache_key}.json"
        if cache_path.is_file():
            return json.loads(cache_path.read_text(encoding="utf-8"))

    query = urllib.parse.urlencode({**params, "format": "json", "formatversion": "2"})
    url = f"{COMMONS_API}?{query}"
    last_error: Exception | None = None
    for attempt in range(1, MAX_RETRIES + 1):
        rate_limit()
        req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT, "Accept": "application/json"})
        try:
            with urllib.request.urlopen(req, timeout=REQUEST_TIMEOUT_SEC) as resp:
                data = json.loads(resp.read().decode("utf-8"))
            if cache_key:
                CACHE_DIR.joinpath(f"{cache_key}.json").write_text(
                    json.dumps(data, ensure_ascii=False),
                    encoding="utf-8",
                )
            return data
        except (urllib.error.HTTPError, urllib.error.URLError, TimeoutError, json.JSONDecodeError) as exc:
            last_error = exc
            time.sleep(min(8, attempt * 1.5))
    raise RuntimeError(f"Commons API failed after retries: {url} ({last_error})")


def search_queries(name_en: str, iso3: str) -> list[str]:
    aliases = COUNTRY_ALIASES.get(iso3, [])
    primary = name_en
    alt = aliases[0] if aliases and aliases[0].lower() != name_en.lower() else None
    queries = [
        f"{primary} passport cover",
        f"{primary} biometric passport",
        f"Passport of {primary}",
        f"{primary} passport",
    ]
    if alt:
        queries.append(f"{alt} passport cover")
    # Deduplicate while preserving order
    seen: set[str] = set()
    out: list[str] = []
    for q in queries:
        key = q.lower()
        if key not in seen:
            seen.add(key)
            out.append(q)
    return out


def commons_search(query: str) -> list[dict[str, Any]]:
    cache_key = "search_" + hashlib.sha1(query.encode("utf-8")).hexdigest()[:20]
    data = api_get(
        {
            "action": "query",
            "list": "search",
            "srsearch": query,
            "srnamespace": 6,
            "srlimit": SEARCH_LIMIT,
            "srprop": "snippet|timestamp|size",
        },
        cache_key=cache_key,
    )
    return list(data.get("query", {}).get("search", []) or [])


def fetch_imageinfo(titles: list[str]) -> dict[str, dict[str, Any]]:
    result: dict[str, dict[str, Any]] = {}
    for i in range(0, len(titles), 40):
        chunk = titles[i : i + 40]
        joined = "|".join(chunk)
        cache_key = "ii_" + hashlib.sha1(joined.encode("utf-8")).hexdigest()[:24]
        data = api_get(
            {
                "action": "query",
                "prop": "imageinfo|categories",
                "titles": joined,
                "iiprop": "url|size|mime|extmetadata|sha1|timestamp",
                "iiextmetadatafilter": "|".join(
                    [
                        "LicenseShortName",
                        "LicenseUrl",
                        "License",
                        "Artist",
                        "Credit",
                        "Attribution",
                        "AttributionRequired",
                        "ImageDescription",
                        "ObjectName",
                        "DateTimeOriginal",
                        "UsageTerms",
                        "Copyrighted",
                        "Permission",
                    ]
                ),
                "cllimit": 50,
            },
            cache_key=cache_key,
        )
        for page in data.get("query", {}).get("pages", []) or []:
            title = page.get("title")
            if not title or page.get("missing"):
                continue
            infos = page.get("imageinfo") or []
            if not infos:
                continue
            info = infos[0]
            meta = info.get("extmetadata") or {}
            cats = [c.get("title", "") for c in (page.get("categories") or [])]
            result[title] = {
                "title": title,
                "pageUrl": f"https://commons.wikimedia.org/wiki/{urllib.parse.quote(title.replace(' ', '_'))}",
                "url": info.get("url"),
                "descriptionUrl": info.get("descriptionurl"),
                "width": info.get("width"),
                "height": info.get("height"),
                "size": info.get("size"),
                "mime": info.get("mime"),
                "sha1": info.get("sha1"),
                "timestamp": info.get("timestamp"),
                "categories": cats,
                "licenseShort": strip_html((meta.get("LicenseShortName") or {}).get("value")),
                "licenseUrl": strip_html((meta.get("LicenseUrl") or {}).get("value")),
                "licenseGuess": strip_html((meta.get("License") or {}).get("value")),
                "artist": strip_html((meta.get("Artist") or {}).get("value")),
                "credit": strip_html((meta.get("Credit") or {}).get("value")),
                "attribution": strip_html((meta.get("Attribution") or {}).get("value")),
                "description": strip_html((meta.get("ImageDescription") or {}).get("value")),
                "objectName": strip_html((meta.get("ObjectName") or {}).get("value")),
                "dateOriginal": strip_html((meta.get("DateTimeOriginal") or {}).get("value")),
                "usageTerms": strip_html((meta.get("UsageTerms") or {}).get("value")),
                "copyrighted": strip_html((meta.get("Copyrighted") or {}).get("value")),
                "permission": strip_html((meta.get("Permission") or {}).get("value")),
            }
    return result


def license_allowed(license_name: str | None, usage_terms: str | None = None) -> tuple[bool, str]:
    blob = f"{license_name or ''} {usage_terms or ''}".strip()
    if not blob:
        return False, "missing_license"
    lower = blob.lower()
    for token in REJECT_LICENSE_TOKENS:
        if token in lower and "public domain" not in lower:
            # Allow "Copyrighted: False" style metadata separately via short name.
            if token == "copyrighted" and re.search(r"copyrighted\s*[:=]?\s*false", lower):
                continue
            return False, f"rejected_license_token:{token}"
    # Normalize common short names
    short = (license_name or "").strip()
    if short.lower() in {"pd", "public domain", "cc0", "cc-zero", "cc0 1.0"}:
        return True, "allowlisted"
    if re.fullmatch(r"cc[\s\-]?by(\s|-)?sa?(\s|-)?\d(\.\d)?", short, flags=re.I):
        return True, "allowlisted"
    if re.fullmatch(r"cc[\s\-]?by(\s|-)?\d(\.\d)?", short, flags=re.I):
        return True, "allowlisted"
    for pattern in ALLOWED_LICENSE_PATTERNS:
        if pattern.search(short):
            # Extra guard against NC/ND slipping past BY prefix.
            if re.search(r"\bnc\b|\bnd\b", short, flags=re.I):
                return False, "noncommercial_or_nd"
            return True, "allowlisted"
    return False, "license_not_allowlisted"


def classify_candidate(info: dict[str, Any], country_name: str, aliases: list[str], iso3: str = "") -> dict[str, Any]:
    title = info["title"]
    desc = info.get("description") or ""
    cats = " ".join(info.get("categories") or [])
    blob = f"{title} {desc} {cats} {info.get('objectName') or ''}"
    blob_l = blob.lower()

    reasons: list[str] = []
    hard_reject = False

    if NEGATIVE_TITLE.search(blob):
        hard_reject = True
        reasons.append("negative_content_signal")
    if PERSONAL_DATA_RE.search(blob):
        hard_reject = True
        reasons.append("personal_data_signal")
    for domain in COMPETITOR_DOMAINS:
        if domain in blob_l or domain in (info.get("credit") or "").lower():
            hard_reject = True
            reasons.append(f"competitor_or_blocked_source:{domain}")
    for token in CROSS_COUNTRY_BLOCKERS.get(iso3, ()):
        if token in blob_l:
            hard_reject = True
            reasons.append(f"cross_country_blocker:{token}")
            break

    passport_type = "ordinary"
    if DIPLOMATIC_RE.search(blob):
        passport_type = "diplomatic" if "diplomatic" in blob.lower() else "service"
        reasons.append("non_ordinary_type")

    era = "current"
    if HISTORIC_RE.search(blob):
        era = "historic"
        reasons.append("historic_signal")

    looks_cover = bool(COVER_POSITIVE.search(blob))
    has_passport_word = bool(PASSPORT_WORD.search(blob))
    # Prefer exact country tokens; require at least one.
    name_tokens = [n for n in [country_name, *aliases] if n]
    country_hit = any(re.search(re.escape(n), blob, flags=re.I) for n in name_tokens)
    country_in_title = any(re.search(re.escape(n), title, flags=re.I) for n in name_tokens)
    vague_title = bool(
        re.search(r"passport\s*\(\d+\)", title, flags=re.I)
        or re.search(r"^File:Passport\b", title, flags=re.I)
        and not country_in_title
    )
    if vague_title:
        reasons.append("vague_title")
    # Explicit early-year markers in the title (avoid matching modern 20xx).
    if re.search(r"\b(1[6-9]\d{2}|190\d|191\d|192\d|193\d|194\d|195\d)\b", title):
        era = "historic"
        reasons.append("early_year_in_title")

    width = int(info.get("width") or 0)
    height = int(info.get("height") or 0)
    if width and height and (width < MIN_WIDTH or height < MIN_HEIGHT):
        hard_reject = True
        reasons.append("low_resolution")

    aspect = (width / height) if width and height else 0.0
    # Ordinary passport covers are portrait-ish; reject landscape maps/charts.
    portrait_ok = 0.52 <= aspect <= 0.95 if aspect else False
    if aspect and not portrait_ok:
        hard_reject = True
        reasons.append(f"non_portrait_aspect:{aspect:.2f}")

    license_ok, license_reason = license_allowed(info.get("licenseShort"), info.get("usageTerms"))
    if not license_ok:
        hard_reject = True
        reasons.append(license_reason)

    author = info.get("artist") or info.get("credit") or ""
    if not author:
        hard_reject = True
        reasons.append("unknown_author")

    mime = (info.get("mime") or "").lower()
    if mime and not mime.startswith("image/"):
        hard_reject = True
        reasons.append("not_image")

    confidence = 0
    if looks_cover:
        confidence += 40
    elif has_passport_word:
        confidence += 15
    if country_hit:
        confidence += 25
    if passport_type == "ordinary":
        confidence += 10
    if era == "current":
        confidence += 10
    if license_ok:
        confidence += 10
    if portrait_ok:
        confidence += 10
    if width >= 400 and height >= 500:
        confidence += 5
    if hard_reject:
        confidence = min(confidence, 20)

    eligible = (
        not hard_reject
        and license_ok
        and bool(author)
        and has_passport_word
        and country_hit
        and passport_type == "ordinary"
        and portrait_ok
    )
    auto_eligible = (
        eligible
        and looks_cover
        and era == "current"
        and country_in_title
        and not vague_title
    )

    return {
        "commonsFileTitle": title,
        "commonsPageUrl": info.get("pageUrl") or info.get("descriptionUrl"),
        "originalFileUrl": info.get("url"),
        "author": author,
        "licenseName": info.get("licenseShort") or None,
        "licenseUrl": info.get("licenseUrl") or None,
        "description": desc[:500],
        "imageDate": info.get("dateOriginal") or info.get("timestamp"),
        "resolution": {"width": width, "height": height, "bytes": info.get("size")},
        "passportType": passport_type,
        "currentOrHistoric": era,
        "confidence": confidence,
        "eligible": eligible,
        "autoEligible": auto_eligible,
        "looksCover": looks_cover,
        "reasons": reasons,
        "sha1": info.get("sha1"),
    }


def attribution_text(author: str, title: str, license_name: str, page_url: str) -> str:
    return (
        f'"{title}" by {author}, via Wikimedia Commons, licensed under {license_name}. '
        f"Source: {page_url}"
    )


def decide_status(candidates: list[dict[str, Any]]) -> tuple[str, dict[str, Any] | None, str]:
    eligible = [c for c in candidates if c.get("eligible")]
    if not eligible:
        # Distinguish rejected vs not found
        if not candidates:
            return "not_found", None, "no_commons_hits"
        if any("license" in " ".join(c.get("reasons") or []) for c in candidates):
            best = max(candidates, key=lambda c: c.get("confidence", 0))
            return "rejected", best, "no_allowlisted_eligible_candidate"
        best = max(candidates, key=lambda c: c.get("confidence", 0))
        if best.get("confidence", 0) >= 30:
            return "needs_manual_review", best, "uncertain_candidate_needs_human_review"
        return "not_found", best, "no_suitable_passport_cover_candidate"

    auto = [c for c in eligible if c.get("autoEligible")]
    current_covers = [
        c
        for c in auto
        if c.get("currentOrHistoric") == "current" and c.get("looksCover")
    ]
    current_any = [c for c in eligible if c.get("currentOrHistoric") == "current"]
    historic_only = [c for c in eligible if c.get("currentOrHistoric") == "historic"]

    if len(current_covers) == 1:
        chosen = current_covers[0]
        # Require strong cover evidence before auto-publishing.
        if chosen.get("confidence", 0) >= 85 and chosen.get("looksCover"):
            return "approved", chosen, "single_current_ordinary_cover"
        return "needs_manual_review", chosen, "single_candidate_below_auto_threshold"

    if len(current_covers) > 1:
        # Multiple valid current covers — do not auto-pick unless one dominates.
        ranked = sorted(current_covers, key=lambda c: c.get("confidence", 0), reverse=True)
        if (
            ranked[0]["confidence"] >= ranked[1]["confidence"] + 25
            and ranked[0]["confidence"] >= 95
            and ranked[0].get("looksCover")
        ):
            return "approved", ranked[0], "dominant_current_ordinary_cover"
        return "needs_manual_review", ranked[0], "multiple_valid_current_covers"

    if len(current_any) == 1:
        chosen = current_any[0]
        # Without explicit cover wording, never auto-approve.
        return "needs_manual_review", chosen, "current_but_cover_uncertain"

    if len(current_any) > 1:
        ranked = sorted(current_any, key=lambda c: c.get("confidence", 0), reverse=True)
        return "needs_manual_review", ranked[0], "multiple_current_candidates"

    if historic_only:
        ranked = sorted(historic_only, key=lambda c: c.get("confidence", 0), reverse=True)
        return "needs_manual_review", ranked[0], "historic_only_never_silent_current"

    ranked = sorted(eligible, key=lambda c: c.get("confidence", 0), reverse=True)
    return "needs_manual_review", ranked[0], "eligible_but_uncertain"


def apply_choice(entry: dict[str, Any], status: str, chosen: dict[str, Any] | None, note: str) -> None:
    entry["status"] = status
    entry["reviewNotes"] = note
    entry["reviewedAt"] = utc_now()
    entry["emblemRightsReviewRequired"] = True
    if not chosen:
        entry["rejectionReason"] = note if status in {"rejected", "not_found"} else None
        return
    entry["commonsFileTitle"] = chosen.get("commonsFileTitle")
    entry["commonsPageUrl"] = chosen.get("commonsPageUrl")
    entry["originalFileUrl"] = chosen.get("originalFileUrl")
    entry["author"] = chosen.get("author")
    entry["licenseName"] = chosen.get("licenseName")
    entry["licenseUrl"] = chosen.get("licenseUrl")
    entry["imageDate"] = chosen.get("imageDate")
    entry["resolution"] = chosen.get("resolution")
    entry["passportType"] = chosen.get("passportType") or "unknown"
    entry["currentOrHistoric"] = chosen.get("currentOrHistoric") or "unknown"
    if entry["author"] and entry["licenseName"] and entry["commonsPageUrl"]:
        entry["attributionText"] = attribution_text(
            entry["author"],
            entry["commonsFileTitle"] or "Passport cover",
            entry["licenseName"],
            entry["commonsPageUrl"],
        )
    if status == "rejected":
        entry["rejectionReason"] = note
    elif status == "not_found":
        entry["rejectionReason"] = note
    else:
        entry["rejectionReason"] = None
    if status == "approved":
        iso3 = entry["iso3"].lower()
        entry["localFile"] = f"/assets/passports/{iso3}.webp"


def audit_country(passport: dict[str, Any], *, use_cache: bool = True) -> dict[str, Any]:
    entry = empty_entry(passport)
    iso3 = passport["iso3"]
    name = passport["nameEn"]
    aliases = COUNTRY_ALIASES.get(iso3, [])
    titles: list[str] = []
    seen: set[str] = set()
    for query in search_queries(name, iso3):
        try:
            hits = commons_search(query)
        except Exception as exc:  # noqa: BLE001
            entry["reviewNotes"] = f"search_error:{exc}"
            continue
        for hit in hits:
            title = hit.get("title")
            if not title or title in seen:
                continue
            seen.add(title)
            titles.append(title)
    if not titles:
        entry["status"] = "not_found"
        entry["rejectionReason"] = "no_commons_search_hits"
        entry["reviewNotes"] = "no_commons_search_hits"
        return entry

    try:
        infos = fetch_imageinfo(titles)
    except Exception as exc:  # noqa: BLE001
        entry["status"] = "needs_manual_review"
        entry["reviewNotes"] = f"imageinfo_error:{exc}"
        return entry

    candidates = []
    for title in titles:
        info = infos.get(title)
        if not info:
            continue
        candidates.append(classify_candidate(info, name, aliases, iso3))
    entry["candidates"] = candidates[:25]
    status, chosen, note = decide_status(candidates)
    apply_choice(entry, status, chosen, note)
    return entry


def download_bytes(url: str) -> bytes:
    last_error: Exception | None = None
    for attempt in range(1, MAX_RETRIES + 1):
        rate_limit()
        req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
        try:
            with urllib.request.urlopen(req, timeout=REQUEST_TIMEOUT_SEC) as resp:
                return resp.read()
        except (urllib.error.HTTPError, urllib.error.URLError, TimeoutError) as exc:
            last_error = exc
            time.sleep(min(8, attempt * 1.5))
    raise RuntimeError(f"Download failed: {url} ({last_error})")


def process_approved_image(entry: dict[str, Any], *, overwrite: bool = False) -> None:
    from PIL import Image
    from io import BytesIO

    if entry.get("status") != "approved":
        return
    url = entry.get("originalFileUrl")
    if not url:
        entry["status"] = "needs_manual_review"
        entry["reviewNotes"] = "approved_missing_original_url"
        return

    iso3 = entry["iso3"]
    out_name = f"{iso3.lower()}.webp"
    public_path = PUBLIC_ASSETS / out_name
    if public_path.is_file() and not overwrite:
        raw = public_path.read_bytes()
        entry["fileHash"] = hashlib.sha256(raw).hexdigest()
        entry["localFile"] = f"/assets/passports/{out_name}"
        with Image.open(BytesIO(raw)) as im:
            entry["resolution"] = {
                "width": im.width,
                "height": im.height,
                "bytes": len(raw),
                "derivative": True,
            }
        return

    original = download_bytes(url)
    original_hash = hashlib.sha256(original).hexdigest()
    archive_dir = ORIGINALS_DIR / iso3
    archive_dir.mkdir(parents=True, exist_ok=True)
    # Keep original extension when possible
    suffix = Path(urllib.parse.urlparse(url).path).suffix or ".bin"
    archive_path = archive_dir / f"original{suffix}"
    archive_path.write_bytes(original)
    (archive_dir / "source.json").write_text(
        json.dumps(
            {
                "iso3": iso3,
                "originalFileUrl": url,
                "commonsPageUrl": entry.get("commonsPageUrl"),
                "commonsFileTitle": entry.get("commonsFileTitle"),
                "sha256": original_hash,
                "archivedAt": utc_now(),
            },
            ensure_ascii=False,
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )

    with Image.open(BytesIO(original)) as im:
        im = im.convert("RGBA") if im.mode in {"P", "RGBA"} else im.convert("RGB")
        w, h = im.size
        if w < MIN_WIDTH or h < MIN_HEIGHT:
            entry["status"] = "rejected"
            entry["rejectionReason"] = "downloaded_image_too_small"
            entry["localFile"] = None
            return
        # Never upscale
        scale = min(1.0, MAX_DERIV_EDGE / max(w, h))
        if scale < 1.0:
            new_size = (max(1, int(w * scale)), max(1, int(h * scale)))
            im = im.resize(new_size, Image.Resampling.LANCZOS)
        # Conservative center crop only if extreme panorama (unlikely for covers)
        w, h = im.size
        aspect = w / h if h else 1
        if aspect > 1.2:
            # Keep most of image; slight crop toward square-ish passport ratio ~3:4
            target = h * 0.78
            left = max(0, int((w - target) / 2))
            im = im.crop((left, 0, min(w, left + int(target)), h))

        buf = BytesIO()
        save_kwargs = {"format": "WEBP", "quality": WEBP_QUALITY, "method": 6}
        # Strip metadata by saving fresh pixels only (no exif kw)
        if im.mode == "RGBA":
            im.save(buf, **save_kwargs)
        else:
            im.convert("RGB").save(buf, **save_kwargs)
        data = buf.getvalue()
        quality = WEBP_QUALITY
        while len(data) > MAX_DERIV_BYTES and quality > 55:
            quality -= 7
            buf = BytesIO()
            im.convert("RGB").save(buf, format="WEBP", quality=quality, method=6)
            data = buf.getvalue()

    PUBLIC_ASSETS.mkdir(parents=True, exist_ok=True)
    public_path.write_bytes(data)
    entry["fileHash"] = hashlib.sha256(data).hexdigest()
    entry["localFile"] = f"/assets/passports/{out_name}"
    with Image.open(BytesIO(data)) as dim:
        entry["resolution"] = {
            "width": dim.width,
            "height": dim.height,
            "bytes": len(data),
            "originalSha256": original_hash,
            "derivative": True,
        }


def write_thumb_for_review(entry: dict[str, Any]) -> str | None:
    """Optional local thumb for manual-review report (from Commons thumb URL when possible)."""
    if not entry.get("originalFileUrl"):
        return None
    try:
        from PIL import Image
        from io import BytesIO

        raw = download_bytes(entry["originalFileUrl"])
        with Image.open(BytesIO(raw)) as im:
            im = im.convert("RGB")
            im.thumbnail((160, 200))
            out = THUMBS_DIR / f"{entry['iso3'].lower()}.jpg"
            im.save(out, format="JPEG", quality=70)
            return str(out.relative_to(ROOT)).replace("\\", "/")
    except Exception:  # noqa: BLE001
        return None


def summarize(entries: list[dict[str, Any]]) -> dict[str, Any]:
    counts = {
        "approved": 0,
        "needs_manual_review": 0,
        "not_found": 0,
        "rejected": 0,
    }
    licenses: dict[str, int] = {}
    current_ordinary = 0
    historic_unknown = 0
    missing: list[str] = []
    emblem_risks: list[str] = []
    for e in entries:
        status = e.get("status") or "not_found"
        counts[status] = counts.get(status, 0) + 1
        if status != "approved":
            missing.append(e["iso3"])
        else:
            lic = e.get("licenseName") or "unknown"
            licenses[lic] = licenses.get(lic, 0) + 1
            if e.get("currentOrHistoric") == "current" and e.get("passportType") == "ordinary":
                current_ordinary += 1
            else:
                historic_unknown += 1
            if e.get("emblemRightsReviewRequired"):
                emblem_risks.append(e["iso3"])
        if status == "needs_manual_review" and e.get("currentOrHistoric") in {"historic", "unknown"}:
            historic_unknown += 1
    return {
        "passportsAudited": len(entries),
        "counts": counts,
        "currentOrdinaryApproved": current_ordinary,
        "historicOrUnknownSignals": historic_unknown,
        "licenseDistribution": dict(sorted(licenses.items(), key=lambda kv: (-kv[1], kv[0]))),
        "countriesWithoutApproved": missing,
        "emblemRightsReviewRequiredCount": len(emblem_risks),
        "emblemRightsReviewIso3": emblem_risks,
    }


def write_audit_md(manifest: dict[str, Any], summary: dict[str, Any]) -> None:
    counts = summary["counts"]
    lines = [
        "# Passport cover audit",
        "",
        f"- Generated: `{manifest.get('generatedAt')}`",
        "- Discovery source: Wikimedia Commons API only",
        f"- User-Agent: `{USER_AGENT}`",
        "",
        "## Counts",
        "",
        f"| Status | Count |",
        f"| --- | ---: |",
        f"| approved | {counts.get('approved', 0)} |",
        f"| needs_manual_review | {counts.get('needs_manual_review', 0)} |",
        f"| not_found | {counts.get('not_found', 0)} |",
        f"| rejected | {counts.get('rejected', 0)} |",
        f"| **total** | **{summary['passportsAudited']}** |",
        "",
        f"- Current ordinary approved covers: **{summary['currentOrdinaryApproved']}**",
        f"- Historic/unknown signals (approved non-current + review historic): **{summary['historicOrUnknownSignals']}**",
        f"- Emblem/official-insignia legal-review required (all approved): **{summary['emblemRightsReviewRequiredCount']}**",
        "",
        "## License distribution (approved)",
        "",
    ]
    if summary["licenseDistribution"]:
        lines += ["| License | Count |", "| --- | ---: |"]
        for lic, n in summary["licenseDistribution"].items():
            lines.append(f"| {lic} | {n} |")
    else:
        lines.append("_No approved licenses yet._")
    lines += [
        "",
        "## Countries without an approved cover",
        "",
    ]
    missing = summary["countriesWithoutApproved"]
    if missing:
        lines.append(", ".join(missing))
    else:
        lines.append("_None._")
    lines += [
        "",
        "## Notes",
        "",
        "- Auto-approval is conservative: uncertain, historic-only, or multi-candidate matches stay in `needs_manual_review`.",
        "- Photograph licenses do not clear separate state-emblem / passport-reproduction restrictions.",
        "- Production assets are written only with `--download-approved`.",
        "",
    ]
    AUDIT_PATH.write_text("\n".join(lines) + "\n", encoding="utf-8")


def write_manual_review_report(entries: list[dict[str, Any]], *, fetch_thumbs: bool = False) -> None:
    rows = [e for e in entries if e.get("status") == "needs_manual_review"]
    lines = [
        "# Manual review queue",
        "",
        f"Entries: **{len(rows)}**",
        "",
        "Open each Commons file page, confirm it is a clear **current ordinary front cover**, "
        "verify commercial-use license metadata, and check for personal data before promoting to approved.",
        "",
        "| ISO3 | Country | Thumb | Commons | License | Era | Type | Notes |",
        "| --- | --- | --- | --- | --- | --- | --- | --- |",
    ]
    for e in sorted(rows, key=lambda x: x["iso3"]):
        thumb = ""
        if fetch_thumbs:
            path = write_thumb_for_review(e)
            if path:
                thumb = f"![](../../{path})"
        page = e.get("commonsPageUrl") or ""
        link = f"[file]({page})" if page else "—"
        lines.append(
            f"| {e['iso3']} | {e['countryNameEn']} | {thumb or '—'} | {link} | "
            f"{e.get('licenseName') or '—'} | {e.get('currentOrHistoric')} | "
            f"{e.get('passportType')} | {e.get('reviewNotes') or ''} |"
        )
    MANUAL_REVIEW_PATH.write_text("\n".join(lines) + "\n", encoding="utf-8")


def write_covers_runtime_meta(entries: list[dict[str, Any]]) -> None:
    import passport_cover_config as cover_cfg  # local import avoids cycles at module load

    if not cover_cfg.REAL_PASSPORT_COVERS_ENABLED:
        PUBLIC_COVERS_META.parent.mkdir(parents=True, exist_ok=True)
        PUBLIC_COVERS_META.write_text(
            json.dumps(
                {
                    "generatedAt": utc_now(),
                    "source": "Wikimedia Commons (gated)",
                    "realPassportCoversEnabled": False,
                    "count": 0,
                    "covers": {},
                    "note": "Real passport covers disabled publicly until emblem review is cleared.",
                },
                ensure_ascii=False,
                indent=2,
            )
            + "\n",
            encoding="utf-8",
        )
        return
    covers: dict[str, Any] = {}
    for e in entries:
        if e.get("status") != "approved" or not e.get("localFile"):
            continue
        if e.get("deploymentStatus") != "cleared":
            continue
        if e.get("emblemRightsReviewRequired"):
            continue
        local = ROOT / "public" / e["localFile"].lstrip("/")
        if not local.is_file():
            continue
        res = e.get("resolution") or {}
        covers[e["iso3"]] = {
            "iso3": e["iso3"],
            "iso2": e["iso2"],
            "localFile": e["localFile"],
            "width": res.get("width"),
            "height": res.get("height"),
            "fileHash": e.get("fileHash"),
            "author": e.get("author"),
            "licenseName": e.get("licenseName"),
            "licenseUrl": e.get("licenseUrl"),
            "attributionText": e.get("attributionText"),
            "commonsPageUrl": e.get("commonsPageUrl"),
            "commonsFileTitle": e.get("commonsFileTitle"),
            "currentOrHistoric": e.get("currentOrHistoric"),
            "passportType": e.get("passportType"),
            "deploymentStatus": e.get("deploymentStatus"),
            "emblemRightsReviewRequired": e.get("emblemRightsReviewRequired", True),
            "altEn": f"Photograph of the {e['countryNameEn']} passport cover (Wikimedia Commons)",
            "altAr": f"صورة غلاف جواز سفر {e['countryNameAr']} (ويكيميديا كومنز)",
        }
    PUBLIC_COVERS_META.parent.mkdir(parents=True, exist_ok=True)
    PUBLIC_COVERS_META.write_text(
        json.dumps(
            {
                "generatedAt": utc_now(),
                "source": "Wikimedia Commons (approved subset only)",
                "realPassportCoversEnabled": True,
                "count": len(covers),
                "covers": covers,
            },
            ensure_ascii=False,
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )


def write_attributions_html(entries: list[dict[str, Any]]) -> None:
    approved = [e for e in entries if e.get("status") == "approved" and e.get("localFile")]
    rows_en = []
    rows_ar = []
    for e in sorted(approved, key=lambda x: x["countryNameEn"]):
        lic = e.get("licenseName") or "—"
        lic_url = e.get("licenseUrl") or "#"
        page = e.get("commonsPageUrl") or "#"
        rows_en.append(
            "<tr>"
            f"<td>{html.escape(e['countryNameEn'])} ({e['iso3']})</td>"
            f"<td>{html.escape(e.get('author') or '—')}</td>"
            f"<td><a href=\"{html.escape(lic_url)}\">{html.escape(lic)}</a></td>"
            f"<td><a href=\"{html.escape(page)}\">{html.escape(e.get('commonsFileTitle') or 'Commons file')}</a></td>"
            f"<td>{html.escape(e.get('attributionText') or '')}</td>"
            "</tr>"
        )
        rows_ar.append(
            "<tr>"
            f"<td>{html.escape(e['countryNameAr'])} ({e['iso3']})</td>"
            f"<td>{html.escape(e.get('author') or '—')}</td>"
            f"<td><a href=\"{html.escape(lic_url)}\">{html.escape(lic)}</a></td>"
            f"<td><a href=\"{html.escape(page)}\">{html.escape(e.get('commonsFileTitle') or 'ملف كومنز')}</a></td>"
            f"<td dir=\"ltr\">{html.escape(e.get('attributionText') or '')}</td>"
            "</tr>"
        )
    theme_css = theme.THEME_CSS
    theme_js = theme.THEME_JS
    theme_btn = theme.theme_control_html()
    no_flash = theme.NO_FLASH_SCRIPT
    body = f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="utf-8"/>
  {no_flash}
  <meta name="viewport" content="width=device-width, initial-scale=1"/>
  <meta name="robots" content="noindex, follow"/>
  <title>Mir’ah | Passport image attributions</title>
  <link rel="canonical" href="https://miraah.mirapp.workers.dev/passport/image-attributions.html"/>
  <meta name="theme-color" content="#07111f"/>
  <link rel="icon" href="/favicon.svg" type="image/svg+xml"/>
  <link rel="icon" type="image/png" sizes="16x16" href="/favicon-16x16.png"/>
  <link rel="icon" type="image/png" sizes="32x32" href="/favicon-32x32.png"/>
  <link rel="apple-touch-icon" sizes="180x180" href="/apple-touch-icon.png"/>
  <link rel="manifest" href="/site.webmanifest"/>
  <style>
{theme_css}
    a{{color:var(--brand-cyan)}}
    body{{margin:0;background:var(--bg);color:var(--text);font-family:Georgia,"Times New Roman",serif;line-height:1.6}}
    .shell{{max-width:980px;margin:auto;padding:28px 18px 60px}}
    h1,h2{{font-family:system-ui,Segoe UI,sans-serif}}
    .topbar{{display:flex;justify-content:flex-end;gap:8px;margin-bottom:12px}}
    .panel{{background:var(--surface);border:1px solid var(--border);border-radius:16px;padding:18px;margin:18px 0}}
    table{{width:100%;border-collapse:collapse;font-size:13px}}
    th,td{{border-top:1px solid var(--border);padding:10px;vertical-align:top;text-align:start}}
    th{{color:var(--text-muted);font-weight:700}}
    .muted{{color:var(--text-muted)}}
    .tabs button{{margin-inline-end:8px;margin-bottom:10px;background:var(--surface-soft);border:1px solid var(--border);color:var(--text);padding:8px 12px;border-radius:10px;cursor:pointer}}
    .tabs button.active{{background:linear-gradient(135deg,var(--brand-cyan),var(--brand-blue-soft));color:var(--text-on-brand);border:0}}
    .btn{{border:1px solid var(--border);background:var(--surface-soft);color:var(--text);padding:9px 13px;border-radius:11px;cursor:pointer}}
    [hidden]{{display:none!important}}
  </style>
</head>
<body>
  <main class="shell">
    <div class="topbar">{theme_btn}</div>
    <p class="muted"><a href="./">← Passport power</a></p>
    <h1>Passport cover image attributions</h1>
    <p class="muted">Approved cover photographs are sourced only from Wikimedia Commons under commercial-use-compatible licenses. Mir’ah illustrations are used when no approved cover exists. Photograph licenses do not resolve separate restrictions on state emblems or passport reproduction.</p>
    <div class="tabs">
      <button type="button" class="active" data-lang="en">English</button>
      <button type="button" data-lang="ar">العربية</button>
    </div>
    <section id="panel-en" class="panel">
      <h2>License obligations</h2>
      <ul class="muted">
        <li>Keep author, title, source page, and license link visible for CC BY / CC BY-SA works.</li>
        <li>CC BY-SA share-alike obligations apply to adaptations of those images.</li>
        <li>Do not imply that a Mir’ah illustration is an official government reproduction.</li>
        <li>State emblem / official insignia rules may still require legal review even when the photograph is freely licensed.</li>
      </ul>
      <h2>Approved Commons covers ({len(approved)})</h2>
      <table>
        <thead><tr><th>Country</th><th>Author</th><th>License</th><th>Source</th><th>Attribution</th></tr></thead>
        <tbody>
          {''.join(rows_en) if rows_en else '<tr><td colspan="5">No approved covers yet.</td></tr>'}
        </tbody>
      </table>
      <h2>Fallback illustrations</h2>
      <p class="muted">Where no approved cover is available, the UI shows a Mir’ah-designed passport illustration. Attribution: <strong>Mir’ah illustration</strong>.</p>
    </section>
    <section id="panel-ar" class="panel" hidden dir="rtl" lang="ar">
      <h2>التزامات الترخيص</h2>
      <ul class="muted">
        <li>يجب إظهار المؤلف والعنوان وصفحة المصدر ورابط الرخصة لأعمال CC BY / CC BY-SA.</li>
        <li>تنطبق التزامات المشاركة بالمثل (ShareAlike) على التعديلات المشتقة من صور CC BY-SA.</li>
        <li>لا تُعرض رسوم مرآة على أنها نسخ رسمية حكومية.</li>
        <li>قد تتطلب شعارات الدولة والشارات الرسمية مراجعة قانونية منفصلة حتى مع ترخيص الصورة الحر.</li>
      </ul>
      <h2>أغلفة كومنز المعتمدة ({len(approved)})</h2>
      <table>
        <thead><tr><th>الدولة</th><th>المؤلف</th><th>الرخصة</th><th>المصدر</th><th>الإسناد</th></tr></thead>
        <tbody>
          {''.join(rows_ar) if rows_ar else '<tr><td colspan="5">لا توجد أغلفة معتمدة بعد.</td></tr>'}
        </tbody>
      </table>
      <h2>الرسوم البديلة</h2>
      <p class="muted">عند عدم توفر غلاف معتمد، تعرض الواجهة رسم جواز من تصميم مرآة. الإسناد: <strong>رسم توضيحي من مرآة</strong>.</p>
    </section>
  </main>
  <script>
{theme_js}
    initThemeControls();
    const buttons=[...document.querySelectorAll('.tabs button')];
    const en=document.getElementById('panel-en');
    const ar=document.getElementById('panel-ar');
    buttons.forEach(btn=>btn.addEventListener('click',()=>{{
      buttons.forEach(b=>b.classList.toggle('active',b===btn));
      const arMode=btn.dataset.lang==='ar';
      en.hidden=arMode; ar.hidden=!arMode;
      document.documentElement.lang=arMode?'ar':'en';
      document.documentElement.dir=arMode?'rtl':'ltr';
      if(typeof syncThemeControls==='function')syncThemeControls();
    }}));
  </script>
</body>
</html>
"""
    ATTRIBUTIONS_HTML.write_text(body, encoding="utf-8")


def production_asset_size_bytes() -> int:
    if not PUBLIC_ASSETS.is_dir():
        return 0
    return sum(p.stat().st_size for p in PUBLIC_ASSETS.glob("*.webp"))


def run_audit(
    *,
    only: str | None,
    resume: bool,
    download_approved: bool,
    overwrite: bool,
    report_thumbs: bool,
) -> dict[str, Any]:
    ensure_dirs()
    passports = load_passports()
    if only:
        only = only.upper()
        passports = [p for p in passports if p["iso3"] == only]
        if not passports:
            raise SystemExit(f"Unknown ISO3: {only}")

    manifest = load_manifest()
    by_iso = {e["iso3"]: e for e in manifest.get("entries", []) if "iso3" in e}

    total = len(passports)
    for idx, passport in enumerate(passports, start=1):
        iso3 = passport["iso3"]
        if resume and iso3 in by_iso:
            prev = by_iso[iso3]
            # Placeholders from partial runs use not_found with empty notes/candidates.
            audited = bool(prev.get("candidates")) or bool(prev.get("reviewNotes")) or prev.get(
                "status"
            ) in {"approved", "needs_manual_review", "rejected"}
            if audited and prev.get("status") in {
                "approved",
                "needs_manual_review",
                "not_found",
                "rejected",
            }:
                print(f"[{idx}/{total}] skip {iso3} (resume)", flush=True)
                continue
        print(f"[{idx}/{total}] audit {iso3} {passport['nameEn']}", flush=True)
        entry = audit_country(passport)
        by_iso[iso3] = entry
        # Persist incrementally for long runs
        all_codes = [p["iso3"] for p in load_passports()]
        manifest["entries"] = [by_iso[c] for c in all_codes if c in by_iso]
        # For partial --country runs, keep previous entries for other codes
        for code in all_codes:
            if code not in by_iso:
                # synthesize placeholder only when full audit not done yet
                continue
        save_manifest(manifest)

    # Ensure exactly 199 slots when full set present
    all_passports = load_passports()
    entries = []
    for p in all_passports:
        if p["iso3"] in by_iso:
            entries.append(by_iso[p["iso3"]])
        else:
            entries.append(empty_entry(p))
    manifest["entries"] = entries

    if download_approved:
        for entry in entries:
            if entry.get("status") == "approved":
                print(f"download/process {entry['iso3']}", flush=True)
                try:
                    process_approved_image(entry, overwrite=overwrite)
                except Exception as exc:  # noqa: BLE001
                    entry["status"] = "needs_manual_review"
                    entry["reviewNotes"] = f"download_failed:{exc}"
                    entry["localFile"] = None

    save_manifest(manifest)
    summary = summarize(entries)
    write_audit_md(manifest, summary)
    write_manual_review_report(entries, fetch_thumbs=report_thumbs)
    write_covers_runtime_meta(entries)
    write_attributions_html(entries)
    summary["totalProductionAssetBytes"] = production_asset_size_bytes()
    summary_path = COVERS_ROOT / "summary.json"
    summary_path.write_text(json.dumps(summary, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return summary


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    mode = parser.add_mutually_exclusive_group()
    mode.add_argument(
        "--audit-only",
        action="store_true",
        default=True,
        help="Audit Commons candidates only (default). Does not write production assets.",
    )
    mode.add_argument(
        "--download-approved",
        action="store_true",
        help="After audit, download and write approved production WebP assets.",
    )
    parser.add_argument("--country", help="Limit to one ISO3 code (e.g. MLT)")
    parser.add_argument("--resume", action="store_true", help="Skip ISO3 codes already present in manifest")
    parser.add_argument(
        "--report",
        action="store_true",
        help="Also fetch small local thumbnails for the manual-review report",
    )
    parser.add_argument(
        "--overwrite",
        action="store_true",
        help="Allow overwriting existing production WebP files (requires --download-approved)",
    )
    parser.add_argument(
        "--refresh-reports",
        action="store_true",
        help="Rebuild AUDIT.md / attributions / covers.json from existing manifest without re-querying Commons",
    )
    args = parser.parse_args(argv)
    if args.download_approved:
        args.audit_only = False
    return args


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    ensure_dirs()
    if args.refresh_reports:
        manifest = load_manifest()
        entries = manifest.get("entries") or []
        summary = summarize(entries)
        write_audit_md(manifest, summary)
        write_manual_review_report(entries, fetch_thumbs=args.report)
        write_covers_runtime_meta(entries)
        write_attributions_html(entries)
        summary["totalProductionAssetBytes"] = production_asset_size_bytes()
        (COVERS_ROOT / "summary.json").write_text(
            json.dumps(summary, ensure_ascii=False, indent=2) + "\n",
            encoding="utf-8",
        )
        print(json.dumps(summary, ensure_ascii=False, indent=2))
        return 0

    summary = run_audit(
        only=args.country,
        resume=args.resume,
        download_approved=args.download_approved,
        overwrite=args.overwrite,
        report_thumbs=args.report,
    )
    print(json.dumps(summary, ensure_ascii=False, indent=2))
    print(
        f"\nManifest: {MANIFEST_PATH}\nAudit: {AUDIT_PATH}\n"
        f"Approved: {summary['counts'].get('approved', 0)} / {summary['passportsAudited']}",
        flush=True,
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
