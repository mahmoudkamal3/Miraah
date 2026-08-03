#!/usr/bin/env python3
"""Unit tests for the hardened World Bank updater."""

from __future__ import annotations

import copy
import json
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

import update_world_bank as wb  # noqa: E402


INDICATOR_META = {
    "life_expectancy": {
        "code": "SP.DYN.LE00.IN",
        "label": "Life expectancy",
        "unit": "years",
        "direction": "higher",
    },
    "gdp_ppp": {
        "code": "NY.GDP.PCAP.PP.CD",
        "label": "GDP PPP",
        "unit": "$",
        "direction": "higher",
    },
    "gni_ppp": {
        "code": "NY.GNP.PCAP.PP.CD",
        "label": "GNI PPP",
        "unit": "$",
        "direction": "higher",
    },
    "unemployment": {
        "code": "SL.UEM.TOTL.ZS",
        "label": "Unemployment",
        "unit": "%",
        "direction": "lower",
    },
    "inflation": {
        "code": "FP.CPI.TOTL.ZG",
        "label": "Inflation",
        "unit": "%",
        "direction": "lower",
    },
    "internet": {
        "code": "IT.NET.USER.ZS",
        "label": "Internet",
        "unit": "%",
        "direction": "higher",
    },
    "homicides": {
        "code": "VC.IHR.PSRC.P5",
        "label": "Homicides",
        "unit": "per 100k",
        "direction": "lower",
    },
    "health_spend": {
        "code": "SH.XPD.CHEX.PP.CD",
        "label": "Health",
        "unit": "$",
        "direction": "higher",
    },
    "labor_participation": {
        "code": "SL.TLF.CACT.ZS",
        "label": "Labor",
        "unit": "%",
        "direction": "higher",
    },
    "urban_population": {
        "code": "SP.URB.TOTL.IN.ZS",
        "label": "Urban",
        "unit": "%",
        "direction": "neutral",
    },
    "renewable_energy": {
        "code": "EG.FEC.RNEW.ZS",
        "label": "Renewable",
        "unit": "%",
        "direction": "higher",
    },
    "population": {
        "code": "SP.POP.TOTL",
        "label": "Population",
        "unit": "people",
        "direction": "neutral",
    },
}


def make_payload(*, stale_year: bool = True) -> dict:
    indicators = {
        key: {"2020": 10.0 + i, "2023": 20.0 + i}
        for i, key in enumerate(INDICATOR_META)
    }
    if stale_year:
        # Stale year that should disappear when API returns null for 2022.
        indicators["life_expectancy"]["2022"] = 99.0
    return {
        "countries": {
            "AAA": {
                "name": "Alpha",
                "region": "Test",
                "income": "High income",
                "indicators": copy.deepcopy(indicators),
                "happiness": {"2025": {"score": 7.1, "rank": 1, "gdp": 1.2}},
            },
            "BBB": {
                "name": "Beta",
                "region": "Test",
                "income": "Low income",
                "indicators": copy.deepcopy(indicators),
                "happiness": {"2025": {"score": 5.5, "rank": 50, "gdp": 0.8}},
            },
        },
        "indicatorMeta": copy.deepcopy(INDICATOR_META),
        "sources": {
            "wdi": "old-wdi",
            "happiness": "World Happiness Report 2026, Figure 2.1 data",
        },
        "updatedAt": "2020-01-01T00:00:00Z",
        "years": [str(y) for y in range(2000, 2026)],
    }


def wrap_html(payload: dict, blank_lines: int = 2) -> str:
    encoded = json.dumps(payload, ensure_ascii=False, separators=(",", ":"))
    gaps = "\n" * blank_lines
    return (
        "<!doctype html><html><body><script>"
        f"const DATA={encoded};{gaps}const $=s=>document.querySelector(s);"
        "init();</script></body></html>"
    )


def api_rows_for_code(wdi_code: str, *, include_null_2022: bool = True) -> list[dict]:
    """Build enough synthetic rows to pass validation thresholds."""
    rows: list[dict] = []
    # Pad with known countries repeating years so observation counts pass.
    countries = ["AAA", "BBB"] + [f"C{i:03d}" for i in range(160)]
    # Only AAA/BBB exist in payload; the Cxxx codes are skipped as non-roster.
    for iso in ["AAA", "BBB"]:
        for year in range(2000, 2026):
            value: float | None = float((year % 50) + hash(wdi_code) % 7)
            if include_null_2022 and year == 2022 and wdi_code == "SP.DYN.LE00.IN":
                value = None
            rows.append(
                {
                    "countryiso3code": iso,
                    "date": str(year),
                    "value": value,
                    "indicator": {"id": wdi_code},
                }
            )
    # Extra padding rows with unknown ISO3 (aggregates) — must be ignored.
    for year in range(2000, 2026):
        rows.append(
            {
                "countryiso3code": "WLD",
                "date": str(year),
                "value": 1.0,
                "indicator": {"id": wdi_code},
            }
        )
    # Still need MIN_ROWS_PER_INDICATOR (500) and MIN_OBSERVATIONS (1000).
    # With 2 countries * 26 years = 52 usable, need more known countries in payload
    # OR lower thresholds in tests via patch.
    return rows


class UpdaterTests(unittest.TestCase):
    def setUp(self) -> None:
        # Lower thresholds for compact fixtures.
        self._patches = [
            mock.patch.object(wb, "MIN_COUNTRIES", 2),
            mock.patch.object(wb, "MIN_ROWS_PER_INDICATOR", 10),
            mock.patch.object(wb, "MIN_OBSERVATIONS_PER_INDICATOR", 20),
        ]
        for p in self._patches:
            p.start()

    def tearDown(self) -> None:
        for p in self._patches:
            p.stop()
        wb.request_json_fn = None

    def test_parse_flexible_blank_lines_before_const_dollar(self) -> None:
        payload = make_payload()
        for blanks in (0, 1, 2, 5):
            # blank_lines=0 means ";const $=" — still valid with regex
            html = wrap_html(payload, blank_lines=blanks)
            if blanks == 0:
                html = html.replace(";const $=", ";const $=")
            parsed = wb.read_payload(html)
            self.assertEqual(parsed["countries"]["AAA"]["name"], "Alpha")
            rebuilt = wb.embed_payload(html, parsed)
            self.assertEqual(wb.read_payload(rebuilt)["updatedAt"], payload["updatedAt"])
            self.assertIn("const $=", rebuilt)

    def test_parse_multiple_blank_lines_and_spaces(self) -> None:
        payload = make_payload()
        encoded = json.dumps(payload, ensure_ascii=False, separators=(",", ":"))
        html = f"<script>const DATA={encoded};\n\n\n   \nconst $=s=>0;</script>"
        parsed = wb.read_payload(html)
        self.assertIn("AAA", parsed["countries"])
        out = wb.embed_payload(html, parsed)
        self.assertRegex(out, r"\};\s*const\s+\$\s*=")

    def _fetch_factory(
        self,
        *,
        pages: int = 1,
        fail_page: int | None = None,
        null_2022: bool = True,
        mutate: dict[str, float] | None = None,
    ):
        def fetch(code: str, end_year: int) -> tuple[list[dict], int]:
            del end_year
            if pages == 1:
                if fail_page == 1:
                    raise wb.UpdateError(f"simulated failure for {code}")
                rows = api_rows_for_code(code, include_null_2022=null_2022)
                if mutate and code == "SP.DYN.LE00.IN":
                    for row in rows:
                        if row["countryiso3code"] == "AAA" and row["date"] == "2023":
                            row["value"] = mutate["AAA_2023"]
                # Ensure enough rows
                while len(rows) < 30:
                    rows.append(
                        {
                            "countryiso3code": "AAA",
                            "date": "2010",
                            "value": 1.0,
                            "indicator": {"id": code},
                        }
                    )
                return rows, 1

            # Multi-page simulation via request_json_fn
            raise AssertionError("use request_json pagination path")

        return fetch

    def test_pagination_fetches_all_pages(self) -> None:
        calls = {"n": 0}

        def fake_request(url: str):
            from urllib.parse import parse_qs, urlparse

            calls["n"] += 1
            qs = parse_qs(urlparse(url).query)
            page = int(qs["page"][0])
            code = url.split("/indicator/")[1].split("?")[0]
            if page == 1:
                rows = [
                    {
                        "countryiso3code": "AAA",
                        "date": str(2000 + i),
                        "value": float(i),
                        "indicator": {"id": code},
                    }
                    for i in range(15)
                ]
                return [{"page": 1, "pages": 2, "total": 30, "per_page": 15}, rows]
            if page == 2:
                rows = [
                    {
                        "countryiso3code": "BBB",
                        "date": str(2000 + i),
                        "value": float(i + 10),
                        "indicator": {"id": code},
                    }
                    for i in range(15)
                ]
                return [{"page": 2, "pages": 2, "total": 30, "per_page": 15}, rows]
            raise wb.UpdateError(f"unexpected page {page}")

        wb.request_json_fn = fake_request
        rows, pages = wb.fetch_indicator_pages("SP.DYN.LE00.IN", 2025, per_page=15)
        self.assertEqual(pages, 2)
        self.assertEqual(len(rows), 30)
        self.assertEqual(calls["n"], 2)

    def test_pagination_failure_aborts(self) -> None:
        def fake_request(url: str):
            from urllib.parse import parse_qs, urlparse

            page = int(parse_qs(urlparse(url).query)["page"][0])
            if page == 1:
                return [
                    {"page": 1, "pages": 2, "total": 2, "per_page": 1},
                    [{"countryiso3code": "AAA", "date": "2020", "value": 1.0}],
                ]
            raise wb.UpdateError("page 2 exploded")

        wb.request_json_fn = fake_request
        with self.assertRaises(wb.UpdateError):
            wb.fetch_indicator_pages("SP.DYN.LE00.IN", 2025, per_page=1)

    def test_null_removes_stale_stored_year(self) -> None:
        payload = make_payload(stale_year=True)
        self.assertIn("2022", payload["countries"]["AAA"]["indicators"]["life_expectancy"])

        def fetch(code: str, end_year: int):
            del end_year
            rows = []
            for iso in ("AAA", "BBB"):
                for year in range(2000, 2026):
                    value = None if (code == "SP.DYN.LE00.IN" and year == 2022) else float(year)
                    rows.append(
                        {
                            "countryiso3code": iso,
                            "date": str(year),
                            "value": value,
                            "indicator": {"id": code},
                        }
                    )
            return rows, 1

        new_payload, summary = wb.refresh_payload(payload, end_year=2025, fetch_fn=fetch)
        self.assertNotIn(
            "2022",
            new_payload["countries"]["AAA"]["indicators"]["life_expectancy"],
        )
        self.assertGreaterEqual(summary["valuesRemoved"], 1)

    def test_api_failure_zero_file_changes(self) -> None:
        payload = make_payload()
        html = wrap_html(payload)
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            dash = root / "dashboard.html"
            compare = root / "compare" / "index.html"
            compare.parent.mkdir(parents=True, exist_ok=True)
            dash.write_text(html, encoding="utf-8")
            compare.write_text(html, encoding="utf-8")
            before_d = dash.read_bytes()
            before_i = compare.read_bytes()

            def fetch(code: str, end_year: int):
                del end_year
                if code == "SL.UEM.TOTL.ZS":
                    raise wb.UpdateError("boom")
                rows = [
                    {
                        "countryiso3code": iso,
                        "date": str(year),
                        "value": 1.0,
                        "indicator": {"id": code},
                    }
                    for iso in ("AAA", "BBB")
                    for year in range(2000, 2026)
                ]
                return rows, 1

            code, summary = wb.run(
                write=True,
                end_year=2025,
                target=dash,
                compare=compare,
                fetch_fn=fetch,
            )
            self.assertEqual(code, 1)
            self.assertTrue(summary["errors"])
            self.assertEqual(dash.read_bytes(), before_d)
            self.assertEqual(compare.read_bytes(), before_i)

    def test_dry_run_zero_file_changes(self) -> None:
        payload = make_payload(stale_year=True)

        def fetch(code: str, end_year: int):
            del end_year
            rows = [
                {
                    "countryiso3code": iso,
                    "date": str(year),
                    "value": float(year) + (0 if code != "SP.DYN.LE00.IN" else 0.5),
                    "indicator": {"id": code},
                }
                for iso in ("AAA", "BBB")
                for year in range(2000, 2026)
                if not (code == "SP.DYN.LE00.IN" and year == 2022)
            ]
            return rows, 1

        html = wrap_html(payload)
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            dash = root / "dashboard.html"
            compare = root / "compare" / "index.html"
            compare.parent.mkdir(parents=True, exist_ok=True)
            dash.write_text(html, encoding="utf-8")
            compare.write_text(html, encoding="utf-8")
            before_d = dash.read_bytes()
            before_i = compare.read_bytes()
            mtime_d = dash.stat().st_mtime_ns

            code, summary = wb.run(
                write=False,
                end_year=2025,
                target=dash,
                compare=compare,
                fetch_fn=fetch,
            )
            self.assertEqual(code, 0)
            self.assertTrue(summary["changed"])
            self.assertFalse(summary["wrote"])
            self.assertEqual(summary["mode"], "dry-run")
            self.assertEqual(dash.read_bytes(), before_d)
            self.assertEqual(compare.read_bytes(), before_i)
            self.assertEqual(dash.stat().st_mtime_ns, mtime_d)

    def test_happiness_preservation(self) -> None:
        payload = make_payload()
        before = wb.happiness_snapshot(payload)

        def fetch(code: str, end_year: int):
            del end_year
            rows = [
                {
                    "countryiso3code": iso,
                    "date": str(year),
                    "value": 3.0,
                    "indicator": {"id": code},
                }
                for iso in ("AAA", "BBB")
                for year in range(2000, 2026)
            ]
            return rows, 1

        new_payload, _ = wb.refresh_payload(payload, end_year=2025, fetch_fn=fetch)
        self.assertEqual(wb.happiness_snapshot(new_payload), before)
        self.assertEqual(
            new_payload["countries"]["AAA"]["happiness"]["2025"]["score"],
            7.1,
        )

    def test_query_end_year_is_used_for_api_but_years_follow_observations(self) -> None:
        payload = make_payload()

        def fetch(code: str, end_year: int):
            self.assertEqual(end_year, 2031)
            # Observations only through 2028 even though API was queried to 2031.
            rows = [
                {
                    "countryiso3code": iso,
                    "date": str(year),
                    "value": 1.0,
                    "indicator": {"id": code},
                }
                for iso in ("AAA", "BBB")
                for year in range(2000, 2029)
            ]
            return rows, 1

        new_payload, summary = wb.refresh_payload(payload, end_year=2031, fetch_fn=fetch)
        self.assertEqual(summary["queryEndYear"], 2031)
        self.assertEqual(summary["observedEndYear"], 2028)
        self.assertEqual(summary["endYear"], 2028)
        self.assertEqual(new_payload["years"][0], "2000")
        self.assertEqual(new_payload["years"][-1], "2028")
        self.assertNotIn("2031", new_payload["years"])
        self.assertNotIn("2029", new_payload["years"])

    def test_current_year_without_observations_excluded_from_years(self) -> None:
        payload = make_payload()

        def fetch(code: str, end_year: int):
            self.assertEqual(end_year, 2026)
            rows = [
                {
                    "countryiso3code": iso,
                    "date": str(year),
                    "value": 1.0 if year <= 2025 else None,
                    "indicator": {"id": code},
                }
                for iso in ("AAA", "BBB")
                for year in range(2000, 2027)
            ]
            return rows, 1

        new_payload, summary = wb.refresh_payload(payload, end_year=2026, fetch_fn=fetch)
        self.assertEqual(summary["queryEndYear"], 2026)
        self.assertEqual(summary["observedEndYear"], 2025)
        self.assertEqual(new_payload["years"][-1], "2025")
        self.assertNotIn("2026", new_payload["years"])
        # Per-indicator latest remains based on actual observations.
        self.assertEqual(
            max(new_payload["countries"]["AAA"]["indicators"]["population"]),
            "2025",
        )

    def test_current_year_with_observations_included_in_years(self) -> None:
        payload = make_payload()

        def fetch(code: str, end_year: int):
            self.assertEqual(end_year, 2026)
            rows = [
                {
                    "countryiso3code": iso,
                    "date": str(year),
                    "value": 1.0,
                    "indicator": {"id": code},
                }
                for iso in ("AAA", "BBB")
                for year in range(2000, 2027)
            ]
            return rows, 1

        new_payload, summary = wb.refresh_payload(payload, end_year=2026, fetch_fn=fetch)
        self.assertEqual(summary["observedEndYear"], 2026)
        self.assertEqual(new_payload["years"][-1], "2026")
        self.assertIn("2026", new_payload["years"])

    def test_no_value_or_year_changes_would_write_false(self) -> None:
        payload = make_payload(stale_year=False)

        def fetch(code: str, end_year: int):
            del end_year
            rows = [
                {
                    "countryiso3code": iso,
                    "date": str(year),
                    "value": 1.0,
                    "indicator": {"id": code},
                }
                for iso in ("AAA", "BBB")
                for year in range(2000, 2026)
            ]
            return rows, 1

        for iso in payload["countries"]:
            for key in INDICATOR_META:
                payload["countries"][iso]["indicators"][key] = {
                    str(year): 1.0 for year in range(2000, 2026)
                }
        payload["years"] = [str(y) for y in range(2000, 2026)]
        original_updated = payload["updatedAt"]
        original_sources = copy.deepcopy(payload["sources"])

        html = wrap_html(payload)
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            dash = root / "dashboard.html"
            compare = root / "compare" / "index.html"
            compare.parent.mkdir(parents=True, exist_ok=True)
            dash.write_text(html, encoding="utf-8")
            compare.write_text(html, encoding="utf-8")

            code, summary = wb.run(
                write=False,
                end_year=2026,
                target=dash,
                compare=compare,
                fetch_fn=fetch,
            )
            self.assertEqual(code, 0)
            self.assertFalse(summary["changed"])
            self.assertFalse(summary["wouldWrite"])
            self.assertFalse(summary["wrote"])
            self.assertEqual(summary["message"], "No data changes")
            self.assertEqual(summary["observedEndYear"], 2025)
            self.assertEqual(summary["endYear"], 2025)
            # Re-check via refresh_payload that metadata stays put.
            new_payload, refresh_summary = wb.refresh_payload(
                payload, end_year=2026, fetch_fn=fetch
            )
            self.assertFalse(refresh_summary["changed"])
            self.assertEqual(new_payload["updatedAt"], original_updated)
            self.assertEqual(new_payload["sources"], original_sources)
            self.assertEqual(new_payload["years"][-1], "2025")

    def test_byte_identical_output_files(self) -> None:
        payload = make_payload(stale_year=True)

        def fetch(code: str, end_year: int):
            del end_year
            rows = [
                {
                    "countryiso3code": iso,
                    "date": str(year),
                    "value": float(year),
                    "indicator": {"id": code},
                }
                for iso in ("AAA", "BBB")
                for year in range(2000, 2026)
                if not (code == "SP.DYN.LE00.IN" and year == 2022)
            ]
            return rows, 1

        html = wrap_html(payload, blank_lines=2)
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            dash = root / "dashboard.html"
            compare = root / "compare" / "index.html"
            compare.parent.mkdir(parents=True, exist_ok=True)
            dash.write_text(html, encoding="utf-8")
            compare.write_text(html, encoding="utf-8")

            code, summary = wb.run(
                write=True,
                end_year=2025,
                target=dash,
                compare=compare,
                fetch_fn=fetch,
            )
            self.assertEqual(code, 0)
            self.assertTrue(summary["wrote"])
            self.assertEqual(dash.read_bytes(), compare.read_bytes())
            # Happiness still present
            parsed = wb.read_payload(dash.read_text(encoding="utf-8"))
            self.assertEqual(parsed["countries"]["AAA"]["happiness"]["2025"]["score"], 7.1)
            self.assertNotIn("2022", parsed["countries"]["AAA"]["indicators"]["life_expectancy"])

    def test_no_changes_skips_updated_at(self) -> None:
        payload = make_payload(stale_year=False)

        def fetch(code: str, end_year: int):
            del end_year
            rows = []
            for iso in ("AAA", "BBB"):
                for year in range(2000, 2026):
                    rows.append(
                        {
                            "countryiso3code": iso,
                            "date": str(year),
                            "value": 1.0,
                            "indicator": {"id": code},
                        }
                    )
            return rows, 1

        for iso in payload["countries"]:
            for key in INDICATOR_META:
                payload["countries"][iso]["indicators"][key] = {
                    str(year): 1.0 for year in range(2000, 2026)
                }
        payload["years"] = [str(y) for y in range(2000, 2026)]
        original_updated = payload["updatedAt"]

        new_payload, summary = wb.refresh_payload(payload, end_year=2026, fetch_fn=fetch)
        self.assertFalse(summary["changed"])
        self.assertFalse(summary["yearsChanged"])
        self.assertEqual(summary["observedEndYear"], 2025)
        self.assertEqual(new_payload["updatedAt"], original_updated)
        self.assertEqual(new_payload["years"][-1], "2025")
        self.assertNotIn("2026", new_payload["years"])

    def test_default_cli_is_dry_run(self) -> None:
        args = wb.parse_args([])
        self.assertFalse(args.write)
        args_write = wb.parse_args(["--write"])
        self.assertTrue(args_write.write)



    def test_updater_never_overwrites_homepage(self) -> None:
        payload = make_payload(stale_year=True)

        def fetch(code: str, end_year: int):
            del end_year
            rows = [
                {
                    "countryiso3code": iso,
                    "date": str(year),
                    "value": float(year),
                    "indicator": {"id": code},
                }
                for iso in ("AAA", "BBB")
                for year in range(2000, 2026)
                if not (code == "SP.DYN.LE00.IN" and year == 2022)
            ]
            return rows, 1

        html = wrap_html(payload, blank_lines=2)
        homepage_html = "<!doctype html><html><body><div class=\"home-hero\"></div><script>const HOME_BOOT={}</script></body></html>"
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            dash = root / "dashboard.html"
            compare = root / "compare" / "index.html"
            home = root / "index.html"
            compare.parent.mkdir(parents=True, exist_ok=True)
            dash.write_text(html, encoding="utf-8")
            compare.write_text(html, encoding="utf-8")
            home.write_text(homepage_html, encoding="utf-8")
            before = home.read_bytes()
            code, summary = wb.run(
                write=True,
                end_year=2025,
                target=dash,
                compare=compare,
                homepage=home,
                fetch_fn=fetch,
            )
            self.assertEqual(code, 0)
            self.assertTrue(summary["wrote"])
            self.assertEqual(home.read_bytes(), before)
            self.assertIn("HOME_BOOT", home.read_text(encoding="utf-8"))
            self.assertEqual(dash.read_bytes(), compare.read_bytes())
            self.assertNotEqual(dash.read_bytes(), before)


if __name__ == "__main__":
    unittest.main()
