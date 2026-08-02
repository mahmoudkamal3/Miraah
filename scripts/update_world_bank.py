#!/usr/bin/env python3
"""Refresh embedded WDI series while retaining the last known-good dashboard.

Default mode is --dry-run (fetch + validate, no file writes).
Pass --write to update public/dashboard.html and public/index.html.
"""

from __future__ import annotations

import argparse
import copy
import json
import math
import re
import sys
import tempfile
import time
import urllib.error
import urllib.parse
import urllib.request
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Callable


ROOT = Path(__file__).resolve().parents[1]
PUBLIC = ROOT / "public"
TARGET = PUBLIC / "dashboard.html"
INDEX = PUBLIC / "index.html"

DATA_START_RE = re.compile(r"const\s+DATA\s*=")
DATA_END_RE = re.compile(r"const\s+\$\s*=")

START_YEAR = 2000
EXPECTED_INDICATOR_COUNT = 12
MIN_COUNTRIES = 150
MIN_ROWS_PER_INDICATOR = 500
MIN_OBSERVATIONS_PER_INDICATOR = 1000
USER_AGENT = "CountryMirror/1.0"
WDI_SOURCE = "World Bank Indicators API v2 (source 2: WDI)"
HAPPINESS_SOURCE = "World Happiness Report 2026, Figure 2.1 data"

# Injected in tests.
request_json_fn: Callable[[str], Any] | None = None


class UpdateError(RuntimeError):
    """Fatal refresh error; production files must not be modified."""


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


def current_end_year(now: datetime | None = None) -> int:
    return (now or utc_now()).year


def build_years(end_year: int | None = None) -> list[str]:
    end = end_year if end_year is not None else current_end_year()
    if end < START_YEAR:
        raise UpdateError(f"Invalid years end {end}; must be >= {START_YEAR}")
    return [str(y) for y in range(START_YEAR, end + 1)]


def latest_observed_year(payload: dict) -> int | None:
    """Latest year with at least one finite observation in accepted country indicators."""
    latest: int | None = None
    for country in payload.get("countries", {}).values():
        indicators = country.get("indicators") or {}
        if not isinstance(indicators, dict):
            continue
        for series in indicators.values():
            if not isinstance(series, dict):
                continue
            for year, value in series.items():
                if not str(year).isdigit() or not is_finite_number(value):
                    continue
                year_i = int(year)
                if latest is None or year_i > latest:
                    latest = year_i
    return latest


def years_from_observations(payload: dict) -> list[str]:
    latest = latest_observed_year(payload)
    if latest is None:
        raise UpdateError("No valid indicator observations found to build DATA.years")
    return build_years(latest)


def locate_data_spans(html: str) -> tuple[int, int, int]:
    """Return (json_start, after_assignment, const_dollar_start).

    json_start: first char of the DATA JSON value
    after_assignment: index just past the trailing ';' of the DATA statement
    const_dollar_start: index of the following ``const $=``
    """
    start_match = DATA_START_RE.search(html)
    if not start_match:
        raise UpdateError("Could not locate const DATA= in dashboard HTML")
    json_start = start_match.end()
    end_match = DATA_END_RE.search(html, json_start)
    if not end_match:
        raise UpdateError("Could not locate const $= after DATA block")
    between = html[json_start : end_match.start()]
    stripped = between.rstrip()
    if not stripped.endswith(";"):
        raise UpdateError("DATA assignment is missing a terminating semicolon")
    # Index of ';' relative to json_start inside `between`
    semi_rel = len(stripped) - 1
    # Map back accounting for trailing whitespace removed by rstrip
    # stripped is between without trailing WS, so ';' is at json_start + semi_rel
    after_assignment = json_start + semi_rel + 1
    return json_start, after_assignment, end_match.start()


def extract_data_json(html: str) -> str:
    json_start, after_assignment, _ = locate_data_spans(html)
    return html[json_start : after_assignment - 1].strip()


def read_payload(html: str) -> dict:
    try:
        return json.loads(extract_data_json(html))
    except json.JSONDecodeError as exc:
        raise UpdateError(f"Embedded DATA JSON is invalid: {exc}") from exc


def embed_payload(html: str, payload: dict) -> str:
    """Replace DATA JSON, preserving the HTML shell and flexible whitespace before const $=."""
    json_start, after_assignment, const_dollar = locate_data_spans(html)
    encoded = json.dumps(payload, ensure_ascii=False, separators=(",", ":"))
    whitespace = html[after_assignment:const_dollar]
    if not whitespace:
        whitespace = "\n\n"
    return html[:json_start] + encoded + ";" + whitespace + html[const_dollar:]


def request_json(url: str, attempts: int = 4) -> Any:
    if request_json_fn is not None:
        return request_json_fn(url)
    error: Exception | None = None
    for attempt in range(attempts):
        try:
            req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
            with urllib.request.urlopen(req, timeout=60) as response:
                return json.load(response)
        except (urllib.error.URLError, TimeoutError, json.JSONDecodeError, OSError) as exc:
            error = exc
            time.sleep(2**attempt)
    raise UpdateError(f"API request failed after {attempts} attempts: {error}")


def fetch_indicator_pages(
    code: str,
    end_year: int,
    per_page: int = 20000,
) -> tuple[list[dict], int]:
    """Fetch all pages for one WDI indicator. Fails if any page is missing/invalid."""
    all_rows: list[dict] = []
    page = 1
    total_pages = None
    while True:
        params = urllib.parse.urlencode(
            {
                "format": "json",
                "date": f"{START_YEAR}:{end_year}",
                "per_page": str(per_page),
                "page": str(page),
                "source": "2",
            }
        )
        url = f"https://api.worldbank.org/v2/country/all/indicator/{code}?{params}"
        data = request_json(url)
        if not isinstance(data, list) or len(data) < 2:
            raise UpdateError(f"Unexpected World Bank response for {code} page {page}")
        meta, rows = data[0], data[1]
        if not isinstance(meta, dict):
            raise UpdateError(f"Missing pagination metadata for {code} page {page}")
        if rows is None:
            rows = []
        if not isinstance(rows, list):
            raise UpdateError(f"Invalid row payload for {code} page {page}")
        pages = int(meta.get("pages") or 0)
        if pages < 1:
            raise UpdateError(f"Invalid pages metadata for {code}: {meta.get('pages')!r}")
        if total_pages is None:
            total_pages = pages
        elif pages != total_pages:
            raise UpdateError(
                f"Inconsistent pages metadata for {code}: expected {total_pages}, got {pages}"
            )
        current = int(meta.get("page") or page)
        if current != page:
            raise UpdateError(f"Unexpected page index for {code}: wanted {page}, got {current}")
        all_rows.extend(rows)
        if page >= total_pages:
            break
        page += 1
    return all_rows, total_pages or 0


def is_finite_number(value: Any) -> bool:
    try:
        number = float(value)
    except (TypeError, ValueError):
        return False
    return math.isfinite(number)


def build_series_from_rows(
    rows: list[dict],
    known_countries: set[str],
) -> tuple[dict[str, dict[str, float]], int, int]:
    """Return {iso3: {year: value}}, usable_row_count, skipped_unknown_iso3."""
    series_by_country: dict[str, dict[str, float]] = {}
    usable = 0
    skipped_unknown = 0
    for row in rows:
        if not isinstance(row, dict):
            continue
        code = row.get("countryiso3code") or ""
        year = str(row.get("date", ""))
        value = row.get("value")
        if not code or not year.isdigit():
            continue
        if code not in known_countries:
            # Aggregates / extras — never insert into DATA.countries
            skipped_unknown += 1
            continue
        if value is None:
            continue
        if not is_finite_number(value):
            raise UpdateError(f"Non-finite value for {code} {year}: {value!r}")
        series_by_country.setdefault(code, {})[year] = round(float(value), 4)
        usable += 1
    return series_by_country, usable, skipped_unknown


def happiness_snapshot(payload: dict) -> str:
    happy = {code: country.get("happiness") for code, country in payload["countries"].items()}
    return json.dumps(happy, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


def metadata_snapshot(payload: dict) -> str:
    meta = {
        code: {
            "name": country.get("name"),
            "region": country.get("region"),
            "income": country.get("income"),
            "currency": country.get("currency"),
        }
        for code, country in payload["countries"].items()
    }
    return json.dumps(
        {"countries": meta, "indicatorMeta": payload.get("indicatorMeta")},
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    )


def indicators_snapshot(payload: dict) -> str:
    data = {
        code: country.get("indicators", {})
        for code, country in payload["countries"].items()
    }
    return json.dumps(data, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


def empty_summary(query_end_year: int) -> dict[str, Any]:
    return {
        "mode": "dry-run",
        "queryEndYear": query_end_year,
        "observedEndYear": None,
        "endYear": None,
        "years": [],
        "indicatorsFetched": 0,
        "pages": {},
        "countriesInPayload": 0,
        "countriesTouched": 0,
        "valuesAdded": 0,
        "valuesChanged": 0,
        "valuesRemoved": 0,
        "indicatorStats": {},
        "changed": False,
        "wouldWrite": False,
        "wrote": False,
        "errors": [],
        "message": "",
    }


def compare_series(
    old: dict[str, float],
    new: dict[str, float],
) -> tuple[int, int, int]:
    added = changed = removed = 0
    for year, value in new.items():
        if year not in old:
            added += 1
        elif old[year] != value:
            changed += 1
    for year in old:
        if year not in new:
            removed += 1
    return added, changed, removed


def refresh_payload(
    payload: dict,
    *,
    end_year: int | None = None,
    fetch_fn: Callable[[str, int], tuple[list[dict], int]] | None = None,
) -> tuple[dict, dict[str, Any]]:
    """Fetch all indicators and return (new_payload, summary). Never writes files."""
    if "countries" not in payload or "indicatorMeta" not in payload:
        raise UpdateError("DATA payload missing countries or indicatorMeta")

    end = end_year if end_year is not None else current_end_year()
    summary = empty_summary(end)
    summary["countriesInPayload"] = len(payload["countries"])
    known = set(payload["countries"])

    if len(payload["indicatorMeta"]) != EXPECTED_INDICATOR_COUNT:
        raise UpdateError(
            f"Expected {EXPECTED_INDICATOR_COUNT} indicators, found {len(payload['indicatorMeta'])}"
        )

    if len(known) < MIN_COUNTRIES:
        raise UpdateError(f"Country roster too small: {len(known)} < {MIN_COUNTRIES}")

    happy_before = happiness_snapshot(payload)
    meta_before = metadata_snapshot(payload)
    indicators_before = indicators_snapshot(payload)
    years_before = list(payload.get("years") or [])

    working = copy.deepcopy(payload)
    fetch = fetch_fn or (lambda code, ey: fetch_indicator_pages(code, ey))
    touched_countries: set[str] = set()

    for key, meta in working["indicatorMeta"].items():
        wdi_code = meta.get("code")
        if not wdi_code:
            raise UpdateError(f"indicatorMeta[{key}] missing WDI code")
        rows, pages = fetch(wdi_code, end)
        summary["pages"][key] = pages
        if len(rows) < MIN_ROWS_PER_INDICATOR:
            raise UpdateError(
                f"Too few API rows for {key} ({wdi_code}): {len(rows)} < {MIN_ROWS_PER_INDICATOR}"
            )
        series_map, usable, skipped_unknown = build_series_from_rows(rows, known)
        if usable < MIN_OBSERVATIONS_PER_INDICATOR:
            raise UpdateError(
                f"Too few usable observations for {key} ({wdi_code}): "
                f"{usable} < {MIN_OBSERVATIONS_PER_INDICATOR}"
            )

        added = changed = removed = 0
        for iso3, country in working["countries"].items():
            indicators = country.setdefault("indicators", {})
            old_series = dict(indicators.get(key) or {})
            new_series = dict(series_map.get(iso3) or {})
            a, c, r = compare_series(old_series, new_series)
            added += a
            changed += c
            removed += r
            if a or c or r:
                touched_countries.add(iso3)
            # Replace entire series (clears stale years that are now null/absent)
            indicators[key] = new_series

        summary["indicatorStats"][key] = {
            "code": wdi_code,
            "pages": pages,
            "apiRows": len(rows),
            "observations": usable,
            "skippedNonCountry": skipped_unknown,
            "added": added,
            "changed": changed,
            "removed": removed,
        }
        summary["valuesAdded"] += added
        summary["valuesChanged"] += changed
        summary["valuesRemoved"] += removed
        summary["indicatorsFetched"] += 1

    # DATA.years follows actual observations, not an empty queried current year.
    observed_end = latest_observed_year(working)
    if observed_end is None:
        raise UpdateError("No valid indicator observations found to build DATA.years")
    working["years"] = build_years(observed_end)
    summary["observedEndYear"] = observed_end
    summary["endYear"] = observed_end
    summary["years"] = list(working["years"])

    # Preserve happiness source attribution; only bump WDI source/updatedAt when values change.
    sources = dict(working.get("sources") or {})
    sources["happiness"] = sources.get("happiness") or HAPPINESS_SOURCE

    indicators_after = indicators_snapshot(working)
    years_after = working["years"]
    values_changed = indicators_after != indicators_before
    years_changed = years_after != years_before
    changed = values_changed or years_changed

    if changed:
        working["updatedAt"] = utc_now().strftime("%Y-%m-%dT%H:%M:%SZ")
        sources["wdi"] = WDI_SOURCE
        working["sources"] = sources
    else:
        # Keep prior updatedAt/sources exactly when nothing changed.
        working["updatedAt"] = payload.get("updatedAt")
        working["sources"] = copy.deepcopy(payload.get("sources") or sources)

    # Safety validations
    if happiness_snapshot(working) != happy_before:
        raise UpdateError("Happiness data changed unexpectedly during refresh")
    if metadata_snapshot(working) != meta_before:
        raise UpdateError("Country metadata or indicatorMeta changed unexpectedly")
    if set(working["countries"]) != known:
        raise UpdateError("Country roster changed; aggregates must not be inserted")
    if summary["indicatorsFetched"] != EXPECTED_INDICATOR_COUNT:
        raise UpdateError("Not all expected indicators were fetched")

    summary["countriesTouched"] = len(touched_countries)
    summary["changed"] = changed
    summary["valuesChangedOnly"] = values_changed
    summary["yearsChanged"] = years_changed
    summary["queryEndYear"] = end
    return working, summary


def validate_embedded_html(html: str, original_payload: dict, new_payload: dict) -> None:
    parsed = read_payload(html)
    if happiness_snapshot(parsed) != happiness_snapshot(original_payload):
        raise UpdateError("Prepared HTML lost or altered happiness data")
    if metadata_snapshot(parsed) != metadata_snapshot(original_payload):
        raise UpdateError("Prepared HTML altered country metadata or indicatorMeta")
    if indicators_snapshot(parsed) != indicators_snapshot(new_payload):
        raise UpdateError("Prepared HTML indicators do not match refreshed payload")
    if parsed.get("years") != new_payload.get("years"):
        raise UpdateError("Prepared HTML years do not match refreshed payload")


def prepare_outputs(original_html: str, new_payload: dict, original_payload: dict) -> str:
    html_out = embed_payload(original_html, new_payload)
    validate_embedded_html(html_out, original_payload, new_payload)
    # Round-trip parse must succeed
    read_payload(html_out)
    return html_out


def atomic_write_pair(html_out: str, target: Path = TARGET, index: Path = INDEX) -> None:
    target.parent.mkdir(parents=True, exist_ok=True)
    # Prepare both temps, validate, then replace.
    with tempfile.NamedTemporaryFile(
        "w", encoding="utf-8", delete=False, dir=target.parent, suffix=".tmp"
    ) as dash_tmp:
        dash_tmp.write(html_out)
        dash_path = Path(dash_tmp.name)
    with tempfile.NamedTemporaryFile(
        "w", encoding="utf-8", delete=False, dir=index.parent, suffix=".tmp"
    ) as index_tmp:
        index_tmp.write(html_out)
        index_path = Path(index_tmp.name)

    try:
        for path in (dash_path, index_path):
            text = path.read_text(encoding="utf-8")
            read_payload(text)
            if text != html_out:
                raise UpdateError("Temporary output drifted from prepared HTML")
        dash_path.replace(target)
        index_path.replace(index)
    finally:
        for path in (dash_path, index_path):
            if path.exists():
                path.unlink(missing_ok=True)

    final_dash = target.read_text(encoding="utf-8")
    final_index = index.read_text(encoding="utf-8")
    if final_dash != final_index:
        raise UpdateError("dashboard.html and index.html are not byte-identical after write")
    if final_dash != html_out:
        raise UpdateError("Written dashboard does not match prepared output")
    read_payload(final_dash)
    read_payload(final_index)


def print_summary(summary: dict[str, Any]) -> None:
    print(json.dumps(summary, ensure_ascii=False, indent=2))


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Refresh World Bank WDI series embedded in the static dashboard."
    )
    mode = parser.add_mutually_exclusive_group()
    mode.add_argument(
        "--dry-run",
        action="store_true",
        help="Fetch and validate without modifying files (default).",
    )
    mode.add_argument(
        "--write",
        action="store_true",
        help="Write updates to public/dashboard.html and public/index.html.",
    )
    parser.add_argument(
        "--end-year",
        type=int,
        default=None,
        help="Override end year (default: current UTC year).",
    )
    return parser.parse_args(argv)


def run(
    *,
    write: bool = False,
    end_year: int | None = None,
    target: Path = TARGET,
    index: Path = INDEX,
    fetch_fn: Callable[[str, int], tuple[list[dict], int]] | None = None,
) -> tuple[int, dict[str, Any]]:
    if not target.exists():
        summary = empty_summary(end_year or current_end_year())
        summary["errors"].append(f"Missing seed dashboard: {target}")
        summary["message"] = "Refresh failed safely; existing dashboard retained"
        return 2, summary

    original_html = target.read_text(encoding="utf-8")
    original_mtime = target.stat().st_mtime_ns
    index_exists = index.exists()
    index_mtime = index.stat().st_mtime_ns if index_exists else None
    index_bytes = index.read_bytes() if index_exists else None
    target_bytes = target.read_bytes()

    try:
        original_payload = read_payload(original_html)
        new_payload, summary = refresh_payload(
            original_payload, end_year=end_year, fetch_fn=fetch_fn
        )
        summary["mode"] = "write" if write else "dry-run"
        html_out = prepare_outputs(original_html, new_payload, original_payload)

        if not summary["changed"]:
            summary["wouldWrite"] = False
            summary["wrote"] = False
            summary["message"] = "No data changes"
            # Ensure dry-run / no-op did not touch files
            if target.read_bytes() != target_bytes:
                raise UpdateError("Files changed unexpectedly during no-op refresh")
            return 0, summary

        summary["wouldWrite"] = True
        if not write:
            summary["wrote"] = False
            summary["message"] = "Dry-run complete; files not modified"
            if target.read_bytes() != target_bytes:
                raise UpdateError("Dry-run modified dashboard.html")
            if index_exists and index.read_bytes() != index_bytes:
                raise UpdateError("Dry-run modified index.html")
            if target.stat().st_mtime_ns != original_mtime:
                raise UpdateError("Dry-run changed dashboard mtime")
            if index_exists and index.stat().st_mtime_ns != index_mtime:
                raise UpdateError("Dry-run changed index mtime")
            return 0, summary

        atomic_write_pair(html_out, target=target, index=index)
        summary["wrote"] = True
        summary["message"] = "Wrote public/dashboard.html and public/index.html"
        return 0, summary
    except Exception as exc:
        summary = empty_summary(end_year or current_end_year())
        summary["mode"] = "write" if write else "dry-run"
        summary["errors"].append(str(exc))
        summary["message"] = "Refresh failed safely; existing dashboard retained"
        # Verify production files untouched on failure
        try:
            if target.read_bytes() != target_bytes:
                summary["errors"].append("WARNING: dashboard.html changed after failure")
            if index_exists and index.read_bytes() != index_bytes:
                summary["errors"].append("WARNING: index.html changed after failure")
        except OSError:
            pass
        return 1, summary


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    write = bool(args.write)
    code, summary = run(write=write, end_year=args.end_year)
    print_summary(summary)
    return code


if __name__ == "__main__":
    raise SystemExit(main())
