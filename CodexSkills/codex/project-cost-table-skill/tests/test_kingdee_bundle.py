from __future__ import annotations

import hashlib
import json
import os
import sys
import tempfile
import unittest
from pathlib import Path
from typing import Mapping, Optional, Sequence


MODULE_ROOT = Path(__file__).resolve().parents[1]
SRC_ROOT = MODULE_ROOT / "src"
if str(SRC_ROOT) not in sys.path:
    sys.path.insert(0, str(SRC_ROOT))

from project_cost_table.inventory import FileIdentity, source_id_for_relative_path
from project_cost_table.manifest import SourceSelection
from project_cost_table.money import MoneyProfile
from project_cost_table.readers.kingdee import KINGDEE_READER_ID, KINGDEE_READER_VERSION, KingdeeReaderProfile
from project_cost_table.readers.kingdee_bundle import (
    KingdeeBundleError,
    KingdeeBundleProfile,
    public_bundle_summary,
    read_kingdee_bundle,
)
from project_cost_table.security import OLE_SIGNATURE, SecurityProfile

from r5_helpers import EVIDENCE, active_reader_profile, standard_rows
from synthetic_builders import write_tabular_xlsx, write_xlsx, write_zip


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _member(
    path: Path,
    archive_name: str,
    *,
    disposition: str = "INCLUDE",
    reader_profile_id: Optional[str] = "SYNTHETIC-KINGDEE-R5",
    member_sha256: Optional[str] = None,
) -> dict:
    excluded = disposition == "EXCLUDE_QUALIFIED_SCOPE"
    return {
        "member_path": archive_name,
        "member_sha256": member_sha256 or _sha256(path),
        "disposition": disposition,
        "exclusion_reason_code": "OUTSIDE_APPROVED_ENTITY_SCOPE" if excluded else None,
        "reader_profile_id": None if excluded else reader_profile_id,
        "evidence_ref": EVIDENCE,
    }


def _bundle_profile(bundle: Path, members: Sequence[Mapping[str, object]]) -> KingdeeBundleProfile:
    return KingdeeBundleProfile.from_mapping(
        {
            "schema_version": "kmfa.project_cost.kingdee_bundle_profile.v1",
            "profile_id": "SYNTHETIC-KINGDEE-BUNDLE-R5",
            "status": "ACTIVE",
            "schema_id": "schema.synthetic.kingdee.bundle.r5.v1",
            "bundle_source_sha256": _sha256(bundle),
            "evidence_refs": [EVIDENCE],
            "members": list(members),
        }
    )


def _bundle_selection(root: Path, bundle: Path, profile: KingdeeBundleProfile) -> SourceSelection:
    metadata = bundle.stat()
    relative_path = bundle.relative_to(root).as_posix()
    return SourceSelection(
        slot_id="general_ledger",
        source_id=source_id_for_relative_path(relative_path),
        private_relative_path=relative_path,
        sha256=_sha256(bundle),
        identity=FileIdentity(
            device=metadata.st_dev,
            inode=metadata.st_ino,
            size_bytes=metadata.st_size,
            mtime_ns=metadata.st_mtime_ns,
            link_count=metadata.st_nlink,
        ),
        reader=KINGDEE_READER_ID,
        reader_version=KINGDEE_READER_VERSION,
        logical_source_period="2000-01",
        schema_id=profile.schema_id,
        schema_fingerprint=profile.schema_fingerprint,
        selection_resolution_ref=None,
    )


class KingdeeBundleTests(unittest.TestCase):
    def setUp(self) -> None:
        self.security = SecurityProfile.from_yaml(MODULE_ROOT / "config" / "security_limits.yml")
        self.money = MoneyProfile.from_yaml(MODULE_ROOT / "config" / "money_profile.yml")
        self.reader_profile = active_reader_profile()

    def _read(
        self,
        *,
        raw: Path,
        scratch: Path,
        bundle: Path,
        profile: KingdeeBundleProfile,
        reader_profiles: Optional[Mapping[str, KingdeeReaderProfile]] = None,
        selection: Optional[SourceSelection] = None,
    ):
        return read_kingdee_bundle(
            input_root=raw,
            selection=selection or _bundle_selection(raw, bundle, profile),
            bundle_profile=profile,
            member_reader_profiles=reader_profiles
            if reader_profiles is not None
            else {self.reader_profile.profile_id: self.reader_profile},
            security_profile=self.security,
            money_profile=self.money,
            private_scratch_root=scratch,
        )

    def test_all_included_entity_workbooks_are_read_and_conserved(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            base = Path(temporary)
            raw, build, scratch = base / "raw", base / "build", base / "scratch"
            raw.mkdir()
            build.mkdir()
            scratch.mkdir()
            first = build / "first.xlsx"
            second = build / "second.xlsx"
            first_rows = standard_rows()
            second_rows = standard_rows()
            second_rows[1][0] = "ENTITY-T"
            second_rows[1][5] = "V-T"
            write_tabular_xlsx(first, first_rows)
            write_tabular_xlsx(second, second_rows)
            bundle = raw / "ledger-bundle.zip"
            write_zip(bundle, (("entity-a.xlsx", first.read_bytes()), ("nested/entity-b.xlsx", second.read_bytes())))
            profile = _bundle_profile(
                bundle,
                (_member(first, "entity-a.xlsx"), _member(second, "nested/entity-b.xlsx")),
            )

            result = self._read(raw=raw, scratch=scratch, bundle=bundle, profile=profile)

            self.assertEqual(result.control.workbook_member_count, 2)
            self.assertEqual(result.control.included_member_count, 2)
            self.assertEqual(result.control.excluded_member_count, 0)
            self.assertEqual(result.control.emitted_record_count, 14)
            self.assertEqual(result.control.physical_data_row_count, 16)
            self.assertEqual(result.control.empty_row_count, 2)
            self.assertEqual(result.control.row_conservation_delta, 0)
            self.assertEqual(len({record.archive_member_ref for record in result.records}), 2)
            self.assertEqual(len({record.source_record_ref for record in result.records}), 14)
            self.assertTrue(all(record.container_source_id == _bundle_selection(raw, bundle, profile).source_id for record in result.records))
            self.assertTrue(all(record.container_sha256 == _sha256(bundle) for record in result.records))
            self.assertEqual(list(scratch.iterdir()), [])

            public = json.dumps(public_bundle_summary(result), ensure_ascii=False, sort_keys=True)
            for forbidden in ("sha256", "ledger-bundle.zip", "entity-a.xlsx", "5001", "PROJECT-S", _sha256(bundle)):
                self.assertNotIn(forbidden, public)
            self.assertIn('"included_member_count": 2', public)

    def test_included_legacy_xls_blocks_the_entire_slot(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            base = Path(temporary)
            raw, build, scratch = base / "raw", base / "build", base / "scratch"
            raw.mkdir()
            build.mkdir()
            scratch.mkdir()
            legacy = build / "legacy.xls"
            legacy.write_bytes(OLE_SIGNATURE + b"public-synthetic-legacy-workbook")
            bundle = raw / "ledger-bundle.zip"
            write_zip(bundle, (("entity-legacy.xls", legacy.read_bytes()),))
            profile = _bundle_profile(
                bundle,
                (_member(legacy, "entity-legacy.xls", reader_profile_id=None),),
            )

            with self.assertRaises(KingdeeBundleError) as caught:
                self._read(raw=raw, scratch=scratch, bundle=bundle, profile=profile, reader_profiles={})

            self.assertEqual(caught.exception.code, "UNSUPPORTED_LEGACY_XLS_SLOT")
            self.assertRegex(caught.exception.member_ref or "", r"^member_[0-9a-f]{32}$")
            self.assertNotIn("entity-legacy.xls", str(caught.exception))
            self.assertEqual(list(scratch.iterdir()), [])

    def test_evidence_qualified_legacy_exclusion_does_not_hide_included_xlsx(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            base = Path(temporary)
            raw, build, scratch = base / "raw", base / "build", base / "scratch"
            raw.mkdir()
            build.mkdir()
            scratch.mkdir()
            ledger = build / "ledger.xlsx"
            legacy = build / "legacy.xls"
            write_tabular_xlsx(ledger, standard_rows())
            legacy.write_bytes(OLE_SIGNATURE + b"public-synthetic-out-of-scope")
            bundle = raw / "ledger-bundle.zip"
            write_zip(bundle, (("approved.xlsx", ledger.read_bytes()), ("other-entity.xls", legacy.read_bytes())))
            profile = _bundle_profile(
                bundle,
                (
                    _member(ledger, "approved.xlsx"),
                    _member(
                        legacy,
                        "other-entity.xls",
                        disposition="EXCLUDE_QUALIFIED_SCOPE",
                        reader_profile_id=None,
                    ),
                ),
            )

            result = self._read(raw=raw, scratch=scratch, bundle=bundle, profile=profile)

            self.assertEqual(result.control.included_member_count, 1)
            self.assertEqual(result.control.excluded_member_count, 1)
            self.assertEqual(result.control.legacy_xls_member_count, 1)
            excluded = [item for item in result.members if item.disposition == "EXCLUDE_QUALIFIED_SCOPE"]
            self.assertEqual(len(excluded), 1)
            self.assertEqual(excluded[0].security_status, "LEGACY_XLS_SIGNATURE_ONLY_EXCLUDED_BY_EVIDENCE")
            self.assertEqual(result.control.emitted_record_count, 7)

    def test_unclassified_workbook_and_member_digest_drift_fail_closed(self) -> None:
        for case in ("inventory", "digest"):
            with self.subTest(case=case), tempfile.TemporaryDirectory() as temporary:
                base = Path(temporary)
                raw, build, scratch = base / "raw", base / "build", base / "scratch"
                raw.mkdir()
                build.mkdir()
                scratch.mkdir()
                ledger = build / "ledger.xlsx"
                other = build / "other.xlsx"
                write_tabular_xlsx(ledger, standard_rows())
                write_tabular_xlsx(other, standard_rows()[:2])
                members = [("approved.xlsx", ledger.read_bytes())]
                if case == "inventory":
                    members.append(("unclassified.xlsx", other.read_bytes()))
                bundle = raw / "ledger-bundle.zip"
                write_zip(bundle, members)
                declared_digest = "f" * 64 if case == "digest" else None
                profile = _bundle_profile(
                    bundle,
                    (_member(ledger, "approved.xlsx", member_sha256=declared_digest),),
                )

                with self.assertRaises(KingdeeBundleError) as caught:
                    self._read(raw=raw, scratch=scratch, bundle=bundle, profile=profile)

                self.assertEqual(
                    caught.exception.code,
                    "BUNDLE_MEMBER_INVENTORY_DRIFT" if case == "inventory" else "BUNDLE_MEMBER_DIGEST_DRIFT",
                )
                self.assertEqual(list(scratch.iterdir()), [])

    def test_unsupported_spreadsheet_member_is_not_silently_treated_as_an_attachment(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            base = Path(temporary)
            raw, build, scratch = base / "raw", base / "build", base / "scratch"
            raw.mkdir()
            build.mkdir()
            scratch.mkdir()
            ledger = build / "ledger.xlsx"
            write_tabular_xlsx(ledger, standard_rows())
            bundle = raw / "ledger-bundle.zip"
            write_zip(bundle, (("approved.xlsx", ledger.read_bytes()), ("unlocked.xlsb", b"synthetic")))
            profile = _bundle_profile(bundle, (_member(ledger, "approved.xlsx"),))

            with self.assertRaises(KingdeeBundleError) as caught:
                self._read(raw=raw, scratch=scratch, bundle=bundle, profile=profile)

            self.assertEqual(caught.exception.code, "BUNDLE_UNSUPPORTED_SPREADSHEET_MEMBER")
            self.assertNotIn("unlocked.xlsb", str(caught.exception))
            self.assertEqual(list(scratch.iterdir()), [])

    def test_formula_in_any_xlsx_member_blocks_before_business_parse(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            base = Path(temporary)
            raw, build, scratch = base / "raw", base / "build", base / "scratch"
            raw.mkdir()
            build.mkdir()
            scratch.mkdir()
            formula = build / "formula.xlsx"
            write_xlsx(formula, formula="1+1")
            bundle = raw / "ledger-bundle.zip"
            write_zip(bundle, (("formula.xlsx", formula.read_bytes()),))
            profile = _bundle_profile(bundle, (_member(formula, "formula.xlsx"),))

            with self.assertRaises(KingdeeBundleError) as caught:
                self._read(raw=raw, scratch=scratch, bundle=bundle, profile=profile)

            self.assertEqual(caught.exception.code, "OOXML_BLOCKED")
            self.assertRegex(caught.exception.member_ref or "", r"^member_[0-9a-f]{32}$")
            self.assertNotIn("formula.xlsx", str(caught.exception))
            self.assertEqual(list(scratch.iterdir()), [])

    def test_scratch_exclusivity_and_selected_identity_are_non_waivable(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            base = Path(temporary)
            raw, build, scratch = base / "raw", base / "build", base / "scratch"
            raw.mkdir()
            build.mkdir()
            scratch.mkdir()
            ledger = build / "ledger.xlsx"
            write_tabular_xlsx(ledger, standard_rows())
            bundle = raw / "ledger-bundle.zip"
            write_zip(bundle, (("approved.xlsx", ledger.read_bytes()),))
            profile = _bundle_profile(bundle, (_member(ledger, "approved.xlsx"),))
            selection = _bundle_selection(raw, bundle, profile)

            (scratch / "occupied").write_text("public synthetic marker", encoding="utf-8")
            with self.assertRaises(KingdeeBundleError) as caught:
                self._read(raw=raw, scratch=scratch, bundle=bundle, profile=profile, selection=selection)
            self.assertEqual(caught.exception.code, "BUNDLE_SCRATCH_NOT_EMPTY")
            (scratch / "occupied").unlink()

            os.utime(bundle, ns=(selection.identity.mtime_ns + 1, selection.identity.mtime_ns + 1))
            with self.assertRaises(KingdeeBundleError) as caught:
                self._read(raw=raw, scratch=scratch, bundle=bundle, profile=profile, selection=selection)
            self.assertEqual(caught.exception.code, "BUNDLE_SELECTION_IDENTITY_DRIFT")

            overlapping = raw / "scratch"
            overlapping.mkdir()
            fresh_selection = _bundle_selection(raw, bundle, profile)
            with self.assertRaises(KingdeeBundleError) as caught:
                self._read(raw=raw, scratch=overlapping, bundle=bundle, profile=profile, selection=fresh_selection)
            self.assertEqual(caught.exception.code, "BUNDLE_SCRATCH_OVERLAP")


if __name__ == "__main__":
    unittest.main()
