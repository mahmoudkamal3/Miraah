# Passport Power data

Mir’ah / مرآة Passport Power is a static bilingual product area. It does **not** embed the passport matrix inside the country comparison dashboard.

## Provisional source

- Repository: https://github.com/imorte/passport-index-data
- Preferred file: `passport-index-tidy-iso3.csv`
- License on the GitHub repository: **MIT** (see `source-data/passport-index-data/LICENSE`)
- Upstream dataset update date: **2026-02-17** (README: “Last updated: 17 February 2026”)
- Local mirror + metadata: `source-data/passport-index-data/`
- Retrieval timestamp: recorded in `SOURCE_META.yml` at fetch time

### MIT attribution

This product includes data from [imorte/passport-index-data](https://github.com/imorte/passport-index-data). The repository is MIT-licensed, and the MIT copyright notice and permission notice are preserved under `source-data/passport-index-data/LICENSE`.

### Commercial / rights warning (blocking)

- The GitHub repository dataset carries an MIT license.
- The data was collected from an upstream third-party source (the upstream README associates it with passportindex.org information).
- Upstream database/content rights require a **separate review**.
- An MIT license on the GitHub packaging must **not** be treated as commercially cleared rights to the underlying visa database/content.
- Public monetization and authoritative travel claims are **blocked** until that upstream-rights review is complete.
- Do not present Mir’ah ranks as official, authoritative, IATA, Henley, or any other vendor’s global official rank.

## Current coverage labels

- 199 passports ranked
- 199 matrix destinations including home
- 198 comparable travel destinations after excluding home
- UI coverage copy:
  - EN: “Calculated across 199 passports and 198 travel destinations”
  - AR: “محسوب بين 199 جواز سفر وعبر 198 وجهة سفر”

## Visitor-browser rule

Normalized JSON under `public/data/passports/` is generated offline. The visitor browser never fetches the third-party GitHub CSV.

## Normalization rules

| Source `Requirement` | Mir’ah status | Mobility points |
|---|---|---|
| `7`–`360` (numeric days) | `visa_free` (+ `days`) | 1 |
| `visa free` | `visa_free` | 1 |
| `visa on arrival` | `visa_on_arrival` | 1 |
| `eta` | `eta` | 1 |
| `e-visa` | `evisa` | 0 |
| `visa required` | `visa_required` | 0 |
| `no admission` | `no_admission` | 0 |
| `-1` | `home` (excluded) | 0 |

Unknown values fail closed (updater aborts; no production writes).

## Mir’ah Mobility Score & experimental rank

- **Mir’ah Mobility Score** = count of destinations with `visa_free`, `visa_on_arrival`, or `eta`
- **Experimental Mir’ah rank / ترتيب مرآة التجريبي** = dense ranking by Mobility Score descending
- Equal scores share a rank; the next distinct score receives the next integer rank
- Category totals remain separate from the ranking score
- Invariants:
  - `visa_free + visa_on_arrival + eta + evisa + visa_required + no_admission + home = 199`
  - `visa_free + visa_on_arrival + eta = mobility_score`
- Do not call this a VisaIndex, Henley, or IATA score/rank

## SEO safety (temporary)

Until a commercially reviewed and sufficiently complete data source is installed:

- Passport Power HTML pages use `noindex, follow`
- `/passport/` URLs are excluded from `sitemap.xml`
- Country comparison homepage remains `index, follow`
- `robots.txt` continues to `Allow: /` (do not block passport assets)

### How to reverse later

1. Complete upstream-rights review and replace/upgrade the dataset if needed.
2. Set `PASSPORT_INDEXING_ENABLED = True` in `scripts/render_passport_pages.py`.
3. Re-run `python scripts/render_passport_pages.py` (and optionally `python scripts/render_dashboard.py` so SEO helpers stay aligned).
4. Confirm passport pages emit `index, follow` and sitemap includes `/passport/` plus slug pages.
5. Submit the updated sitemap in Search Console only after the content is ready to be indexed.

## ISO3 mapping gaps (MVP audit)

- Passport countries not in Mir’ah World Bank set: `TWN`, `VAT`
- Mir’ah territories without a passport row (20): mostly non-passport territories such as `ABW`, `ASM`, `BMU`, `CHI`, `CUW`, `CYM`, `FRO`, `GIB`, `GRL`, `GUM`, `IMN`, `MAF`, `MNP`, `NCL`, `PRI`, `PYF`, `SXM`, `TCA`, `VGB`, `VIR`
- Intersection: 197 ISO3 codes

No silent ISO guessing is performed.

## Generated assets

- `public/data/passports/meta.json`
- `public/data/passports/index.json`
- `public/data/passports/names.json`
- `public/data/passports/by-code/{ISO3}.json`
- `public/passport/index.html`
- `public/passport/{slug}/index.html`
- Homepage-only sitemap while `PASSPORT_INDEXING_ENABLED` is false

## Commands

```bash
python -m unittest tests.test_passport_data tests.test_passport_pages tests.test_update_world_bank -v
python scripts/update_passport_data.py --dry-run
python scripts/update_passport_data.py --refresh-source --write
python scripts/render_passport_pages.py
python scripts/render_dashboard.py
```

## Visualization note

Passport Power includes:

1. An accessible SVG **regional distribution chart** (destination counts by region).
2. An interactive **worldwide access map** built from Natural Earth (public domain), documented in `PASSPORT_MAP.md`. Geometry is prebuilt into `public/passport/assets/world-map.json` and loaded only after a passport is selected (no runtime CDN).

### Future: historical mobility line chart (not implemented)

The reference-style historical mobility-score line chart is **deferred**. The current Passport Index Data mirror is a snapshot, not a trustworthy licensed time series. Do **not** invent, interpolate, or scrape historical scores. Revisit only after a properly licensed historical dataset is available.

## Disclaimer

Visa rules change. Mir’ah Passport Power is informational only and is not legal travel advice. Travelers must verify requirements with an embassy, airline, or official authority.
