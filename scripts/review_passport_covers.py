#!/usr/bin/env python3
"""Manual passport-cover review: schema migration, targeted Commons search, local tool.

Local-only. Review UI lives under source-data/passport-covers/review/ (never public/).
Does not set deploymentStatus to cleared. Does not enable REAL_PASSPORT_COVERS_ENABLED.
"""

from __future__ import annotations

import argparse
import hashlib
import html
import json
import re
import sys
import urllib.parse
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

import audit_passport_covers as audit  # noqa: E402
import passport_cover_config as cfg  # noqa: E402
import passport_locale as locale  # noqa: E402

REVIEW_ROOT = audit.COVERS_ROOT / "review"
TOOL_DIR = REVIEW_ROOT / "tool"
THUMBS_DIR = REVIEW_ROOT / "thumbs"
DECISIONS_PATH = REVIEW_ROOT / "decisions.json"
REPORT_PATH = REVIEW_ROOT / "MANUAL_REVIEW_PASS.md"
FINAL_TABLE_PATH = REVIEW_ROOT / "FINAL_TABLE.md"
STAGED_DIR = audit.COVERS_ROOT / cfg.STAGED_ASSETS_SUBDIR

LOCAL_LANG_NAMES: dict[str, list[str]] = {
    "MLT": ["Malta", "Maltese", "Passaport Malti"],
    "SGP": ["Singapore", "Singapura"],
    "JPN": ["Japan", "Japanese", "日本", "日本国旅券"],
    "ESP": ["Spain", "Spanish", "España", "pasaporte español"],
    "DEU": ["Germany", "German", "Deutschland", "Reisepass"],
    "FRA": ["France", "French", "France", "passeport français"],
    "ITA": ["Italy", "Italian", "Italia", "passaporto"],
    "GBR": ["United Kingdom", "British", "UK passport"],
    "USA": ["United States", "US passport", "American passport"],
    "ARE": ["United Arab Emirates", "UAE", "إمارات", "جواز سفر"],
    "EGY": ["Egypt", "Egyptian", "مصر", "جواز سفر مصري"],
    "SAU": ["Saudi Arabia", "Saudi", "السعودية", "جواز سفر سعودي"],
    "MAR": ["Morocco", "Moroccan", "المغرب", "جواز سفر مغربي"],
}

# Documented public colour families (not official emblems) for Mir’ah fallbacks.
COVER_COLOR_FAMILIES: dict[str, str] = {
    # Burgundy / EU-style ordinary booklets (publicly described)
    "burgundy": "#6b1f33",
    "navy": "#0f2f5b",
    "green": "#1a4a32",
    "black": "#1a1a1a",
    "red": "#7a1c1c",
    "teal": "#0f4a4a",
}


def ensure_review_dirs() -> None:
    for path in (REVIEW_ROOT, TOOL_DIR, THUMBS_DIR, STAGED_DIR):
        path.mkdir(parents=True, exist_ok=True)


def default_dual_fields(entry: dict[str, Any]) -> None:
    """Attach dual license/deployment fields without auto-clearing deployment."""
    old = entry.get("status") or "not_found"
    if "imageLicenseStatus" not in entry:
        if old == "approved":
            entry["imageLicenseStatus"] = "approved"
        elif old == "rejected":
            entry["imageLicenseStatus"] = "rejected"
        else:
            entry["imageLicenseStatus"] = "unclear"
    if "deploymentStatus" not in entry:
        if entry["imageLicenseStatus"] == "approved":
            # Photo license OK still requires emblem/passport-reproduction review.
            entry["deploymentStatus"] = "emblem_review_required"
        elif entry["imageLicenseStatus"] == "rejected":
            entry["deploymentStatus"] = "blocked"
        else:
            entry["deploymentStatus"] = "editorial_review_required"
    # Never silently clear.
    if entry.get("deploymentStatus") == "cleared" and not entry.get("explicitClearance"):
        entry["deploymentStatus"] = "emblem_review_required"
    entry.setdefault("emblemRightsReviewRequired", True)
    entry.setdefault("coverVersion", None)
    entry.setdefault("validFrom", None)
    entry.setdefault("validUntil", None)
    entry.setdefault("currentnessEvidenceUrl", None)
    entry.setdefault("currentnessEvidenceType", None)
    entry.setdefault("currentnessConfidence", "low")
    entry.setdefault("visuallyReviewed", False)
    entry.setdefault("visualReviewNotes", "")
    entry.setdefault("objectClass", "unclear")
    entry.setdefault("stagedLocalFile", None)
    entry.setdefault("displayDecision", "fallback")
    # Public path only when gate on AND deployment cleared (never auto).
    if not cfg.REAL_PASSPORT_COVERS_ENABLED:
        entry["localFile"] = None


def migrate_manifest() -> dict[str, Any]:
    ensure_review_dirs()
    manifest = audit.load_manifest()
    for entry in manifest.get("entries", []):
        default_dual_fields(entry)
        # Relocate previously public derivatives to staged/
        iso3 = entry["iso3"].lower()
        staged = STAGED_DIR / f"{iso3}.webp"
        public = audit.PUBLIC_ASSETS / f"{iso3}.webp"
        if public.is_file():
            public.replace(staged)
        if staged.is_file() and entry.get("imageLicenseStatus") == "approved":
            entry["stagedLocalFile"] = str(staged.relative_to(ROOT)).replace("\\", "/")
            entry["fileHash"] = entry.get("fileHash") or hashlib.sha256(staged.read_bytes()).hexdigest()
        if not cfg.REAL_PASSPORT_COVERS_ENABLED:
            entry["localFile"] = None
    audit.save_manifest(manifest)
    return manifest


def targeted_queries(name_en: str, iso3: str) -> list[str]:
    base = audit.search_queries(name_en, iso3)
    extra = [
        f"current ordinary passport of {name_en}",
        f"biometric passport {name_en}",
        f"{name_en} passport cover",
        f"new passport {name_en}",
        f"ordinary passport {name_en}",
    ]
    for local in LOCAL_LANG_NAMES.get(iso3, []):
        extra.append(f"{local} passport")
        extra.append(f"{local} passport cover")
    aliases = audit.COUNTRY_ALIASES.get(iso3, [])
    for a in aliases[:2]:
        extra.append(f"ordinary passport {a}")
    seen: set[str] = set()
    out: list[str] = []
    for q in base + extra:
        key = q.lower()
        if key not in seen:
            seen.add(key)
            out.append(q)
    return out[:12]


def classify_object(candidate: dict[str, Any]) -> str:
    blob = " ".join(
        [
            candidate.get("commonsFileTitle") or "",
            candidate.get("description") or "",
            " ".join(candidate.get("reasons") or []),
        ]
    ).lower()
    if any(x in blob for x in ("stamp", "visa page", "biodata", "data page", "identity", "mrz", "personal")):
        return "identity_or_data_page"
    if candidate.get("passportType") in {"diplomatic", "service"}:
        return "diplomatic_or_service"
    if candidate.get("currentOrHistoric") == "historic":
        return "historic_passport"
    if candidate.get("looksCover") and candidate.get("passportType") == "ordinary":
        return "cover_only"
    if candidate.get("eligible"):
        return "ordinary_passport_uncertain"
    return "unclear_object"


def enrich_candidates(entry: dict[str, Any]) -> None:
    for cand in entry.get("candidates") or []:
        cand["objectClass"] = classify_object(cand)
        # Commons thumb via Special:FilePath (still Commons-only).
        title = cand.get("commonsFileTitle") or ""
        if title.startswith("File:"):
            name = title[5:]
            cand["thumbUrl"] = (
                "https://commons.wikimedia.org/wiki/Special:FilePath/"
                + urllib.parse.quote(name.replace(" ", "_"))
                + "?width=220"
            )
        else:
            cand["thumbUrl"] = None


def targeted_research_country(passport: dict[str, Any], entry: dict[str, Any]) -> dict[str, Any]:
    """Merge additional Commons search hits into entry candidates."""
    iso3 = passport["iso3"]
    name = passport["nameEn"]
    aliases = audit.COUNTRY_ALIASES.get(iso3, [])
    titles: list[str] = []
    seen = {c.get("commonsFileTitle") for c in (entry.get("candidates") or []) if c.get("commonsFileTitle")}
    for query in targeted_queries(name, iso3):
        try:
            hits = audit.commons_search(query)
        except Exception as exc:  # noqa: BLE001
            entry["reviewNotes"] = (entry.get("reviewNotes") or "") + f"|search_error:{exc}"
            continue
        for hit in hits:
            title = hit.get("title")
            if not title or title in seen:
                continue
            seen.add(title)
            titles.append(title)
    if titles:
        try:
            infos = audit.fetch_imageinfo(titles)
        except Exception as exc:  # noqa: BLE001
            entry["reviewNotes"] = (entry.get("reviewNotes") or "") + f"|ii_error:{exc}"
            infos = {}
        new_cands = []
        for title in titles:
            info = infos.get(title)
            if not info:
                continue
            new_cands.append(audit.classify_candidate(info, name, aliases, iso3))
        entry["candidates"] = (entry.get("candidates") or []) + new_cands
        # Cap stored candidates
        entry["candidates"] = entry["candidates"][:40]
    enrich_candidates(entry)
    entry["targetedSearchAt"] = audit.utc_now()
    default_dual_fields(entry)
    return entry


def download_thumb(candidate: dict[str, Any], iso3: str, index: int) -> str | None:
    url = candidate.get("originalFileUrl") or candidate.get("thumbUrl")
    if not url:
        return None
    try:
        from io import BytesIO

        from PIL import Image

        raw = audit.download_bytes(url)
        with Image.open(BytesIO(raw)) as im:
            im = im.convert("RGB")
            im.thumbnail((220, 300))
            safe = re.sub(r"[^A-Za-z0-9._-]+", "_", (candidate.get("commonsFileTitle") or f"c{index}")[:80])
            out = THUMBS_DIR / f"{iso3.lower()}_{index}_{safe[:40]}.jpg"
            im.save(out, format="JPEG", quality=72)
            rel = str(out.relative_to(REVIEW_ROOT)).replace("\\", "/")
            candidate["localThumb"] = rel
            return rel
    except Exception:  # noqa: BLE001
        return None


def load_decisions() -> dict[str, Any]:
    if DECISIONS_PATH.is_file():
        return json.loads(DECISIONS_PATH.read_text(encoding="utf-8"))
    return {"updatedAt": None, "decisions": {}}


def save_decisions(payload: dict[str, Any]) -> None:
    payload["updatedAt"] = audit.utc_now()
    DECISIONS_PATH.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def apply_decision(entry: dict[str, Any], decision: dict[str, Any]) -> None:
    action = decision.get("action") or "keep_fallback"
    entry["visuallyReviewed"] = bool(decision.get("visuallyReviewed", True))
    entry["visualReviewNotes"] = decision.get("visualReviewNotes") or ""
    entry["objectClass"] = decision.get("objectClass") or entry.get("objectClass") or "unclear"
    entry["reviewedAt"] = audit.utc_now()
    for key in (
        "coverVersion",
        "validFrom",
        "validUntil",
        "currentnessEvidenceUrl",
        "currentnessEvidenceType",
        "currentnessConfidence",
        "commonsFileTitle",
        "commonsPageUrl",
        "originalFileUrl",
        "author",
        "licenseName",
        "licenseUrl",
        "attributionText",
        "passportType",
        "currentOrHistoric",
        "imageDate",
        "resolution",
    ):
        if key in decision and decision[key] is not None:
            entry[key] = decision[key]

    if action == "approve_photo":
        entry["imageLicenseStatus"] = "approved"
        entry["deploymentStatus"] = "emblem_review_required"
        entry["emblemRightsReviewRequired"] = True
        entry["status"] = "needs_manual_review"  # legacy: not public-cleared
        entry["displayDecision"] = "staged_photo"
        entry["rejectionReason"] = None
        # Prefer staging path, never public while gate off / emblem review required.
        iso3 = entry["iso3"].lower()
        staged = STAGED_DIR / f"{iso3}.webp"
        if staged.is_file():
            entry["stagedLocalFile"] = str(staged.relative_to(ROOT)).replace("\\", "/")
        entry["localFile"] = None
    elif action == "reject":
        entry["imageLicenseStatus"] = "rejected"
        entry["deploymentStatus"] = "blocked"
        entry["status"] = "rejected"
        entry["displayDecision"] = "fallback"
        entry["rejectionReason"] = decision.get("reason") or "manual_reject"
    elif action == "mark_historic":
        entry["imageLicenseStatus"] = entry.get("imageLicenseStatus") or "unclear"
        entry["currentOrHistoric"] = "historic"
        entry["deploymentStatus"] = "blocked"
        entry["status"] = "needs_manual_review"
        entry["displayDecision"] = "fallback"
        entry["rejectionReason"] = "historic_cover"
    elif action == "mark_wrong_type":
        entry["passportType"] = decision.get("passportType") or "diplomatic"
        entry["deploymentStatus"] = "blocked"
        entry["status"] = "needs_manual_review"
        entry["displayDecision"] = "fallback"
        entry["rejectionReason"] = "wrong_passport_type"
    elif action == "mark_license_problem":
        entry["imageLicenseStatus"] = "rejected"
        entry["deploymentStatus"] = "blocked"
        entry["status"] = "rejected"
        entry["displayDecision"] = "fallback"
        entry["rejectionReason"] = decision.get("reason") or "license_problem"
    elif action == "request_search":
        entry["imageLicenseStatus"] = "unclear"
        entry["deploymentStatus"] = "editorial_review_required"
        entry["status"] = "needs_manual_review"
        entry["displayDecision"] = "fallback"
        entry["reviewNotes"] = "request_another_targeted_search"
    else:  # keep_fallback
        entry["displayDecision"] = "fallback"
        if entry.get("imageLicenseStatus") == "approved" and not (
            entry.get("visuallyReviewed")
            and entry.get("currentnessConfidence") == "high"
            and entry.get("passportType") == "ordinary"
            and entry.get("currentOrHistoric") != "historic"
        ):
            # Downgrade display; keep license note if already approved earlier.
            entry["deploymentStatus"] = "emblem_review_required"
        elif entry.get("imageLicenseStatus") not in {"approved", "rejected"}:
            entry["imageLicenseStatus"] = "unclear"
            entry["deploymentStatus"] = "editorial_review_required"
        entry["status"] = "needs_manual_review" if entry.get("status") == "approved" else entry.get("status")
        entry["localFile"] = None

    default_dual_fields(entry)


def write_public_gated_outputs(manifest: dict[str, Any]) -> None:
    """While gate is off, public covers.json is empty and attributions explain fallback."""
    entries = manifest.get("entries") or []
    if not cfg.REAL_PASSPORT_COVERS_ENABLED:
        audit.PUBLIC_COVERS_META.parent.mkdir(parents=True, exist_ok=True)
        audit.PUBLIC_COVERS_META.write_text(
            json.dumps(
                {
                    "generatedAt": audit.utc_now(),
                    "source": "Wikimedia Commons (gated)",
                    "realPassportCoversEnabled": False,
                    "count": 0,
                    "covers": {},
                    "note": "Real passport covers are disabled publicly. Mir’ah illustrations are shown.",
                },
                ensure_ascii=False,
                indent=2,
            )
            + "\n",
            encoding="utf-8",
        )
        # Attributions page: review-only note, no public image URLs.
        audit.write_attributions_html([])
        # Ensure no webp remain in public assets.
        if audit.PUBLIC_ASSETS.is_dir():
            for path in audit.PUBLIC_ASSETS.glob("*.webp"):
                dest = STAGED_DIR / path.name
                path.replace(dest)
    else:
        # Only deployment-cleared + visually confirmed would be published — still none auto.
        publishable = [
            e
            for e in entries
            if e.get("deploymentStatus") == "cleared"
            and e.get("imageLicenseStatus") == "approved"
            and e.get("visuallyReviewed")
            and e.get("currentnessConfidence") == "high"
            and e.get("passportType") == "ordinary"
            and e.get("currentOrHistoric") != "historic"
            and e.get("explicitClearance")
        ]
        audit.write_covers_runtime_meta(publishable)
        audit.write_attributions_html(publishable)


def build_review_tool(manifest: dict[str, Any]) -> Path:
    ensure_review_dirs()
    entries = sorted(manifest.get("entries") or [], key=lambda e: e["iso3"])
    cards = []
    for entry in entries:
        cands = entry.get("candidates") or []
        cand_html = []
        for i, c in enumerate(cands[:8]):
            thumb = c.get("localThumb")
            img = (
                f'<img src="../{html.escape(thumb)}" alt="" width="110" height="150" loading="lazy">'
                if thumb
                else "<div class='no-thumb'>no local thumb</div>"
            )
            page = c.get("commonsPageUrl") or "#"
            cand_html.append(
                f"""<article class="cand">
                {img}
                <div class="meta">
                  <a href="{html.escape(page)}" target="_blank" rel="noopener">{html.escape(c.get('commonsFileTitle') or 'file')}</a>
                  <div>author: {html.escape(c.get('author') or '—')}</div>
                  <div>license: {html.escape(c.get('licenseName') or '—')}</div>
                  <div>date: {html.escape(str(c.get('imageDate') or '—'))}</div>
                  <div>size: {html.escape(json.dumps(c.get('resolution') or {}))}</div>
                  <div>class: {html.escape(c.get('objectClass') or 'unclear')}</div>
                  <div>type/era: {html.escape(str(c.get('passportType')))} / {html.escape(str(c.get('currentOrHistoric')))}</div>
                  <div class="desc">{html.escape((c.get('description') or '')[:280])}</div>
                </div>
                </article>"""
            )
        cards.append(
            f"""<section class="card" id="{html.escape(entry['iso3'])}" data-iso3="{html.escape(entry['iso3'])}">
            <header>
              <h2>{html.escape(entry['countryNameEn'])} <small>{html.escape(entry['iso3'])}</small></h2>
              <div class="badges">
                <span>license:{html.escape(entry.get('imageLicenseStatus') or 'unclear')}</span>
                <span>deploy:{html.escape(entry.get('deploymentStatus') or '—')}</span>
                <span>display:{html.escape(entry.get('displayDecision') or 'fallback')}</span>
              </div>
            </header>
            <p class="notes">{html.escape(entry.get('reviewNotes') or '')} | {html.escape(entry.get('visualReviewNotes') or '')}</p>
            <p>Evidence: {html.escape(entry.get('currentnessEvidenceUrl') or '—')} ({html.escape(entry.get('currentnessEvidenceType') or '—')}) confidence={html.escape(entry.get('currentnessConfidence') or 'low')}</p>
            <div class="actions" data-iso3="{html.escape(entry['iso3'])}">
              <button data-action="approve_photo">approve photo</button>
              <button data-action="reject">reject</button>
              <button data-action="mark_historic">mark historic</button>
              <button data-action="mark_wrong_type">wrong type</button>
              <button data-action="mark_license_problem">license problem</button>
              <button data-action="request_search">request search</button>
              <button data-action="keep_fallback">keep fallback</button>
            </div>
            <div class="cands">{''.join(cand_html) or '<p>No candidates</p>'}</div>
            </section>"""
        )

    page = f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8"/>
<title>Mir’ah local passport-cover review (NOT FOR DEPLOY)</title>
<style>
body{{font-family:Segoe UI,system-ui,sans-serif;margin:0;background:#0b1220;color:#e8eef8}}
header.top{{position:sticky;top:0;background:#121c2e;padding:12px 16px;border-bottom:1px solid #243552;z-index:5}}
.wrap{{max-width:1100px;margin:auto;padding:16px}}
.card{{border:1px solid #2a3f5d;border-radius:14px;padding:14px;margin:14px 0;background:#101a2b}}
.card h2{{margin:0 0 8px;font-size:18px}}
.badges span{{display:inline-block;margin:2px 6px 2px 0;padding:3px 8px;border-radius:999px;background:#1a2b44;font-size:11px}}
.cands{{display:grid;grid-template-columns:repeat(auto-fill,minmax(240px,1fr));gap:10px;margin-top:10px}}
.cand{{border:1px solid #243552;border-radius:10px;padding:8px;background:#0c1626}}
.cand img{{width:110px;height:150px;object-fit:contain;background:#000;display:block;margin-bottom:6px}}
.actions button{{margin:4px 4px 0 0;padding:6px 8px;border-radius:8px;border:1px solid #3a5578;background:#182841;color:#fff;cursor:pointer;font-size:12px}}
.actions button:hover{{background:#243b5c}}
.notes,.meta,.desc{{color:#9db0c9;font-size:12px;line-height:1.45}}
.no-thumb{{width:110px;height:150px;display:grid;place-items:center;background:#000;color:#666;font-size:11px}}
.warn{{color:#ffb4b4}}
</style>
</head>
<body>
<header class="top">
  <strong>Local-only passport cover review</strong>
  <span class="warn"> — must never be deployed. REAL_PASSPORT_COVERS_ENABLED={cfg.REAL_PASSPORT_COVERS_ENABLED}</span>
  <div>Entries: {len(entries)}. Decisions save to decisions.local.json in this folder (export manually into decisions.json).</div>
</header>
<div class="wrap">
{''.join(cards)}
</div>
<script>
const store=JSON.parse(localStorage.getItem('miraahCoverDecisions')||'{{}}');
function save(){{localStorage.setItem('miraahCoverDecisions', JSON.stringify(store)); document.getElementById('exportBox').value=JSON.stringify({{decisions:store}},null,2);}}
document.querySelectorAll('.actions button').forEach(btn=>{{
  btn.addEventListener('click',()=>{{
    const iso=btn.parentElement.dataset.iso3;
    store[iso]={{action:btn.dataset.action, visuallyReviewed:true, visualReviewNotes:'local-tool:'+btn.dataset.action, currentnessConfidence:'low'}};
    save();
    btn.parentElement.querySelectorAll('button').forEach(b=>b.style.outline='');
    btn.style.outline='2px solid #38d6b0';
  }});
}});
</script>
<div class="wrap">
<h3>Export decisions JSON</h3>
<textarea id="exportBox" style="width:100%;height:180px;background:#0c1626;color:#fff;border:1px solid #243552"></textarea>
</div>
<script>document.getElementById('exportBox').value=JSON.stringify({{decisions:store}},null,2);</script>
</body></html>
"""
    out = TOOL_DIR / "index.html"
    out.write_text(page, encoding="utf-8")
    (TOOL_DIR / "README.md").write_text(
        "# Local passport-cover review tool\n\n"
        "Serve only from this folder for local review:\n\n"
        "```bash\npython -m http.server 8765 --directory source-data/passport-covers/review\n```\n\n"
        "Then open http://127.0.0.1:8765/tool/\n\n"
        "Do **not** copy this into `public/` or deploy it.\n",
        encoding="utf-8",
    )
    return out


def summarize(entries: list[dict[str, Any]]) -> dict[str, Any]:
    photo_license_approved = sum(1 for e in entries if e.get("imageLicenseStatus") == "approved")
    visually_confirmed = sum(
        1
        for e in entries
        if e.get("visuallyReviewed")
        and e.get("imageLicenseStatus") == "approved"
        and e.get("passportType") == "ordinary"
        and e.get("currentOrHistoric") != "historic"
        and e.get("currentnessConfidence") == "high"
        and not (e.get("objectClass") in {"identity_or_data_page", "unclear_object"})
    )
    current_ordinary = visually_confirmed
    deployment_cleared = sum(1 for e in entries if e.get("deploymentStatus") == "cleared")
    emblem_review = sum(1 for e in entries if e.get("deploymentStatus") == "emblem_review_required")
    fallback = sum(1 for e in entries if e.get("displayDecision", "fallback") == "fallback" or not cfg.REAL_PASSPORT_COVERS_ENABLED)
    # While gate is off, public fallback count is always 199.
    public_fallback = 199 if not cfg.REAL_PASSPORT_COVERS_ENABLED else fallback
    historic_wrong = sum(
        1
        for e in entries
        if e.get("currentOrHistoric") == "historic"
        or e.get("passportType") in {"diplomatic", "service"}
        or e.get("rejectionReason") in {"historic_cover", "wrong_passport_type"}
    )
    unresolved = sum(
        1
        for e in entries
        if e.get("deploymentStatus") in {"editorial_review_required", "emblem_review_required"}
        or (
            e.get("imageLicenseStatus") == "unclear"
            and e.get("displayDecision") == "fallback"
        )
    )
    visually_list = [
        e["iso3"]
        for e in entries
        if e.get("visuallyReviewed")
        and e.get("imageLicenseStatus") == "approved"
        and e.get("currentnessConfidence") == "high"
        and e.get("passportType") == "ordinary"
        and e.get("currentOrHistoric") != "historic"
    ]
    unresolved_list = [e["iso3"] for e in entries if e["iso3"] not in visually_list]
    return {
        "photoLicenseApproved": photo_license_approved,
        "visuallyConfirmed": visually_confirmed,
        "currentOrdinary": current_ordinary,
        "deploymentCleared": deployment_cleared,
        "emblemReviewRequired": emblem_review,
        "fallbackPublic": public_fallback,
        "historicOrWrongType": historic_wrong,
        "unresolved": len(unresolved_list),
        "visuallyConfirmedIso3": visually_list,
        "unresolvedIso3": unresolved_list,
        "realPassportCoversEnabled": cfg.REAL_PASSPORT_COVERS_ENABLED,
    }


def write_final_table(entries: list[dict[str, Any]], summary: dict[str, Any]) -> None:
    lines = [
        "# Passport cover manual-review final table (199)",
        "",
        f"- REAL_PASSPORT_COVERS_ENABLED: `{cfg.REAL_PASSPORT_COVERS_ENABLED}`",
        f"- Photo-license approved: **{summary['photoLicenseApproved']}**",
        f"- Visually confirmed current ordinary: **{summary['visuallyConfirmed']}**",
        f"- Deployment cleared: **{summary['deploymentCleared']}**",
        f"- Emblem review required: **{summary['emblemReviewRequired']}**",
        f"- Public fallback (gate off ⇒ 199): **{summary['fallbackPublic']}**",
        "",
        "| ISO3 | Country | Photo license | Visually current ordinary | Deployment | Display | Reason | Commons | License | Currentness evidence |",
        "| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |",
    ]
    for e in sorted(entries, key=lambda x: x["iso3"]):
        vis = (
            "yes"
            if (
                e.get("visuallyReviewed")
                and e.get("imageLicenseStatus") == "approved"
                and e.get("currentnessConfidence") == "high"
                and e.get("passportType") == "ordinary"
                and e.get("currentOrHistoric") != "historic"
            )
            else "no"
        )
        lines.append(
            "| {iso3} | {country} | {lic} | {vis} | {dep} | {disp} | {reason} | {commons} | {license} | {evid} |".format(
                iso3=e["iso3"],
                country=e.get("countryNameEn") or "",
                lic=e.get("imageLicenseStatus") or "unclear",
                vis=vis,
                dep=e.get("deploymentStatus") or "",
                disp="fallback" if not cfg.REAL_PASSPORT_COVERS_ENABLED else (e.get("displayDecision") or "fallback"),
                reason=html.escape((e.get("visualReviewNotes") or e.get("rejectionReason") or e.get("reviewNotes") or "")[:80]),
                commons=(e.get("commonsFileTitle") or "—").replace("|", "/"),
                license=(e.get("licenseName") or "—").replace("|", "/"),
                evid=(e.get("currentnessEvidenceUrl") or "—").replace("|", "/"),
            )
        )
    FINAL_TABLE_PATH.write_text("\n".join(lines) + "\n", encoding="utf-8")
    REPORT_PATH.write_text(
        "# Manual review pass\n\n"
        + json.dumps(summary, ensure_ascii=False, indent=2)
        + "\n\nSee FINAL_TABLE.md for all 199 rows.\n",
        encoding="utf-8",
    )


def run_targeted(only: str | None, limit: int | None, download_thumbs: bool) -> None:
    manifest = migrate_manifest()
    by_iso = {e["iso3"]: e for e in manifest["entries"]}
    passports = audit.load_passports()
    targets = []
    for p in passports:
        e = by_iso[p["iso3"]]
        if only and p["iso3"] != only.upper():
            continue
        # All without deployment-cleared public photos — i.e. everyone while gate off,
        # but prioritize unresolved / non-visually-confirmed.
        if e.get("visuallyReviewed") and e.get("currentnessConfidence") == "high":
            continue
        targets.append(p)
    if limit:
        targets = targets[:limit]
    total = len(targets)
    for i, p in enumerate(targets, 1):
        print(f"[{i}/{total}] targeted {p['iso3']} {p['nameEn']}", flush=True)
        entry = by_iso[p["iso3"]]
        targeted_research_country(p, entry)
        if download_thumbs:
            for idx, cand in enumerate((entry.get("candidates") or [])[:5]):
                if cand.get("eligible") or cand.get("looksCover") or idx < 2:
                    download_thumb(cand, p["iso3"], idx)
        by_iso[p["iso3"]] = entry
        manifest["entries"] = [by_iso[c["iso3"]] for c in passports]
        if i % 5 == 0:
            audit.save_manifest(manifest)
    audit.save_manifest(manifest)
    write_public_gated_outputs(manifest)
    build_review_tool(manifest)
    summary = summarize(manifest["entries"])
    write_final_table(manifest["entries"], summary)
    print(json.dumps(summary, ensure_ascii=False, indent=2))


def apply_decisions_file() -> None:
    manifest = migrate_manifest()
    decisions = load_decisions().get("decisions") or {}
    by_iso = {e["iso3"]: e for e in manifest["entries"]}
    for iso3, decision in decisions.items():
        if iso3 not in by_iso:
            continue
        apply_decision(by_iso[iso3], decision)
    passports = audit.load_passports()
    manifest["entries"] = [by_iso[p["iso3"]] for p in passports]
    audit.save_manifest(manifest)
    write_public_gated_outputs(manifest)
    build_review_tool(manifest)
    summary = summarize(manifest["entries"])
    write_final_table(manifest["entries"], summary)
    print(json.dumps(summary, ensure_ascii=False, indent=2))


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--migrate", action="store_true", help="Migrate schema + gate public outputs")
    parser.add_argument("--targeted-search", action="store_true", help="Run targeted Commons searches")
    parser.add_argument("--download-thumbs", action="store_true", help="Cache local thumbs for review tool")
    parser.add_argument("--build-tool", action="store_true", help="Rebuild local review HTML")
    parser.add_argument("--apply-decisions", action="store_true", help="Apply review/decisions.json")
    parser.add_argument("--country", help="Limit to one ISO3")
    parser.add_argument("--limit", type=int, help="Limit number of countries for targeted search")
    args = parser.parse_args(argv)

    ensure_review_dirs()
    if args.migrate or not any([args.targeted_search, args.apply_decisions, args.build_tool]):
        manifest = migrate_manifest()
        write_public_gated_outputs(manifest)
        print("migrated", len(manifest["entries"]), "REAL_PASSPORT_COVERS_ENABLED=", cfg.REAL_PASSPORT_COVERS_ENABLED)

    if args.targeted_search:
        run_targeted(args.country, args.limit, args.download_thumbs)
    elif args.apply_decisions:
        apply_decisions_file()
    elif args.build_tool:
        manifest = audit.load_manifest()
        for e in manifest["entries"]:
            enrich_candidates(e)
            default_dual_fields(e)
        build_review_tool(manifest)
        write_final_table(manifest["entries"], summarize(manifest["entries"]))
        print("tool:", TOOL_DIR / "index.html")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
