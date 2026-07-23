from __future__ import annotations

import tempfile
import sys
import unittest
from pathlib import Path

MODULE_ROOT = Path(__file__).resolve().parents[1]
SRC_ROOT = MODULE_ROOT / "src"
if str(SRC_ROOT) not in sys.path:
    sys.path.insert(0, str(SRC_ROOT))

from project_cost_table.source_records import (
    LayerRecord,
    RecordLayer,
    RecordLayerError,
    append_layer_record,
)


SOURCE_ID = "rec_source_record_" + "1" * 32
CANDIDATE_ID = "rec_candidate_" + "2" * 32
DECISION_ID = "rec_decision_" + "3" * 32
FACT_ID = "rec_approved_fact_" + "4" * 32


class SourceRecordLayerTests(unittest.TestCase):
    def test_four_layers_remain_separate_and_append_only(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary) / "private-run"
            records = [
                LayerRecord(
                    record_id=SOURCE_ID,
                    layer=RecordLayer.SOURCE_RECORD,
                    payload_hash="a" * 64,
                    private_payload_ref="private://source/1",
                ),
                LayerRecord(
                    record_id=CANDIDATE_ID,
                    layer=RecordLayer.CANDIDATE,
                    payload_hash="b" * 64,
                    private_payload_ref="private://candidate/1",
                    source_refs=(SOURCE_ID,),
                ),
                LayerRecord(
                    record_id=DECISION_ID,
                    layer=RecordLayer.DECISION,
                    payload_hash="c" * 64,
                    private_payload_ref="private://decision/1",
                    candidate_refs=(CANDIDATE_ID,),
                    evidence_refs=("evidence:synthetic",),
                ),
                LayerRecord(
                    record_id=FACT_ID,
                    layer=RecordLayer.APPROVED_FACT,
                    payload_hash="d" * 64,
                    private_payload_ref="private://fact/1",
                    source_refs=(SOURCE_ID,),
                    decision_refs=(DECISION_ID,),
                    evidence_refs=("evidence:synthetic",),
                ),
            ]
            paths = [append_layer_record(root, record) for record in records]
            self.assertEqual({path.parent.name for path in paths}, {layer.value.lower() for layer in RecordLayer})
            self.assertTrue(all("approval" not in path.read_text(encoding="utf-8").lower() for path in paths))
            with self.assertRaises(RecordLayerError) as caught:
                append_layer_record(root, records[0])
            self.assertEqual(caught.exception.code, "OUTPUT_EXISTS")

    def test_candidate_and_validated_fact_cannot_skip_lineage(self) -> None:
        invalid = [
            LayerRecord(
                record_id=CANDIDATE_ID,
                layer=RecordLayer.CANDIDATE,
                payload_hash="b" * 64,
                private_payload_ref="private://candidate/1",
            ),
            LayerRecord(
                record_id=FACT_ID,
                layer=RecordLayer.APPROVED_FACT,
                payload_hash="d" * 64,
                private_payload_ref="private://fact/1",
                source_refs=(SOURCE_ID,),
            ),
        ]
        expected = ["CANDIDATE_LINEAGE_INVALID", "FACT_LINEAGE_INVALID"]
        for record, code in zip(invalid, expected):
            with self.subTest(code=code):
                with self.assertRaises(RecordLayerError) as caught:
                    record.validate()
                self.assertEqual(caught.exception.code, code)

    def test_supersession_creates_a_new_record_instead_of_overwrite(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary) / "private-run"
            first = LayerRecord(
                record_id=SOURCE_ID,
                layer=RecordLayer.SOURCE_RECORD,
                payload_hash="a" * 64,
                private_payload_ref="private://source/1",
            )
            second = LayerRecord(
                record_id="rec_source_record_" + "5" * 32,
                layer=RecordLayer.SOURCE_RECORD,
                payload_hash="e" * 64,
                private_payload_ref="private://source/2",
                supersedes_ref=SOURCE_ID,
            )
            first_path = append_layer_record(root, first)
            second_path = append_layer_record(root, second)
            self.assertTrue(first_path.exists())
            self.assertTrue(second_path.exists())
            self.assertNotEqual(first_path, second_path)


if __name__ == "__main__":
    unittest.main()
