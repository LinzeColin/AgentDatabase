import stat
import sys
import tempfile
import unittest
import zipfile
from dataclasses import replace
from pathlib import Path
from unittest import mock


MODULE_ROOT = Path(__file__).resolve().parents[1]
SRC_ROOT = MODULE_ROOT / "src"
if str(SRC_ROOT) not in sys.path:
    sys.path.insert(0, str(SRC_ROOT))

from project_cost_table.security import (  # noqa: E402
    FileSecurityError,
    SecurityProfile,
    SecurityProfileError,
    preflight_zip,
)
import project_cost_table.security as security_module  # noqa: E402
from synthetic_builders import (  # noqa: E402
    corrupt_stored_member_payload,
    mark_first_member_encrypted,
    write_special_member_zip,
    write_zip,
)


PROFILE = SecurityProfile.from_yaml(MODULE_ROOT / "config" / "security_limits.yml")


class ArchiveSecurityTests(unittest.TestCase):
    def test_security_profile_rejects_type_coercion_and_policy_relaxation(self) -> None:
        base = {
            "schema_version": "kmfa.project_cost.security_limits.v1",
            "profile_id": "TEST",
            "source_file_bytes_max": 100,
            "archive_member_count_max": 10,
            "archive_total_uncompressed_bytes_max": 100,
            "archive_single_member_bytes_max": 50,
            "archive_compression_ratio_max": 10,
            "archive_nested_depth_max": 2,
            "xml_single_part_bytes_max": 50,
            "allowed_zip_compression_methods": [0, 8],
            "legacy_xls_policy": "BLOCK_UNTIL_LOCKED_READER",
            "macro_enabled_ooxml_policy": "BLOCK",
            "formula_cell_policy": "BLOCK_UNTIL_GOVERNED_CACHED_VALUE_READER",
            "external_relationship_policy": "BLOCK",
        }
        SecurityProfile.from_mapping(base)
        for invalid in (
            dict(base, archive_member_count_max=True),
            dict(base, archive_nested_depth_max=2.0),
            dict(base, allowed_zip_compression_methods=[False, 8]),
            dict(base, external_relationship_policy="ALLOW"),
        ):
            with self.subTest(invalid=invalid):
                with self.assertRaises(SecurityProfileError):
                    SecurityProfile.from_mapping(invalid)

    def test_normal_archive_passes_crc_and_counts_nested_candidates(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            archive = root / "safe.zip"
            write_zip(archive, (("nested/data.txt", b"safe"),))
            report = preflight_zip(root, archive, profile=PROFILE)
            self.assertEqual(report.member_count, 1)
            self.assertEqual(report.nested_archive_candidate_count, 0)
            self.assertEqual(report.recursive_member_count, 1)
            self.assertTrue(report.crc_verified)
            self.assertEqual(len(report.sha256), 64)

    def test_nested_archive_requires_private_scratch_and_is_recursively_verified(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            inner = root / "inner.zip"
            outer = root / "outer.zip"
            scratch = root / "private-scratch"
            scratch.mkdir()
            write_zip(inner, (("data.txt", b"safe"),))
            write_zip(outer, (("nested/inner.zip", inner.read_bytes()),))
            with self.assertRaises(FileSecurityError) as missing_scratch:
                preflight_zip(root, outer, profile=PROFILE)
            self.assertEqual(missing_scratch.exception.code, "NESTED_ARCHIVE_SCRATCH_REQUIRED")
            report = preflight_zip(root, outer, profile=PROFILE, scratch_root=scratch)
            self.assertEqual(report.nested_archive_candidate_count, 1)
            self.assertEqual(report.recursive_member_count, 2)
            self.assertEqual(list(scratch.iterdir()), [])

    def test_nested_signature_depth_recursive_count_and_macro_gates(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            scratch = root / "private-scratch"
            scratch.mkdir()
            bad_signature = root / "bad-signature.zip"
            write_zip(bad_signature, (("book.xlsx", b"opaque"),))
            with self.assertRaises(FileSecurityError) as signature:
                preflight_zip(root, bad_signature, profile=PROFILE, scratch_root=scratch)
            self.assertEqual(signature.exception.code, "NESTED_ARCHIVE_SIGNATURE")
            self.assertEqual(list(scratch.iterdir()), [])

            macro = root / "macro.zip"
            write_zip(macro, (("book.xlsm", b"opaque"),))
            with self.assertRaises(FileSecurityError) as macro_error:
                preflight_zip(root, macro, profile=PROFILE, scratch_root=scratch)
            self.assertEqual(macro_error.exception.code, "NESTED_MACRO_ENABLED_OOXML")

            leaf = root / "leaf.zip"
            middle = root / "middle.zip"
            outer = root / "outer.zip"
            write_zip(leaf, (("data.txt", b"safe"),))
            write_zip(middle, (("leaf.zip", leaf.read_bytes()),))
            write_zip(outer, (("middle.zip", middle.read_bytes()),))
            shallow = replace(PROFILE, archive_nested_depth_max=1)
            with self.assertRaises(FileSecurityError) as depth:
                preflight_zip(root, outer, profile=shallow, scratch_root=scratch)
            self.assertEqual(depth.exception.code, "ARCHIVE_NESTING_DEPTH")

            inner_many = root / "inner-many.zip"
            outer_many = root / "outer-many.zip"
            write_zip(inner_many, (("a", b"1"), ("b", b"2")))
            write_zip(outer_many, (("inner.zip", inner_many.read_bytes()),))
            count_limited = replace(PROFILE, archive_member_count_max=2)
            with self.assertRaises(FileSecurityError) as count:
                preflight_zip(root, outer_many, profile=count_limited, scratch_root=scratch)
            self.assertEqual(count.exception.code, "ARCHIVE_RECURSIVE_MEMBER_LIMIT")

    def test_nested_scratch_must_exist_and_not_be_symlink(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            archive = root / "outer.zip"
            write_zip(archive, (("data.txt", b"safe"),))
            missing = root / "missing"
            with self.assertRaises(FileSecurityError) as absent:
                preflight_zip(root, archive, profile=PROFILE, scratch_root=missing)
            self.assertEqual(absent.exception.code, "UNSAFE_PRIVATE_SCRATCH")
            real = root / "real"
            link = root / "link"
            real.mkdir()
            try:
                link.symlink_to(real, target_is_directory=True)
            except OSError:
                self.skipTest("symlink creation is unavailable")
            with self.assertRaises(FileSecurityError) as linked:
                preflight_zip(root, archive, profile=PROFILE, scratch_root=link)
            self.assertEqual(linked.exception.code, "UNSAFE_PRIVATE_SCRATCH")

    def test_source_change_during_preflight_is_blocked(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            archive_path = root / "changing.zip"
            write_zip(archive_path, (("data.txt", b"safe"),))
            original = security_module._inspect_open_archive

            def inspect_then_mutate(archive, **kwargs):
                result = original(archive, **kwargs)
                with Path(archive.filename).open("ab") as handle:
                    handle.write(b"changed")
                return result

            with mock.patch.object(security_module, "_inspect_open_archive", side_effect=inspect_then_mutate):
                with self.assertRaises(FileSecurityError) as caught:
                    preflight_zip(root, archive_path, profile=PROFILE)
            self.assertEqual(caught.exception.code, "SOURCE_CHANGED_DURING_PREFLIGHT")

    def test_absolute_parent_backslash_drive_and_unc_paths_fail(self) -> None:
        cases = ("/absolute.txt", "../escape.txt", "dir/../escape.txt", "dir\\escape.txt", "C:/drive.txt", "//server/share.txt")
        for member in cases:
            with self.subTest(member=member), tempfile.TemporaryDirectory() as temporary:
                root = Path(temporary)
                archive = root / "bad.zip"
                write_zip(archive, ((member, b"unsafe"),))
                with self.assertRaises(FileSecurityError):
                    preflight_zip(root, archive, profile=PROFILE)

    def test_public_error_serialization_redacts_member_name_by_default(self) -> None:
        error = FileSecurityError("SYNTHETIC", "blocked", member="private-name.txt")
        public = error.as_dict()
        private = error.as_dict(include_sensitive=True)
        self.assertNotIn("member", public)
        self.assertEqual(len(public["member_ref"]), 16)
        self.assertEqual(private["member"], "private-name.txt")

    def test_case_and_unicode_normalized_duplicate_targets_fail(self) -> None:
        cases = (
            (("A.txt", b"a"), ("a.txt", b"b")),
            (("caf\u00e9.txt", b"a"), ("cafe\u0301.txt", b"b")),
        )
        for members in cases:
            with self.subTest(names=[item[0] for item in members]), tempfile.TemporaryDirectory() as temporary:
                root = Path(temporary)
                archive = root / "duplicate.zip"
                write_zip(archive, members)
                with self.assertRaises(FileSecurityError) as caught:
                    preflight_zip(root, archive, profile=PROFILE)
                self.assertEqual(caught.exception.code, "DUPLICATE_ARCHIVE_TARGET")

    def test_symlink_and_special_device_members_fail(self) -> None:
        for file_type, expected in ((stat.S_IFLNK, "SYMLINK_ARCHIVE_MEMBER"), (stat.S_IFIFO, "SPECIAL_ARCHIVE_MEMBER")):
            with self.subTest(file_type=file_type), tempfile.TemporaryDirectory() as temporary:
                root = Path(temporary)
                archive = root / "special.zip"
                write_special_member_zip(archive, "special", file_type)
                with self.assertRaises(FileSecurityError) as caught:
                    preflight_zip(root, archive, profile=PROFILE)
                self.assertEqual(caught.exception.code, expected)

    def test_encrypted_member_flag_fails_before_read(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            archive = root / "encrypted.zip"
            write_zip(archive, (("data.txt", b"safe"),))
            mark_first_member_encrypted(archive)
            with self.assertRaises(FileSecurityError) as caught:
                preflight_zip(root, archive, profile=PROFILE)
            self.assertEqual(caught.exception.code, "ENCRYPTED_ARCHIVE_MEMBER")

    def test_crc_corruption_fails(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            archive = root / "corrupt.zip"
            marker = b"CRC_TARGET_UNIQUE"
            write_zip(archive, (("data.txt", marker),))
            corrupt_stored_member_payload(archive, marker)
            with self.assertRaises(FileSecurityError) as caught:
                preflight_zip(root, archive, profile=PROFILE)
            self.assertIn(caught.exception.code, {"ARCHIVE_CRC_FAILURE", "INVALID_ARCHIVE"})

    def test_compression_ratio_bomb_fails(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            archive = root / "bomb.zip"
            write_zip(archive, (("zeros.bin", b"0" * 50000),), compression=zipfile.ZIP_DEFLATED)
            strict = replace(PROFILE, archive_compression_ratio_max=2)
            with self.assertRaises(FileSecurityError) as caught:
                preflight_zip(root, archive, profile=strict)
            self.assertEqual(caught.exception.code, "ARCHIVE_COMPRESSION_RATIO")

    def test_member_count_single_and_total_size_limits_fail(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            archive = root / "limits.zip"
            write_zip(archive, (("a", b"12"), ("b", b"34")))
            cases = (
                (replace(PROFILE, archive_member_count_max=1), "ARCHIVE_MEMBER_LIMIT"),
                (replace(PROFILE, archive_single_member_bytes_max=1), "ARCHIVE_MEMBER_SIZE_LIMIT"),
                (replace(PROFILE, archive_total_uncompressed_bytes_max=3), "ARCHIVE_TOTAL_SIZE_LIMIT"),
            )
            for profile, expected in cases:
                with self.subTest(expected=expected):
                    with self.assertRaises(FileSecurityError) as caught:
                        preflight_zip(root, archive, profile=profile)
                    self.assertEqual(caught.exception.code, expected)

    def test_unsupported_compression_fails(self) -> None:
        if not hasattr(zipfile, "ZIP_BZIP2"):
            self.skipTest("BZIP2 ZIP support unavailable")
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            archive = root / "unsupported.zip"
            write_zip(archive, (("data.txt", b"safe"),), compression=zipfile.ZIP_BZIP2)
            with self.assertRaises(FileSecurityError) as caught:
                preflight_zip(root, archive, profile=PROFILE)
            self.assertEqual(caught.exception.code, "UNSUPPORTED_COMPRESSION")

    def test_non_zip_signature_and_malformed_zip_fail(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            plain = root / "plain.zip"
            plain.write_bytes(b"not-a-zip")
            with self.assertRaises(FileSecurityError) as mismatch:
                preflight_zip(root, plain, profile=PROFILE)
            self.assertEqual(mismatch.exception.code, "TYPE_SIGNATURE_MISMATCH")
            malformed = root / "malformed.zip"
            malformed.write_bytes(b"PK\x03\x04truncated")
            with self.assertRaises(FileSecurityError) as invalid:
                preflight_zip(root, malformed, profile=PROFILE)
            self.assertEqual(invalid.exception.code, "INVALID_ARCHIVE")


if __name__ == "__main__":
    unittest.main()
