from __future__ import annotations

import json
import os
import sys
import tempfile
import unicodedata
import unittest
from dataclasses import replace
from pathlib import Path
from unittest import mock

MODULE_ROOT = Path(__file__).resolve().parents[1]
SRC_ROOT = MODULE_ROOT / "src"
if str(SRC_ROOT) not in sys.path:
    sys.path.insert(0, str(SRC_ROOT))

from project_cost_table.inventory import (
    InventoryError,
    build_private_full_inventory,
    private_inventory_payload,
    public_inventory_summary,
    scan_inventory_metadata,
    source_id_for_relative_path,
    verify_source_file,
)
from r3_helpers import write_source


class InventoryTests(unittest.TestCase):
    def test_metadata_scan_never_opens_source_body(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            write_source(root, "nested/source.dat", b"body-must-not-open")
            with mock.patch.object(Path, "open", side_effect=AssertionError("source body opened")):
                entries = scan_inventory_metadata(root)
            self.assertEqual(len(entries), 1)
            self.assertEqual(entries[0].status, "SAFE_METADATA")
            self.assertIsNone(entries[0].sha256)

    def test_private_full_inventory_and_public_summary_are_separate(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            write_source(root, "private-name-one.dat", b"one")
            write_source(root, "nested/private-name-two.dat", b"two")
            entries = build_private_full_inventory(root)
            private_text = json.dumps(private_inventory_payload(entries), sort_keys=True)
            public_payload = public_inventory_summary(entries)
            public_text = json.dumps(public_payload, sort_keys=True)
            self.assertIn("private-name-one.dat", private_text)
            self.assertIn("sha256", private_text)
            self.assertNotIn("private-name-one", public_text)
            self.assertNotIn("private-name-two", public_text)
            self.assertNotIn("source_id", public_text)
            self.assertNotIn("sha256", public_text)
            self.assertEqual(public_payload["verified_file_count"], 2)
            self.assertFalse(public_payload["contains_private_locators"])

    def test_hardlink_and_symlink_are_inventory_unsafe(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            original = write_source(root, "original.dat")
            hardlink = root / "hard.dat"
            try:
                os.link(str(original), str(hardlink))
            except OSError:
                self.skipTest("hardlinks are not supported")
            external = Path(temporary).parent / (root.name + "-external")
            external.write_bytes(b"external")
            symlink = root / "link.dat"
            try:
                symlink.symlink_to(external)
            except OSError:
                external.unlink(missing_ok=True)
                self.skipTest("symlinks are not supported")
            try:
                entries = scan_inventory_metadata(root)
                status_by_name = {entry.relative_path: (entry.status, entry.error_code) for entry in entries}
                self.assertEqual(status_by_name["original.dat"], ("UNSAFE", "INPUT_HARDLINK"))
                self.assertEqual(status_by_name["hard.dat"], ("UNSAFE", "INPUT_HARDLINK"))
                self.assertEqual(status_by_name["link.dat"], ("UNSAFE", "INPUT_SYMLINK"))
            finally:
                external.unlink(missing_ok=True)

    def test_formal_verification_ignores_cached_inventory_digest(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            source = write_source(root, "source.dat", b"first")
            entry = scan_inventory_metadata(root)[0]
            stale = replace(entry, sha256="0" * 64)
            source.write_bytes(b"second")
            verified = verify_source_file(root, stale)
            self.assertNotEqual(verified.sha256, stale.sha256)
            self.assertEqual(verified.sha256, __import__("hashlib").sha256(b"second").hexdigest())

    def test_source_id_normalizes_unicode_and_scan_order_is_deterministic(self) -> None:
        composed = "caf\u00e9.dat"
        decomposed = unicodedata.normalize("NFD", composed)
        self.assertEqual(source_id_for_relative_path(composed), source_id_for_relative_path(decomposed))
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            write_source(root, "z.dat")
            write_source(root, "a.dat")
            first = scan_inventory_metadata(root)
            second = scan_inventory_metadata(root)
            self.assertEqual(first, second)
            self.assertEqual([entry.relative_path for entry in first], ["a.dat", "z.dat"])

    def test_normalized_unicode_path_collision_fails_closed_when_filesystem_allows_both(self) -> None:
        composed = "caf\u00e9.dat"
        decomposed = unicodedata.normalize("NFD", composed)
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            write_source(root, composed)
            write_source(root, decomposed)
            if len(list(root.iterdir())) != 2:
                self.skipTest("filesystem normalizes Unicode filenames")
            with self.assertRaises(InventoryError) as caught:
                scan_inventory_metadata(root)
            self.assertEqual(caught.exception.code, "SOURCE_ID_COLLISION")


if __name__ == "__main__":
    unittest.main()
