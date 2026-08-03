#!/usr/bin/env python3
"""Passport Index parsing, normalization, scoring, and ranking for Mir’ah."""

from __future__ import annotations

import csv
import json
import re
from collections import Counter, defaultdict
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
SOURCE_DIR = ROOT / "source-data" / "passport-index-data"
SOURCE_CSV = SOURCE_DIR / "passport-index-tidy-iso3.csv"
SOURCE_META = SOURCE_DIR / "SOURCE_META.yml"
PUBLIC_DATA = ROOT / "public" / "data" / "passports"

# Normalized access statuses used across Mir’ah Passport Power.
STATUS_HOME = "home"
STATUS_VISA_FREE = "visa_free"
STATUS_VOA = "visa_on_arrival"
STATUS_ETA = "eta"
STATUS_EVISA = "evisa"
STATUS_REQUIRED = "visa_required"
STATUS_NO_ADMISSION = "no_admission"

MOBILITY_STATUSES = frozenset({STATUS_VISA_FREE, STATUS_VOA, STATUS_ETA})

CATEGORY_ORDER = (
    STATUS_VISA_FREE,
    STATUS_VOA,
    STATUS_ETA,
    STATUS_EVISA,
    STATUS_REQUIRED,
    STATUS_NO_ADMISSION,
    STATUS_HOME,
)

NUMERIC_DAYS_RE = re.compile(r"^\d+$")


class PassportDataError(ValueError):
    """Raised when source data fails schema or value validation."""


@dataclass(frozen=True)
class Requirement:
    status: str
    days: int | None
    raw: str


def utc_now_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def normalize_requirement(raw: str) -> Requirement:
    """Map a source Requirement cell to a Mir’ah status.

    Raises PassportDataError for unknown values (fail closed).
    """
    value = (raw or "").strip()
    if not value:
        raise PassportDataError("Empty requirement value")
    if value == "-1":
        return Requirement(STATUS_HOME, None, value)
    if value == "visa free":
        return Requirement(STATUS_VISA_FREE, None, value)
    if value == "visa on arrival":
        return Requirement(STATUS_VOA, None, value)
    if value == "eta":
        return Requirement(STATUS_ETA, None, value)
    if value == "e-visa":
        return Requirement(STATUS_EVISA, None, value)
    if value == "visa required":
        return Requirement(STATUS_REQUIRED, None, value)
    if value == "no admission":
        return Requirement(STATUS_NO_ADMISSION, None, value)
    if NUMERIC_DAYS_RE.fullmatch(value):
        days = int(value)
        if days < 1 or days > 366:
            raise PassportDataError(f"Out-of-range visa-free days: {value!r}")
        return Requirement(STATUS_VISA_FREE, days, value)
    raise PassportDataError(f"Unknown requirement value: {value!r}")


def mobility_point(status: str) -> int:
    return 1 if status in MOBILITY_STATUSES else 0


def empty_category_totals() -> dict[str, int]:
    return {key: 0 for key in CATEGORY_ORDER}


def score_passport(destinations: list[dict[str, Any]]) -> dict[str, Any]:
    """Compute category totals and Mir’ah Mobility Score for one passport."""
    totals = empty_category_totals()
    mobility = 0
    for row in destinations:
        status = row["status"]
        if status not in totals:
            raise PassportDataError(f"Unexpected status in destinations: {status!r}")
        totals[status] += 1
        mobility += mobility_point(status)
    scored_destinations = sum(totals[s] for s in CATEGORY_ORDER if s != STATUS_HOME)
    return {
        "mobilityScore": mobility,
        "categoryTotals": totals,
        "destinationCount": scored_destinations,
        "homeExcluded": totals[STATUS_HOME],
    }


def dense_rank(scores: dict[str, int]) -> dict[str, int]:
    """Dense ranking: equal scores share a rank; next distinct score is rank+1."""
    if not scores:
        return {}
    ordered = sorted(scores.items(), key=lambda item: (-item[1], item[0]))
    ranks: dict[str, int] = {}
    current_rank = 0
    previous_score: int | None = None
    for code, score in ordered:
        if previous_score is None or score != previous_score:
            current_rank += 1
            previous_score = score
        ranks[code] = current_rank
    return ranks


def parse_tidy_csv(path: Path) -> list[dict[str, str]]:
    if not path.is_file():
        raise PassportDataError(f"Missing source CSV: {path}")
    with path.open(encoding="utf-8-sig", newline="") as handle:
        reader = csv.DictReader(handle)
        expected = {"Passport", "Destination", "Requirement"}
        if not reader.fieldnames or set(reader.fieldnames) != expected:
            raise PassportDataError(
                f"Unexpected CSV columns: {reader.fieldnames!r}; expected {sorted(expected)}"
            )
        rows = []
        for index, row in enumerate(reader, start=2):
            passport = (row.get("Passport") or "").strip().upper()
            destination = (row.get("Destination") or "").strip().upper()
            requirement = row.get("Requirement") or ""
            if len(passport) != 3 or not passport.isalpha():
                raise PassportDataError(f"Invalid passport ISO3 at line {index}: {passport!r}")
            if len(destination) != 3 or not destination.isalpha():
                raise PassportDataError(f"Invalid destination ISO3 at line {index}: {destination!r}")
            rows.append(
                {
                    "Passport": passport,
                    "Destination": destination,
                    "Requirement": requirement,
                }
            )
    if not rows:
        raise PassportDataError("Source CSV has no data rows")
    return rows


def audit_requirement_values(rows: list[dict[str, str]]) -> dict[str, Any]:
    known = Counter()
    unknown: list[str] = []
    for row in rows:
        raw = row["Requirement"].strip()
        try:
            req = normalize_requirement(raw)
        except PassportDataError:
            unknown.append(raw)
            continue
        label = "<numeric_days>" if req.days is not None else req.raw
        known[label] += 1
    return {
        "known": dict(sorted(known.items(), key=lambda item: (-item[1], item[0]))),
        "unknown": sorted(set(unknown)),
        "unknownCount": len(set(unknown)),
    }


def build_matrices(
    rows: list[dict[str, str]],
) -> tuple[dict[str, list[dict[str, Any]]], set[str]]:
    by_passport: dict[str, list[dict[str, Any]]] = defaultdict(list)
    countries: set[str] = set()
    seen_pairs: set[tuple[str, str]] = set()
    for row in rows:
        passport = row["Passport"]
        destination = row["Destination"]
        pair = (passport, destination)
        if pair in seen_pairs:
            raise PassportDataError(f"Duplicate passport/destination pair: {pair}")
        seen_pairs.add(pair)
        req = normalize_requirement(row["Requirement"])
        countries.add(passport)
        countries.add(destination)
        by_passport[passport].append(
            {
                "destination": destination,
                "status": req.status,
                "days": req.days,
                "raw": req.raw,
            }
        )
    for code, destinations in by_passport.items():
        destinations.sort(key=lambda item: item["destination"])
        homes = [d for d in destinations if d["status"] == STATUS_HOME]
        if len(homes) != 1 or homes[0]["destination"] != code:
            # Source uses -1 for own country; enforce consistency when present.
            if any(d["destination"] == code for d in destinations):
                own = next(d for d in destinations if d["destination"] == code)
                if own["status"] != STATUS_HOME:
                    raise PassportDataError(f"Own-country row is not home for {code}")
    return dict(by_passport), countries


def slugify(name: str, iso3: str) -> str:
    replacements = {
        "á": "a", "à": "a", "â": "a", "ã": "a", "ä": "a", "å": "a",
        "é": "e", "è": "e", "ê": "e", "ë": "e",
        "í": "i", "ì": "i", "î": "i", "ï": "i",
        "ó": "o", "ò": "o", "ô": "o", "õ": "o", "ö": "o",
        "ú": "u", "ù": "u", "û": "u", "ü": "u",
        "ñ": "n", "ç": "c", "ş": "s", "ș": "s", "ț": "t",
        "ý": "y", "ÿ": "y",
        "Á": "a", "À": "a", "Â": "a", "Ã": "a", "Ä": "a",
        "É": "e", "È": "e", "Ê": "e",
        "Í": "i", "Ó": "o", "Ö": "o", "Ú": "u", "Ü": "u",
        "Ñ": "n", "Ç": "c",
        "’": "", "'": "", "ʻ": "", "ʿ": "",
    }
    lowered = name.lower()
    for src, dst in replacements.items():
        lowered = lowered.replace(src.lower(), dst)
    # Explicit multi-char names that need stable SEO slugs.
    special = {
        "côte d’ivoire": "cote-divoire",
        "cote d’ivoire": "cote-divoire",
        "cote d'ivoire": "cote-divoire",
        "são tomé and príncipe": "sao-tome-and-principe",
        "sao tome and principe": "sao-tome-and-principe",
        "türkiye": "turkiye",
    }
    if lowered in special:
        return special[lowered]
    slug = re.sub(r"[^a-z0-9]+", "-", lowered).strip("-")
    return slug or iso3.lower()


def load_source_meta() -> dict[str, str]:
    if not SOURCE_META.is_file():
        raise PassportDataError(f"Missing source metadata: {SOURCE_META}")
    meta: dict[str, str] = {}
    for line in SOURCE_META.read_text(encoding="utf-8").splitlines():
        if ":" not in line or line.strip().startswith("-"):
            continue
        key, _, value = line.partition(":")
        meta[key.strip()] = value.strip()
    required = (
        "source_repository",
        "license",
        "dataset_update_date",
        "retrieval_timestamp_utc",
    )
    missing = [key for key in required if not meta.get(key)]
    if missing:
        raise PassportDataError(f"SOURCE_META.yml missing keys: {missing}")
    return meta


def atomic_write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(path.suffix + ".tmp")
    tmp.write_text(text, encoding="utf-8", newline="\n")
    tmp.replace(path)


def atomic_write_json(path: Path, payload: Any) -> None:
    atomic_write_text(path, json.dumps(payload, ensure_ascii=False, separators=(",", ":")) + "\n")


def compare_payload_trees(old_dir: Path, new_files: dict[Path, str]) -> bool:
    """Return True when any generated file content differs from disk."""
    for path, text in new_files.items():
        if not path.is_file() or path.read_text(encoding="utf-8") != text:
            return True
    # Detect stale generated passport JSON files that should be removed.
    if old_dir.is_dir():
        expected = set(new_files)
        for existing in old_dir.rglob("*"):
            if existing.is_file() and existing not in expected:
                # Keep directory markers only for files we manage under by-code/
                rel = existing.relative_to(old_dir)
                if rel.parts and rel.parts[0] in {"by-code", "index.json", "meta.json", "names.json"}:
                    return True
    return False
