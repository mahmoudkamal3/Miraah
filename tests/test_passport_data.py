#!/usr/bin/env python3
"""Unit tests for Mir’ah Passport Power parsing, scoring, and ranking."""

from __future__ import annotations

import json
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

import passport_core as core  # noqa: E402
import passport_locale as locale  # noqa: E402
import update_passport_data as updater  # noqa: E402


class PassportCoreTests(unittest.TestCase):
    def test_normalize_all_known_statuses(self) -> None:
        cases = [
            ("visa free", core.STATUS_VISA_FREE, None),
            ("90", core.STATUS_VISA_FREE, 90),
            ("visa on arrival", core.STATUS_VOA, None),
            ("eta", core.STATUS_ETA, None),
            ("e-visa", core.STATUS_EVISA, None),
            ("visa required", core.STATUS_REQUIRED, None),
            ("no admission", core.STATUS_NO_ADMISSION, None),
            ("-1", core.STATUS_HOME, None),
        ]
        for raw, status, days in cases:
            req = core.normalize_requirement(raw)
            self.assertEqual(req.status, status)
            self.assertEqual(req.days, days)

    def test_unknown_status_rejected(self) -> None:
        with self.assertRaises(core.PassportDataError):
            core.normalize_requirement("visa-free")
        with self.assertRaises(core.PassportDataError):
            core.normalize_requirement("freedom of movement")
        with self.assertRaises(core.PassportDataError):
            core.normalize_requirement("")

    def test_score_and_category_totals(self) -> None:
        destinations = [
            {"status": core.STATUS_VISA_FREE},
            {"status": core.STATUS_VOA},
            {"status": core.STATUS_ETA},
            {"status": core.STATUS_EVISA},
            {"status": core.STATUS_REQUIRED},
            {"status": core.STATUS_NO_ADMISSION},
            {"status": core.STATUS_HOME},
        ]
        scored = core.score_passport(destinations)
        self.assertEqual(scored["mobilityScore"], 3)
        self.assertEqual(scored["categoryTotals"][core.STATUS_VISA_FREE], 1)
        self.assertEqual(scored["categoryTotals"][core.STATUS_EVISA], 1)
        self.assertEqual(scored["destinationCount"], 6)
        self.assertEqual(scored["homeExcluded"], 1)
        totals = scored["categoryTotals"]
        self.assertEqual(
            totals[core.STATUS_VISA_FREE]
            + totals[core.STATUS_VOA]
            + totals[core.STATUS_ETA],
            scored["mobilityScore"],
        )

    def test_dense_rank_with_ties(self) -> None:
        ranks = core.dense_rank({"AAA": 10, "BBB": 10, "CCC": 8, "DDD": 8, "EEE": 3})
        self.assertEqual(ranks["AAA"], 1)
        self.assertEqual(ranks["BBB"], 1)
        self.assertEqual(ranks["CCC"], 2)
        self.assertEqual(ranks["DDD"], 2)
        self.assertEqual(ranks["EEE"], 3)

    def test_missing_values_in_matrix_builder(self) -> None:
        rows = [
            {"Passport": "AAA", "Destination": "AAA", "Requirement": "-1"},
            {"Passport": "AAA", "Destination": "BBB", "Requirement": "visa free"},
            {"Passport": "BBB", "Destination": "BBB", "Requirement": "-1"},
            {"Passport": "BBB", "Destination": "AAA", "Requirement": "visa required"},
        ]
        by_passport, countries = core.build_matrices(rows)
        self.assertEqual(countries, {"AAA", "BBB"})
        self.assertEqual(len(by_passport["AAA"]), 2)

    def test_locale_covers_fixture_codes(self) -> None:
        locale.validate_locale_coverage({"EGY", "USA", "TWN", "VAT", "XKX"})
        self.assertEqual(locale.NAME_AR["EGY"], "مصر")
        self.assertEqual(locale.NAME_EN["USA"], "United States")
        self.assertEqual(locale.ISO3_TO_ISO2["GBR"], "GB")

    def test_parse_real_source_csv_if_present(self) -> None:
        if not core.SOURCE_CSV.is_file():
            self.skipTest("source CSV not present")
        rows = core.parse_tidy_csv(core.SOURCE_CSV)
        audit = core.audit_requirement_values(rows)
        self.assertEqual(audit["unknownCount"], 0)
        self.assertGreaterEqual(len(rows), 1000)

    def test_updater_dry_run_default_and_atomic_write(self) -> None:
        fixture_csv = (
            "Passport,Destination,Requirement\n"
            "AAA,AAA,-1\n"
            "AAA,BBB,90\n"
            "AAA,CCC,visa on arrival\n"
            "AAA,DDD,eta\n"
            "AAA,EEE,e-visa\n"
            "BBB,BBB,-1\n"
            "BBB,AAA,visa required\n"
            "BBB,CCC,no admission\n"
            "BBB,DDD,visa free\n"
            "BBB,EEE,visa required\n"
            "CCC,CCC,-1\n"
            "CCC,AAA,visa free\n"
            "CCC,BBB,visa free\n"
            "CCC,DDD,visa free\n"
            "CCC,EEE,eta\n"
            "DDD,DDD,-1\n"
            "DDD,AAA,visa required\n"
            "DDD,BBB,visa required\n"
            "DDD,CCC,visa required\n"
            "DDD,EEE,visa required\n"
            "EEE,EEE,-1\n"
            "EEE,AAA,visa required\n"
            "EEE,BBB,visa required\n"
            "EEE,CCC,visa required\n"
            "EEE,DDD,visa required\n"
        )
        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            source_dir = tmp_path / "source-data" / "passport-index-data"
            public_data = tmp_path / "public" / "data" / "passports"
            source_dir.mkdir(parents=True)
            csv_path = source_dir / "passport-index-tidy-iso3.csv"
            csv_path.write_text(fixture_csv, encoding="utf-8")
            (source_dir / "SOURCE_META.yml").write_text(
                "\n".join(
                    [
                        "source_repository: https://github.com/imorte/passport-index-data",
                        "license: MIT",
                        "dataset_update_date: 2026-02-17",
                        "retrieval_timestamp_utc: 2026-08-03T00:00:00Z",
                    ]
                )
                + "\n",
                encoding="utf-8",
            )

            # Extend locale for fixture codes only inside this test.
            extra_codes = {"AAA", "BBB", "CCC", "DDD", "EEE"}
            for code in extra_codes:
                locale.NAME_EN[code] = f"Country {code}"
                locale.NAME_AR[code] = f"دولة {code}"
                locale.ISO3_TO_ISO2[code] = code[:2]

            dash = tmp_path / "public" / "dashboard.html"
            dash.parent.mkdir(parents=True, exist_ok=True)
            countries = {
                code: {"name": f"Country {code}", "region": "Test Region"}
                for code in extra_codes
            }
            dash.write_text(
                'const DATA={"countries":'
                + json.dumps(countries)
                + ',"indicatorMeta":{}};',
                encoding="utf-8",
            )

            with mock.patch.object(core, "SOURCE_DIR", source_dir), mock.patch.object(
                core, "SOURCE_CSV", csv_path
            ), mock.patch.object(core, "SOURCE_META", source_dir / "SOURCE_META.yml"), mock.patch.object(
                core, "PUBLIC_DATA", public_data
            ), mock.patch.object(updater, "ROOT", tmp_path):
                dry = updater.run(write=False, refresh_source=False)
                self.assertTrue(dry["wouldWrite"])
                self.assertFalse(dry["wrote"])
                self.assertFalse(public_data.exists())

                written = updater.run(write=True, refresh_source=False)
                self.assertTrue(written["wrote"])
                self.assertTrue((public_data / "index.json").is_file())
                index = json.loads((public_data / "index.json").read_text(encoding="utf-8"))
                by_score = {p["iso3"]: p for p in index["passports"]}
                self.assertEqual(by_score["CCC"]["mobilityScore"], 4)
                self.assertEqual(by_score["AAA"]["mobilityScore"], 3)
                self.assertEqual(by_score["CCC"]["rank"], 1)
                self.assertEqual(by_score["AAA"]["rank"], 2)

                again = updater.run(write=True, refresh_source=False)
                self.assertFalse(again["wouldWrite"])
                self.assertFalse(again["wrote"])

    def test_cli_defaults_to_dry_run(self) -> None:
        with mock.patch.object(updater, "run", return_value={
            "wouldWrite": False,
            "passportCount": 0,
            "datasetUpdateDate": "2026-02-17",
            "wrote": False,
            "mapping": {"passportNotInMiraah": [], "miraahWithoutPassport": []},
        }) as run_mock:
            code = updater.main([])
            self.assertEqual(code, 0)
            run_mock.assert_called_once_with(write=False, refresh_source=False)


if __name__ == "__main__":
    unittest.main()
