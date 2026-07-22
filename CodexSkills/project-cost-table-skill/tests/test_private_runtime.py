import tempfile
import sys
import unittest
from pathlib import Path


MODULE_ROOT = Path(__file__).resolve().parents[1]
SRC_ROOT = MODULE_ROOT / "src"
if str(SRC_ROOT) not in sys.path:
    sys.path.insert(0, str(SRC_ROOT))

from project_cost_table.private_runtime import RUNTIME_DIRECTORIES, ensure_private_runtime


class PrivateRuntimeTests(unittest.TestCase):
    def test_initializer_creates_only_expected_empty_directories(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            module_root = Path(temporary) / "skill"
            created = ensure_private_runtime(module_root)
            self.assertEqual(tuple(path.name for path in created), RUNTIME_DIRECTORIES)
            self.assertTrue(all(path.is_dir() for path in created))
            self.assertFalse(any(path.is_file() for path in (module_root / "private_runtime").rglob("*")))

    def test_initializer_is_idempotent(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            module_root = Path(temporary) / "skill"
            self.assertEqual(ensure_private_runtime(module_root), ensure_private_runtime(module_root))

    def test_initializer_rejects_symlinked_runtime(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            module_root = Path(temporary) / "skill"
            external = Path(temporary) / "external"
            module_root.mkdir()
            external.mkdir()
            try:
                (module_root / "private_runtime").symlink_to(external, target_is_directory=True)
            except OSError:
                self.skipTest("symlink creation is not permitted")
            with self.assertRaisesRegex(RuntimeError, "symbolic link"):
                ensure_private_runtime(module_root)


if __name__ == "__main__":
    unittest.main()
