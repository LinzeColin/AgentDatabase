from __future__ import annotations

import sys
import unittest
from pathlib import Path

SCRIPTS = Path(__file__).resolve().parents[1] / "scripts"
sys.path.insert(0, str(SCRIPTS))

import model_registry


class ModelRegistryTests(unittest.TestCase):
    def test_resolves_current_alias(self):
        record, unknown = model_registry.resolve_model("Runway Gen-4.5")
        self.assertIsNone(unknown)
        self.assertEqual(record.model_id, "runway_gen45")
        self.assertEqual(record.status, "ACTIVE_OFFICIAL")

    def test_resolves_chinese_alias(self):
        record, unknown = model_registry.resolve_model("海螺 2.3")
        self.assertIsNone(unknown)
        self.assertEqual(record.model_id, "hailuo_23")

    def test_unknown_label_is_not_guessed(self):
        record, unknown = model_registry.resolve_model("Wan 2.7 Ultra Vendor Edition")
        self.assertIsNone(record)
        self.assertEqual(unknown, "Wan 2.7 Ultra Vendor Edition")

    def test_sora_is_non_default(self):
        record, _ = model_registry.resolve_model("Sora 2")
        self.assertEqual(record.status, "RETIRED_NON_DEFAULT")

    def test_registry_has_adapter_paths(self):
        for record in model_registry.MODEL_REGISTRY.values():
            self.assertTrue(record.adapter_path.startswith("references/models/"))
            self.assertTrue(record.verified_on)


if __name__ == "__main__":
    unittest.main()
