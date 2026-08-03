# Passport cover acquisition

Mir’ah discovers passport-cover candidates **only** through the [Wikimedia Commons API](https://commons.wikimedia.org/w/api.php).

## Do not use

Automated discovery must not download, scrape, hotlink, or copy images from Passport Index, VisaIndex, Henley, Google Images, Pinterest, travel blogs, commercial competitors, or unknown websites.

## Commands

```bash
# Default: audit only (no production overwrites)
python scripts/audit_passport_covers.py

python scripts/audit_passport_covers.py --country MLT
python scripts/audit_passport_covers.py --resume
python scripts/audit_passport_covers.py --download-approved
python scripts/audit_passport_covers.py --download-approved --overwrite
python scripts/audit_passport_covers.py --report
python scripts/audit_passport_covers.py --refresh-reports
```

## Outputs

| Path | Purpose |
| --- | --- |
| `manifest.json` | Full per-ISO3 audit record (199 entries) |
| `AUDIT.md` | Count summary and missing approved list |
| `manual-review/REPORT.md` | Human review queue |
| `originals/` | Archived Commons originals (not served) |
| `public/assets/passports/{iso3}.webp` | Production derivatives (download mode only) |
| `public/data/passports/covers.json` | Runtime metadata for approved covers |
| `public/passport/image-attributions.html` | Visible bilingual attributions |

## License allowlist

Auto-approve only machine-readable commercial-use-compatible licenses:

- Public Domain / PD
- CC0
- CC BY
- CC BY-SA

Reject NC, ND (when processing would violate), All Rights Reserved, fair use, editorial-only, missing/ambiguous licenses.

## Emblem / official insignia

A free photograph license does **not** clear separate restrictions on state emblems, official insignia, or passport reproduction. Every approved entry sets `emblemRightsReviewRequired: true`.

## Attribution obligations

- Keep author, title, Commons page, and license link visible for CC BY / CC BY-SA.
- CC BY-SA share-alike applies to adaptations of those images.
- Fallback art is attributed as **Mir’ah illustration** and is not an official reproduction.
