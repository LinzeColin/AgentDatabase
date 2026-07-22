import os
import sys
import tempfile
import unittest
from pathlib import Path


MODULE_ROOT = Path(__file__).resolve().parents[1]
SRC_ROOT = MODULE_ROOT / "src"
if str(SRC_ROOT) not in sys.path:
    sys.path.insert(0, str(SRC_ROOT))

from project_cost_table.paths import (  # noqa: E402
    PathSafetyError,
    atomic_output_directory,
    atomic_write_bytes,
    atomic_write_with_writer,
    resolve_input_file,
)


class GovernedPathTests(unittest.TestCase):
    def test_relative_and_absolute_input_inside_root_pass(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            source = root / "source.txt"
            source.write_text("safe", encoding="utf-8")
            self.assertEqual(resolve_input_file(root, Path("source.txt")), source.resolve())
            self.assertEqual(resolve_input_file(root, source), source.resolve())

    def test_outside_traversal_and_backslash_fail(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary) / "root"
            root.mkdir()
            outside = Path(temporary) / "outside.txt"
            outside.write_text("outside", encoding="utf-8")
            cases = (outside, Path("../outside.txt"), Path("dir\\file.txt"))
            for candidate in cases:
                with self.subTest(candidate=str(candidate)):
                    with self.assertRaises(PathSafetyError):
                        resolve_input_file(root, candidate)

    def test_symlink_file_and_parent_fail(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary) / "root"
            root.mkdir()
            source = root / "source.txt"
            source.write_text("safe", encoding="utf-8")
            link = root / "link.txt"
            external = Path(temporary) / "external"
            external.mkdir()
            (external / "nested.txt").write_text("safe", encoding="utf-8")
            try:
                link.symlink_to(source)
                (root / "linked-dir").symlink_to(external, target_is_directory=True)
            except OSError:
                self.skipTest("symlink creation is unavailable")
            for candidate in (link, Path("linked-dir/nested.txt")):
                with self.subTest(candidate=str(candidate)):
                    with self.assertRaises(PathSafetyError) as caught:
                        resolve_input_file(root, candidate)
                    self.assertEqual(caught.exception.code, "INPUT_SYMLINK")

    def test_hardlink_and_fifo_fail(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            source = root / "source.txt"
            source.write_text("safe", encoding="utf-8")
            hardlink = root / "hardlink.txt"
            os.link(source, hardlink)
            with self.assertRaises(PathSafetyError) as caught:
                resolve_input_file(root, source)
            self.assertEqual(caught.exception.code, "INPUT_HARDLINK")
            fifo = root / "pipe"
            if hasattr(os, "mkfifo"):
                os.mkfifo(fifo)
                with self.assertRaises(PathSafetyError) as fifo_error:
                    resolve_input_file(root, fifo)
                self.assertEqual(fifo_error.exception.code, "INPUT_NOT_REGULAR")

    def test_size_ceiling_fails_before_reader(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            source = root / "source.txt"
            source.write_bytes(b"12345")
            with self.assertRaises(PathSafetyError) as caught:
                resolve_input_file(root, source, max_bytes=4)
            self.assertEqual(caught.exception.code, "INPUT_TOO_LARGE")


class AtomicOutputTests(unittest.TestCase):
    def test_atomic_bytes_publish_nested_target(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            target = atomic_write_bytes(root, "run/result.bin", b"final")
            self.assertEqual(target.read_bytes(), b"final")
            self.assertEqual(list(target.parent.glob(".partial-*")), [])

    def test_existing_target_is_never_overwritten(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            target = root / "result.bin"
            target.write_bytes(b"original")
            with self.assertRaises(PathSafetyError) as caught:
                atomic_write_bytes(root, "result.bin", b"replacement")
            self.assertEqual(caught.exception.code, "OUTPUT_EXISTS")
            self.assertEqual(target.read_bytes(), b"original")

    def test_writer_failure_leaves_no_final_looking_artifact(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)

            def fail(handle) -> None:
                handle.write(b"partial")
                raise RuntimeError("synthetic failure")

            with self.assertRaises(RuntimeError):
                atomic_write_with_writer(root, "result.bin", fail)
            self.assertFalse((root / "result.bin").exists())
            self.assertEqual(list(root.glob(".partial-*")), [])

    def test_publish_race_preserves_other_writer_target(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            target = root / "result.bin"

            def race(handle) -> None:
                handle.write(b"ours")
                target.write_bytes(b"other")

            with self.assertRaises(PathSafetyError) as caught:
                atomic_write_with_writer(root, "result.bin", race)
            self.assertEqual(caught.exception.code, "OUTPUT_EXISTS")
            self.assertEqual(target.read_bytes(), b"other")

    def test_atomic_directory_success_and_failure(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            with atomic_output_directory(root, "run-success") as staging:
                (staging / "artifact.txt").write_text("complete", encoding="utf-8")
                self.assertFalse((root / "run-success").exists())
            self.assertEqual((root / "run-success" / "artifact.txt").read_text(encoding="utf-8"), "complete")
            with self.assertRaises(RuntimeError):
                with atomic_output_directory(root, "run-failure") as staging:
                    (staging / "artifact.txt").write_text("partial", encoding="utf-8")
                    raise RuntimeError("synthetic failure")
            self.assertFalse((root / "run-failure").exists())
            self.assertEqual(list(root.glob(".partial-dir-*")), [])

    def test_unsafe_output_paths_fail(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            for candidate in ("../escape", "/absolute", "dir\\file", "C:/drive", "dir//file", "."):
                with self.subTest(candidate=candidate):
                    with self.assertRaises(PathSafetyError):
                        atomic_write_bytes(root, candidate, b"x")

    def test_symlinked_output_root_fails(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            base = Path(temporary)
            real = base / "real"
            link = base / "link"
            real.mkdir()
            try:
                link.symlink_to(real, target_is_directory=True)
            except OSError:
                self.skipTest("symlink creation is unavailable")
            with self.assertRaises(PathSafetyError) as caught:
                atomic_write_bytes(link, "result.bin", b"x")
            self.assertEqual(caught.exception.code, "OUTPUT_ROOT_SYMLINK")


if __name__ == "__main__":
    unittest.main()
