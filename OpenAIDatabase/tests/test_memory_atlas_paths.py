from __future__ import annotations

import sys
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = ROOT / "scripts"
if str(SCRIPTS) not in sys.path:
    sys.path.insert(0, str(SCRIPTS))

from memory_atlas_paths import (  # noqa: E402
    frontend_relative_to_database,
    resolve_frontend_root,
)


class MemoryAtlasPathsTests(unittest.TestCase):
    def test_split_top_level_frontend_is_canonical(self) -> None:
        frontend = resolve_frontend_root(ROOT)

        self.assertEqual(frontend, ROOT.parent / "MemoryAtlas")
        self.assertEqual(frontend_relative_to_database(ROOT, frontend), "../MemoryAtlas")

    def test_legacy_fixture_layout_remains_a_compatibility_fallback(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            database = Path(temporary) / "OpenAIDatabase"
            frontend = database / "apps/memory-atlas"
            (frontend / "src").mkdir(parents=True)
            (frontend / "package.json").write_text("{}\n", encoding="utf-8")

            resolved = resolve_frontend_root(database)

        self.assertEqual(resolved, frontend.resolve())
        self.assertEqual(frontend_relative_to_database(database.resolve(), resolved), "apps/memory-atlas")


if __name__ == "__main__":
    unittest.main()
