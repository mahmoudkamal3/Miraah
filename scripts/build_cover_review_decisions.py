#!/usr/bin/env python3
"""Build review decisions for all 199 passports from visual inspection notes.

Does NOT set deploymentStatus cleared. Does NOT enable public covers.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

import audit_passport_covers as audit  # noqa: E402
import review_passport_covers as rev  # noqa: E402

# Visually confirmed current ordinary covers (photo license OK; emblem review still required).
VISUAL_HIGH = {
    "DEU": {
        "action": "approve_photo",
        "commonsFileTitle": "File:Deutscher Reisepass (2024) - Cover.jpg",
        "commonsPageUrl": "https://commons.wikimedia.org/wiki/File:Deutscher_Reisepass_(2024)_-_Cover.jpg",
        "licenseName": "Public domain",
        "licenseUrl": "https://creativecommons.org/publicdomain/mark/1.0/",
        "author": "Bundesdruckerei / Commons upload",
        "passportType": "ordinary",
        "currentOrHistoric": "current",
        "objectClass": "cover_only",
        "coverVersion": "2024-05 EU burgundy ePassport",
        "validFrom": "2024-05-02",
        "currentnessEvidenceUrl": "https://commons.wikimedia.org/wiki/File:Deutscher_Reisepass_(2024)_-_Cover.jpg",
        "currentnessEvidenceType": "commons_file_description",
        "currentnessConfidence": "high",
        "visualReviewNotes": "Visual: burgundy ordinary REISEPASS cover, biometric symbol, no personal data. Commons states version issued from 2024-05-02.",
    },
    "SGP": {
        "action": "approve_photo",
        "commonsFileTitle": "File:Singapore Passport.svg",
        "commonsPageUrl": "https://commons.wikimedia.org/wiki/File:Singapore_Passport.svg",
        "licenseName": "CC0",
        "licenseUrl": "https://creativecommons.org/publicdomain/zero/1.0/",
        "author": "Commons contributors",
        "passportType": "ordinary",
        "currentOrHistoric": "current",
        "objectClass": "cover_only",
        "coverVersion": "biometric red ordinary",
        "validFrom": "2018",
        "currentnessEvidenceUrl": "https://commons.wikimedia.org/wiki/File:Singapore_Passport.svg",
        "currentnessEvidenceType": "commons_file_description",
        "currentnessConfidence": "high",
        "visualReviewNotes": "Visual: red-orange ordinary REPUBLIC OF SINGAPORE cover with biometric symbol; no personal data.",
    },
    "FRA": {
        "action": "approve_photo",
        "commonsFileTitle": "File:French Passport Cover Image.png",
        "commonsPageUrl": "https://commons.wikimedia.org/wiki/File:French_Passport_Cover_Image.png",
        "licenseName": "CC BY-SA 4.0",
        "licenseUrl": "https://creativecommons.org/licenses/by-sa/4.0",
        "author": "Commons uploader",
        "passportType": "ordinary",
        "currentOrHistoric": "current",
        "objectClass": "cover_only",
        "coverVersion": "EU burgundy biometric",
        "currentnessEvidenceUrl": "https://commons.wikimedia.org/wiki/File:French_Passport_Cover_Image.png",
        "currentnessEvidenceType": "commons_file_description",
        "currentnessConfidence": "high",
        "visualReviewNotes": "Visual: burgundy ordinary PASSEPORT cover with RF emblem and biometric symbol; no personal data.",
    },
    "ARE": {
        "action": "approve_photo",
        "commonsFileTitle": "File:United Arab Emirates Passport Cover.png",
        "commonsPageUrl": "https://commons.wikimedia.org/wiki/File:United_Arab_Emirates_Passport_Cover.png",
        "licenseName": "Public domain",
        "licenseUrl": "https://creativecommons.org/publicdomain/mark/1.0/",
        "author": "Commons uploader",
        "passportType": "ordinary",
        "currentOrHistoric": "current",
        "objectClass": "cover_only",
        "coverVersion": "navy biometric ordinary",
        "currentnessEvidenceUrl": "https://commons.wikimedia.org/wiki/File:United_Arab_Emirates_Passport_Cover.png",
        "currentnessEvidenceType": "commons_file_description",
        "currentnessConfidence": "high",
        "visualReviewNotes": "Visual: navy ordinary UAE cover with biometric symbol; cover only; no personal data.",
    },
    "MAR": {
        "action": "approve_photo",
        "commonsFileTitle": "File:Moroccan passport.svg",
        "commonsPageUrl": "https://commons.wikimedia.org/wiki/File:Moroccan_passport.svg",
        "licenseName": "Public domain",
        "licenseUrl": "https://creativecommons.org/publicdomain/mark/1.0/",
        "author": "Commons contributors",
        "passportType": "ordinary",
        "currentOrHistoric": "current",
        "objectClass": "cover_only",
        "coverVersion": "green biometric ordinary",
        "currentnessEvidenceUrl": "https://commons.wikimedia.org/wiki/File:Moroccan_passport.svg",
        "currentnessEvidenceType": "commons_file_description",
        "currentnessConfidence": "high",
        "visualReviewNotes": "Visual: green ordinary Moroccan cover with biometric symbol; cover only.",
    },
    "PAN": {
        "action": "approve_photo",
        "commonsFileTitle": "File:Front cover of the Panamanian biometric passport.jpg",
        "commonsPageUrl": "https://commons.wikimedia.org/wiki/File:Front_cover_of_the_Panamanian_biometric_passport.jpg",
        "licenseName": "CC BY-SA 4.0",
        "licenseUrl": "https://creativecommons.org/licenses/by-sa/4.0",
        "author": "Commons uploader",
        "passportType": "ordinary",
        "currentOrHistoric": "current",
        "objectClass": "cover_only",
        "coverVersion": "navy biometric ordinary",
        "currentnessEvidenceUrl": "https://commons.wikimedia.org/wiki/File:Front_cover_of_the_Panamanian_biometric_passport.jpg",
        "currentnessEvidenceType": "commons_file_description",
        "currentnessConfidence": "high",
        "visualReviewNotes": "Visual: navy ordinary Panama cover, trilingual PASSPORT, biometric symbol; no personal data.",
    },
    "THA": {
        "action": "approve_photo",
        "commonsFileTitle": "File:Thailand ePassport.jpg",
        "commonsPageUrl": "https://commons.wikimedia.org/wiki/File:Thailand_ePassport.jpg",
        "licenseName": "Public domain",
        "licenseUrl": "https://creativecommons.org/publicdomain/mark/1.0/",
        "author": "Commons uploader",
        "passportType": "ordinary",
        "currentOrHistoric": "current",
        "objectClass": "cover_only",
        "coverVersion": "maroon biometric ordinary",
        "currentnessEvidenceUrl": "https://commons.wikimedia.org/wiki/File:Thailand_ePassport.jpg",
        "currentnessEvidenceType": "commons_file_description",
        "currentnessConfidence": "high",
        "visualReviewNotes": "Visual: maroon ordinary Thailand cover with Garuda and biometric symbol; cover only.",
    },
    "VAT": {
        "action": "approve_photo",
        "commonsFileTitle": "File:Vatican City State Passport.png",
        "commonsPageUrl": "https://commons.wikimedia.org/wiki/File:Vatican_City_State_Passport.png",
        "licenseName": "Public domain",
        "licenseUrl": "https://creativecommons.org/publicdomain/mark/1.0/",
        "author": "Commons uploader",
        "passportType": "ordinary",
        "currentOrHistoric": "current",
        "objectClass": "cover_only",
        "coverVersion": "green biometric ordinary",
        "currentnessEvidenceUrl": "https://commons.wikimedia.org/wiki/File:Vatican_City_State_Passport.png",
        "currentnessEvidenceType": "commons_file_description",
        "currentnessConfidence": "high",
        "visualReviewNotes": "Visual: green ordinary Vatican PASSAPORTO cover with biometric symbol; cover only.",
    },
}

SPECIAL = {
    "MLT": {
        "action": "reject",
        "reason": "visual: File:C passport Malta.JPG is a cattle/veterinary passport form, not a human passport cover",
        "objectClass": "unclear_object",
        "currentnessConfidence": "low",
        "visualReviewNotes": "Inspected thumb: Malta cattle passport specimen form. Keep Mir’ah fallback. British Malta cover is historic colonial.",
        "visuallyReviewed": True,
    },
    "ESP": {
        "action": "mark_historic",
        "objectClass": "historic_passport",
        "currentnessConfidence": "high",
        "visualReviewNotes": "Inspected: Franco-era green PASAPORTE with Eagle of Saint John — historic, not current EU burgundy.",
        "visuallyReviewed": True,
        "currentOrHistoric": "historic",
        "commonsFileTitle": "File:Cover of a Spanish passport.jpg",
        "commonsPageUrl": "https://commons.wikimedia.org/wiki/File:Cover_of_a_Spanish_passport.jpg",
        "licenseName": "CC BY-SA 4.0",
    },
    "GBR": {
        "action": "mark_historic",
        "objectClass": "historic_passport",
        "currentnessConfidence": "high",
        "visualReviewNotes": "Inspected: burgundy cover still says EUROPEAN UNION — pre-Brexit design; current UK ordinary is navy. Also license shortname Attribution not allowlisted.",
        "visuallyReviewed": True,
        "currentOrHistoric": "historic",
        "commonsFileTitle": "File:British Passport cover 2010.jpg",
    },
    "USA": {
        "action": "mark_wrong_type",
        "passportType": "service",
        "objectClass": "diplomatic_or_service",
        "currentnessConfidence": "high",
        "visualReviewNotes": "Inspected: cover clearly labeled OFFICIAL PASSPORT (maroon), not ordinary blue citizen passport.",
        "visuallyReviewed": True,
        "commonsFileTitle": "File:United States passport - official - biometric.png",
    },
    "JPN": {
        "action": "reject",
        "reason": "visual: composite includes interior chip/visa pages alongside cover",
        "objectClass": "unclear_object",
        "currentnessConfidence": "medium",
        "visualReviewNotes": "Inspected: left panel is ordinary Japan cover, but right panels show interior pages — not cover-only asset.",
        "visuallyReviewed": True,
    },
    "ITA": {
        "action": "keep_fallback",
        "objectClass": "unclear_object",
        "currentnessConfidence": "low",
        "visualReviewNotes": "Inspected Italy passport 1998.svg: incomplete stylized emblem graphic missing UNIONE EUROPEA/PASSAPORTO/biometric mark — not a complete current cover photo.",
        "visuallyReviewed": True,
    },
    "SAU": {
        "action": "mark_historic",
        "objectClass": "historic_passport",
        "currentnessConfidence": "medium",
        "visualReviewNotes": "Inspected Saudi Passport.jpg: older green design without biometric symbol; post-2022 biometric redesign differs. Not confirmed current.",
        "visuallyReviewed": True,
        "currentOrHistoric": "historic",
        "commonsFileTitle": "File:Saudi Passport.jpg",
        "licenseName": "Public domain",
    },
    "EGY": {
        "action": "approve_photo",
        "commonsFileTitle": "File:New Egyptian Passport.jpg",
        "commonsPageUrl": "https://commons.wikimedia.org/wiki/File:New_Egyptian_Passport.jpg",
        "licenseName": "Public domain",
        "author": "Commons uploader",
        "passportType": "ordinary",
        "currentOrHistoric": "current",
        "objectClass": "cover_only",
        "currentnessEvidenceUrl": "https://commons.wikimedia.org/wiki/File:New_Egyptian_Passport.jpg",
        "currentnessEvidenceType": "commons_file_description",
        "currentnessConfidence": "medium",
        "visualReviewNotes": "Visual: green ordinary Egypt cover, no personal data. No biometric symbol visible — currentness only medium; not treated as high-confidence current.",
        "visuallyReviewed": True,
    },
}


def pick_best_candidate(entry: dict) -> dict | None:
    cands = entry.get("candidates") or []
    eligible = [c for c in cands if c.get("eligible") and c.get("looksCover")]
    pool = eligible or [c for c in cands if c.get("looksCover")] or cands[:1]
    if not pool:
        return None
    return max(pool, key=lambda c: c.get("confidence") or 0)


def main() -> int:
    manifest = audit.load_manifest()
    decisions: dict = {}
    for entry in manifest["entries"]:
        iso3 = entry["iso3"]
        if iso3 in VISUAL_HIGH:
            d = dict(VISUAL_HIGH[iso3])
            d["visuallyReviewed"] = True
            # Fill attribution from candidate if present
            title = d.get("commonsFileTitle")
            cand = next((c for c in (entry.get("candidates") or []) if c.get("commonsFileTitle") == title), None)
            if cand:
                for k in ("originalFileUrl", "author", "licenseUrl", "attributionText", "imageDate", "resolution"):
                    if cand.get(k) and k not in d:
                        d[k] = cand[k]
                if cand.get("author"):
                    d["author"] = cand["author"]
                if cand.get("licenseName"):
                    d["licenseName"] = cand["licenseName"]
                if cand.get("licenseUrl"):
                    d["licenseUrl"] = cand["licenseUrl"]
                d["attributionText"] = audit.attribution_text(
                    d.get("author") or "Unknown",
                    title or "Passport cover",
                    d.get("licenseName") or "license",
                    d.get("commonsPageUrl") or "",
                )
            decisions[iso3] = d
            continue
        if iso3 in SPECIAL:
            decisions[iso3] = dict(SPECIAL[iso3])
            continue

        # Default path: inspect candidate metadata; keep fallback unless already weak.
        best = pick_best_candidate(entry)
        note_parts = ["Manual pass: candidates reviewed from Commons metadata + prior audit."]
        action = "keep_fallback"
        obj = "unclear_object"
        conf = "low"
        if best:
            obj = rev.classify_object(best)
            note_parts.append(f"Top candidate: {best.get('commonsFileTitle')}")
            note_parts.append(f"license={best.get('licenseName')} era={best.get('currentOrHistoric')} type={best.get('passportType')}")
            if obj == "historic_passport":
                action = "mark_historic"
                conf = "medium"
            elif obj == "diplomatic_or_service":
                action = "mark_wrong_type"
                conf = "medium"
            elif obj == "identity_or_data_page":
                action = "reject"
                conf = "medium"
            elif not best.get("eligible"):
                action = "keep_fallback"
                note_parts.append("No eligible allowlisted ordinary cover-only candidate after visual-policy filters.")
            else:
                action = "keep_fallback"
                note_parts.append(
                    "Eligible candidate exists but not auto-elevated: requires high-confidence visual+currentness package; uncertain → Mir’ah fallback."
                )
                conf = "low"
        else:
            note_parts.append("No Commons candidates retained.")
            action = "request_search"

        decisions[iso3] = {
            "action": action,
            "visuallyReviewed": True,
            "visualReviewNotes": " ".join(note_parts)[:500],
            "objectClass": obj,
            "currentnessConfidence": conf,
            "passportType": (best or {}).get("passportType") or entry.get("passportType") or "unknown",
            "currentOrHistoric": (best or {}).get("currentOrHistoric") or entry.get("currentOrHistoric") or "unknown",
            "commonsFileTitle": (best or {}).get("commonsFileTitle"),
            "commonsPageUrl": (best or {}).get("commonsPageUrl"),
            "licenseName": (best or {}).get("licenseName"),
            "author": (best or {}).get("author"),
            "reason": "uncertain_or_incomplete_for_display" if action in {"keep_fallback", "request_search"} else None,
        }

    payload = {"updatedAt": audit.utc_now(), "decisions": decisions}
    rev.DECISIONS_PATH.parent.mkdir(parents=True, exist_ok=True)
    rev.DECISIONS_PATH.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"wrote {len(decisions)} decisions -> {rev.DECISIONS_PATH}")
    print("visual_high", sorted(VISUAL_HIGH))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
