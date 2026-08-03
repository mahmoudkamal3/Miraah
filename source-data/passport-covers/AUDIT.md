# Passport cover acquisition — concise audit summary

**Public status:** real passport-cover photographs remain **disabled**.

- `REAL_PASSPORT_COVERS_ENABLED = false` (`scripts/passport_cover_config.py`)
- `public/data/passports/covers.json` exposes `count: 0`
- `public/assets/passports/` must contain no uncleared cover images
- UI uses the Mir’ah illustration for all 199 passports

## Why covers stay disabled

1. **Photo license ≠ deployment clearance.** A Commons-compatible license does not clear state-emblem / passport-reproduction restrictions.
2. **Currentness is hard to prove** from Commons metadata alone for most of the 199 passports.
3. **False positives** appeared during automated discovery (historic covers, official/service types, composites, non-passport documents).
4. Until an explicit human decision sets `deploymentStatus: cleared` **and** flips the gate, public pages must not reference real covers.

## What remains in-repo

- Gate + dual-status helpers in `scripts/passport_cover_config.py` / review scripts
- Slim `manifest.json` (no bulky candidate payloads)
- This summary and `README.md`
- Tests that keep uncleared images out of public output

## What is gitignored / not deployable

Archived originals, staged WebPs, API caches, review thumbs/tool HTML, and build logs under `source-data/passport-covers/`.
