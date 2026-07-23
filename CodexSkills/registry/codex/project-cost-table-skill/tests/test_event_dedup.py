import json
import unittest

from project_cost_table.dedup import (
    DedupDisposition,
    DedupError,
    DuplicateClass,
    create_business_duplicate_resolution,
    create_version_resolution,
    deduplicate_events,
)
from project_cost_table.events import EventDirection, LifecycleStage

from r7_helpers import EVIDENCE, INPUT_RESOLUTION, relation_event


class EventDedupTests(unittest.TestCase):
    def test_same_key_same_version_is_automatic_and_alias_does_not_change_business_fingerprint(self) -> None:
        first = relation_event("a", source_key_seed="key", digest_seed="same", document_id="DOC-SAME")
        second = relation_event(
            "b",
            source_key_seed="key",
            digest_seed="same",
            artifact_seed="another-download",
            document_id="DOC-SAME",
        )
        one = deduplicate_events([first])
        duplicate = deduplicate_events([second, first])
        dispositions = {item.disposition for item in duplicate.decisions}
        self.assertEqual(dispositions, {DedupDisposition.INCLUDED, DedupDisposition.EXCLUDED_DUPLICATE})
        self.assertIn(DuplicateClass.SAME_KEY_SAME_VERSION, {item.duplicate_class for item in duplicate.decisions})
        self.assertEqual(one.business_fingerprint, duplicate.business_fingerprint)
        self.assertEqual(duplicate.pending_count, 0)
        self.assertFalse(duplicate.formal_ready)

    def test_byte_duplicate_class_requires_same_artifact_and_same_record_version(self) -> None:
        first = relation_event("a", source_key_seed="key", digest_seed="same", artifact_seed="same-artifact")
        second = relation_event(
            "b",
            source_key_seed="key",
            digest_seed="same",
            artifact_seed="same-artifact",
            record_seed="another-row-ref",
            document_id="DOC-a",
        )
        result = deduplicate_events([first, second])
        excluded = [item for item in result.decisions if item.disposition == DedupDisposition.EXCLUDED_DUPLICATE]
        self.assertEqual(len(excluded), 1)
        self.assertEqual(excluded[0].duplicate_class, DuplicateClass.BYTE_DUPLICATE)

    def test_changed_version_blocks_until_exact_hash_bound_resolution(self) -> None:
        old = relation_event("old", source_key_seed="same-key", digest_seed="old", amount_minor=10_000)
        current = relation_event("new", source_key_seed="same-key", digest_seed="new", amount_minor=12_000)
        blocked = deduplicate_events([current, old])
        self.assertTrue(all(item.disposition == DedupDisposition.PENDING_VERSION_CONFLICT for item in blocked.decisions))
        self.assertEqual(len(blocked.review_tasks), 1)

        resolution = create_version_resolution(
            canonical_event_ref=current.relation_event_ref,
            superseded_event_refs=(old.relation_event_ref,),
            bound_source_business_key_hash=current.source_business_key_hash,
            input_resolution_ref=INPUT_RESOLUTION,
            evidence_refs=(EVIDENCE,),
        )
        resolved = deduplicate_events([old, current], version_resolutions=[resolution])
        by_ref = {item.relation_event_ref: item for item in resolved.decisions}
        self.assertEqual(by_ref[current.relation_event_ref].disposition, DedupDisposition.INCLUDED)
        self.assertEqual(by_ref[old.relation_event_ref].disposition, DedupDisposition.SUPERSEDED_VERSION)
        self.assertEqual(by_ref[old.relation_event_ref].canonical_event_ref, current.relation_event_ref)

    def test_business_content_duplicate_needs_explicit_equivalence_resolution(self) -> None:
        first = relation_event("first", source_key_seed="key-a", digest_seed="digest-a", document_id="D-1")
        second = relation_event("second", source_key_seed="key-b", digest_seed="digest-b", document_id="D-1")
        # Identity lineage differs by seed but business scope and content remain the same.
        blocked = deduplicate_events([first, second])
        self.assertTrue(all(item.disposition == DedupDisposition.PENDING_BUSINESS_DUPLICATE for item in blocked.decisions))
        resolution = create_business_duplicate_resolution(
            canonical_event_ref=first.relation_event_ref,
            duplicate_event_refs=(second.relation_event_ref,),
            bound_business_content_fingerprint=first.business_content_fingerprint,
            input_resolution_ref=INPUT_RESOLUTION,
            evidence_refs=(EVIDENCE,),
        )
        resolved = deduplicate_events([second, first], business_resolutions=[resolution])
        self.assertEqual(sum(item.disposition == DedupDisposition.INCLUDED for item in resolved.decisions), 1)
        self.assertEqual(
            sum(item.disposition == DedupDisposition.EXCLUDED_DUPLICATE for item in resolved.decisions), 1
        )

    def test_amount_date_counterparty_similarity_is_candidate_only(self) -> None:
        first = relation_event("one", amount_minor=9_999, document_id="D-ONE")
        second = relation_event("two", amount_minor=9_999, document_id="D-TWO")
        result = deduplicate_events([first, second])
        self.assertTrue(all(item.disposition == DedupDisposition.PENDING_POSSIBLE_DUPLICATE for item in result.decisions))
        self.assertTrue(all(item.resolution_ref is None for item in result.decisions))
        self.assertEqual(result.pair_decisions[0].duplicate_class, DuplicateClass.POSSIBLE_DUPLICATE)

    def test_cross_stage_events_are_distinct_and_never_deduplicated(self) -> None:
        contract = relation_event(
            "contract",
            direction=EventDirection.REVENUE,
            stage=LifecycleStage.CONTRACT_VALUE,
            source_key_seed="same-key",
            digest_seed="same-digest",
            document_id="C-1",
        )
        invoice = relation_event(
            "invoice",
            direction=EventDirection.REVENUE,
            stage=LifecycleStage.BILLED,
            source_key_seed="same-key",
            digest_seed="same-digest",
            document_id="C-1",
        )
        result = deduplicate_events([invoice, contract])
        self.assertTrue(all(item.disposition == DedupDisposition.INCLUDED for item in result.decisions))
        self.assertEqual(result.candidate_pair_count, 0)

    def test_candidate_pair_budget_is_partitioned_and_enforced(self) -> None:
        same_partition = [relation_event("event-%d" % number, amount_minor=number + 1) for number in range(3)]
        with self.assertRaises(DedupError) as caught:
            deduplicate_events(same_partition, candidate_pair_budget=2)
        self.assertEqual(caught.exception.code, "CANDIDATE_PAIR_BUDGET_EXCEEDED")

        other_project = relation_event("other", project="PROJECT-OTHER")
        result = deduplicate_events([same_partition[0], other_project], candidate_pair_budget=0)
        self.assertEqual(result.candidate_pair_count, 0)

    def test_order_and_public_summary_are_deterministic_and_redacted(self) -> None:
        events = [relation_event("z", amount_minor=1), relation_event("a", amount_minor=2)]
        first = deduplicate_events(events)
        second = deduplicate_events(list(reversed(events)))
        self.assertEqual(first.as_private_dict(), second.as_private_dict())
        public = json.dumps(first.as_public_summary(), ensure_ascii=False)
        self.assertNotIn("PROJECT-S", public)
        self.assertNotIn("DOC-", public)
        self.assertNotIn("company_approver", public.casefold())


if __name__ == "__main__":
    unittest.main()
