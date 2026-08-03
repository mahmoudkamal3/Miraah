#!/usr/bin/env python3
"""Fetch/normalize passport data into public/data/passports/ (dry-run by default)."""

from __future__ import annotations

import argparse
import json
import sys
import urllib.error
import urllib.request
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

import passport_core as core  # noqa: E402
import passport_locale as locale  # noqa: E402

SOURCE_REPO = "https://github.com/imorte/passport-index-data"
SOURCE_RAW = (
    "https://raw.githubusercontent.com/imorte/passport-index-data/main/"
    "passport-index-tidy-iso3.csv"
)
LICENSE_RAW = "https://raw.githubusercontent.com/imorte/passport-index-data/main/LICENSE"
README_RAW = "https://raw.githubusercontent.com/imorte/passport-index-data/main/README.md"
USER_AGENT = "MiraahPassportUpdater/1.0 (+https://miraah.mirapp.workers.dev/)"


def download(url: str) -> bytes:
    request = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    try:
        with urllib.request.urlopen(request, timeout=60) as response:
            return response.read()
    except urllib.error.URLError as exc:
        raise core.PassportDataError(f"Failed to download {url}: {exc}") from exc


def write_source_bundle(csv_bytes: bytes, license_bytes: bytes, readme_bytes: bytes) -> None:
    core.SOURCE_DIR.mkdir(parents=True, exist_ok=True)
    (core.SOURCE_DIR / "passport-index-tidy-iso3.csv").write_bytes(csv_bytes)
    (core.SOURCE_DIR / "LICENSE").write_bytes(license_bytes)
    (core.SOURCE_DIR / "README.md").write_bytes(readme_bytes)
    retrieval = core.utc_now_iso()
    update_date = "2026-02-17"
    # Prefer date declared in upstream README when present.
    readme_text = readme_bytes.decode("utf-8", errors="replace")
    for line in readme_text.splitlines():
        if "Last updated" in line and "202" in line:
            # Keep ISO date form used by Mir’ah metadata.
            if "17 February 2026" in line or "2026-02-17" in line:
                update_date = "2026-02-17"
            break
    meta = (
        f"source_repository: {SOURCE_REPO}\n"
        "preferred_file: passport-index-tidy-iso3.csv\n"
        "license: MIT\n"
        f"dataset_update_date: {update_date}\n"
        'dataset_update_note: Declared in upstream README as "Last updated: 17 February 2026"\n'
        f"retrieval_timestamp_utc: {retrieval}\n"
        "retrieved_files:\n"
        "  - passport-index-tidy-iso3.csv\n"
        "  - LICENSE\n"
        "  - README.md\n"
        "provisional: true\n"
        "commercial_note: Upstream dataset is provisional for Mir'ah MVP. "
        "Separate upstream-rights review required before commercial monetization. "
        "Underlying data is scraped from passportindex.org.\n"
    )
    (core.SOURCE_DIR / "SOURCE_META.yml").write_text(meta, encoding="utf-8", newline="\n")


def load_miraah_iso3() -> set[str]:
    html = (ROOT / "public" / "dashboard.html").read_text(encoding="utf-8")
    start = html.index('"countries":{') + len('"countries":')
    end = html.index(',"indicatorMeta":', start)
    countries = json.loads(html[start:end])
    return set(countries.keys())


def mapping_report(passport_codes: set[str], miraah_codes: set[str]) -> dict[str, Any]:
    return {
        "passportNotInMiraah": sorted(passport_codes - miraah_codes),
        "miraahWithoutPassport": sorted(miraah_codes - passport_codes),
        "intersectionCount": len(passport_codes & miraah_codes),
        "passportCount": len(passport_codes),
        "miraahCount": len(miraah_codes),
    }


def build_normalized_payload(
    rows: list[dict[str, str]],
    source_meta: dict[str, str],
    miraah_codes: set[str],
) -> tuple[dict[str, Any], dict[str, Any], dict[str, Any], dict[str, dict[str, Any]]]:
    audit = core.audit_requirement_values(rows)
    if audit["unknownCount"]:
        raise core.PassportDataError(f"Unknown requirement values: {audit['unknown']}")

    by_passport, countries = core.build_matrices(rows)
    locale.validate_locale_coverage(countries)
    mapping = mapping_report(set(by_passport), miraah_codes)

    scores: dict[str, int] = {}
    summaries: dict[str, dict[str, Any]] = {}
    detail_files: dict[str, dict[str, Any]] = {}

    for code, destinations in by_passport.items():
        scored = core.score_passport(destinations)
        scores[code] = scored["mobilityScore"]
        summaries[code] = {
            "iso3": code,
            "iso2": locale.ISO3_TO_ISO2[code],
            "slug": core.slugify(locale.NAME_EN[code], code),
            "nameEn": locale.NAME_EN[code],
            "nameAr": locale.NAME_AR[code],
            "region": _region_for(code, miraah_codes),
            **scored,
        }
        detail_files[code] = {
            "iso3": code,
            "iso2": locale.ISO3_TO_ISO2[code],
            "slug": summaries[code]["slug"],
            "nameEn": locale.NAME_EN[code],
            "nameAr": locale.NAME_AR[code],
            "region": summaries[code]["region"],
            "mobilityScore": scored["mobilityScore"],
            "categoryTotals": scored["categoryTotals"],
            "destinationCount": scored["destinationCount"],
            "destinations": [
                {
                    "iso3": item["destination"],
                    "iso2": locale.ISO3_TO_ISO2[item["destination"]],
                    "nameEn": locale.NAME_EN[item["destination"]],
                    "nameAr": locale.NAME_AR[item["destination"]],
                    "region": _region_for(item["destination"], miraah_codes),
                    "status": item["status"],
                    "days": item["days"],
                }
                for item in destinations
            ],
        }

    ranks = core.dense_rank(scores)
    for code, summary in summaries.items():
        summary["rank"] = ranks[code]
        detail_files[code]["rank"] = ranks[code]

    # Ensure unique slugs.
    slug_owners: dict[str, str] = {}
    for code, summary in sorted(summaries.items()):
        slug = summary["slug"]
        if slug in slug_owners:
            summary["slug"] = f"{slug}-{code.lower()}"
            detail_files[code]["slug"] = summary["slug"]
        slug_owners[summary["slug"]] = code

    index = {
        "generatedAt": core.utc_now_iso(),
        "datasetUpdateDate": source_meta["dataset_update_date"],
        "retrievalTimestampUtc": source_meta["retrieval_timestamp_utc"],
        "sourceRepository": source_meta["source_repository"],
        "license": source_meta["license"],
        "methodology": {
            "mobilityScore": (
                "Sum of destinations with visa_free, visa_on_arrival, or eta access. "
                "evisa, visa_required, and no_admission contribute 0. Own country (home) is excluded."
            ),
            "ranking": "Dense ranking by mobilityScore descending; ties share a rank.",
        },
        "passports": sorted(
            summaries.values(),
            key=lambda item: (item["rank"], -item["mobilityScore"], item["nameEn"]),
        ),
    }

    names = {
        code: {
            "nameEn": locale.NAME_EN[code],
            "nameAr": locale.NAME_AR[code],
            "iso2": locale.ISO3_TO_ISO2[code],
            "region": summaries[code]["region"] if code in summaries else _region_for(code, miraah_codes),
            "slug": summaries[code]["slug"] if code in summaries else core.slugify(locale.NAME_EN[code], code),
        }
        for code in sorted(countries)
    }

    meta = {
        "generatedAt": index["generatedAt"],
        "datasetUpdateDate": source_meta["dataset_update_date"],
        "retrievalTimestampUtc": source_meta["retrieval_timestamp_utc"],
        "sourceRepository": SOURCE_REPO,
        "license": "MIT",
        "provisional": True,
        "passportCount": len(summaries),
        "destinationUniverse": len(countries),
        "requirementAudit": audit,
        "mapping": mapping,
        "attribution": (
            "Passport requirement data from imorte/passport-index-data (MIT License). "
            "Original upstream information is associated with passportindex.org."
        ),
        "disclaimer": (
            "Visa rules change. Mir’ah Passport Power is informational only and is not legal "
            "travel advice. Verify requirements with an embassy, airline, or official authority."
        ),
        "commercialRisk": (
            "This source dataset is provisional. Complete a separate upstream-rights review "
            "before commercial monetization."
        ),
    }
    return meta, index, names, detail_files


_REGION_CACHE: dict[str, str] | None = None


def _load_miraah_regions() -> dict[str, str]:
    global _REGION_CACHE
    if _REGION_CACHE is not None:
        return _REGION_CACHE
    html = (ROOT / "public" / "dashboard.html").read_text(encoding="utf-8")
    start = html.index('"countries":{') + len('"countries":')
    end = html.index(',"indicatorMeta":', start)
    countries = json.loads(html[start:end])
    _REGION_CACHE = {code: data.get("region") or "Other" for code, data in countries.items()}
    return _REGION_CACHE


def _region_for(code: str, miraah_codes: set[str]) -> str:
    regions = _load_miraah_regions()
    if code in regions:
        return regions[code]
    # Explicit regions for passport countries outside the Mir’ah World Bank set.
    extras = {"TWN": "East Asia & Pacific", "VAT": "Europe & Central Asia"}
    if code in extras:
        return extras[code]
    raise core.PassportDataError(f"No region mapping for {code}")


def serialize_outputs(
    meta: dict[str, Any],
    index: dict[str, Any],
    names: dict[str, Any],
    details: dict[str, dict[str, Any]],
) -> dict[Path, str]:
    files: dict[Path, str] = {
        core.PUBLIC_DATA / "meta.json": json.dumps(meta, ensure_ascii=False, separators=(",", ":"))
        + "\n",
        core.PUBLIC_DATA / "index.json": json.dumps(index, ensure_ascii=False, separators=(",", ":"))
        + "\n",
        core.PUBLIC_DATA / "names.json": json.dumps(names, ensure_ascii=False, separators=(",", ":"))
        + "\n",
    }
    for code, payload in details.items():
        path = core.PUBLIC_DATA / "by-code" / f"{code}.json"
        files[path] = json.dumps(payload, ensure_ascii=False, separators=(",", ":")) + "\n"
    return files


def write_outputs(files: dict[Path, str]) -> None:
    # Remove stale by-code files when codes disappear.
    by_code = core.PUBLIC_DATA / "by-code"
    if by_code.is_dir():
        keep = {path for path in files if path.parent == by_code}
        for existing in by_code.glob("*.json"):
            if existing not in keep:
                existing.unlink()
    for path, text in files.items():
        core.atomic_write_text(path, text)


def run(*, write: bool, refresh_source: bool) -> dict[str, Any]:
    import tempfile

    csv_path = core.SOURCE_CSV
    temp_dir: tempfile.TemporaryDirectory[str] | None = None
    try:
        if refresh_source:
            csv_bytes = download(SOURCE_RAW)
            license_bytes = download(LICENSE_RAW)
            readme_bytes = download(README_RAW)
            if write:
                write_source_bundle(csv_bytes, license_bytes, readme_bytes)
            else:
                temp_dir = tempfile.TemporaryDirectory()
                tmp = Path(temp_dir.name)
                csv_path = tmp / "passport-index-tidy-iso3.csv"
                csv_path.write_bytes(csv_bytes)
                # Keep using on-disk SOURCE_META for metadata fields during dry-run
                # unless missing; then synthesize from download.
                if not core.SOURCE_META.is_file():
                    write_source_bundle(csv_bytes, license_bytes, readme_bytes)

        rows = core.parse_tidy_csv(csv_path)
        source_meta = core.load_source_meta()
        miraah_codes = load_miraah_iso3()
        meta, index, names, details = build_normalized_payload(rows, source_meta, miraah_codes)
        files = serialize_outputs(meta, index, names, details)
        changed = core.compare_payload_trees(core.PUBLIC_DATA, files)

        result = {
            "wouldWrite": changed,
            "passportCount": meta["passportCount"],
            "unknownRequirements": meta["requirementAudit"]["unknown"],
            "mapping": meta["mapping"],
            "datasetUpdateDate": meta["datasetUpdateDate"],
            "wrote": False,
        }
        if write:
            if changed:
                write_outputs(files)
                result["wrote"] = True
            else:
                result["wrote"] = False
        return result
    finally:
        if temp_dir is not None:
            temp_dir.cleanup()


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--write",
        action="store_true",
        help="Persist normalized JSON under public/data/passports/",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Validate and report without writing (default).",
    )
    parser.add_argument(
        "--refresh-source",
        action="store_true",
        help="Download the upstream CSV/LICENSE/README into source-data/ before normalizing.",
    )
    args = parser.parse_args(argv)
    write = bool(args.write)
    if args.dry_run and args.write:
        raise SystemExit("Use either --dry-run or --write, not both")
    try:
        result = run(write=write, refresh_source=args.refresh_source)
    except core.PassportDataError as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1
    mode = "write" if write else "dry-run"
    print(f"mode={mode}")
    print(f"passports={result['passportCount']}")
    print(f"datasetUpdateDate={result['datasetUpdateDate']}")
    print(f"wouldWrite={result['wouldWrite']}")
    print(f"wrote={result['wrote']}")
    print(
        "mapping gaps: "
        f"passportNotInMiraah={result['mapping']['passportNotInMiraah']} "
        f"miraahWithoutPassport={len(result['mapping']['miraahWithoutPassport'])}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
