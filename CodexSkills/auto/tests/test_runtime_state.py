from __future__ import annotations

import os
import tempfile
import unittest
from pathlib import Path

from CodexSkills.auto.runtime.core import AutoRuntimeError, atomic_write_bytes, read_json
from CodexSkills.auto.runtime.roots import RootEntry, RootRegistry, prepare_state_root
from CodexSkills.auto.runtime.state import (
    RemoteSettlementEvidence,
    SingleFlightLock,
    StateLayout,
    WatermarkStore,
)

from runtime_helpers import CANDIDATE_DIGEST, REPO_ROOT, clock, context, uid


class RuntimeStateTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temporary = tempfile.TemporaryDirectory()
        self.base = Path(self.temporary.name)
        self.source = self.base / "source"
        self.source.mkdir()
        self.state = self.base / "state"

    def tearDown(self) -> None:
        self.temporary.cleanup()

    def layout(self):
        root = prepare_state_root(self.state, repo_root=REPO_ROOT, protected_roots=[self.source])
        return StateLayout.create(root)

    def test_state_root_must_be_repo_external(self) -> None:
        with self.assertRaisesRegex(AutoRuntimeError, "STATE_ROOT_REPOSITORY_OVERLAP"):
            prepare_state_root(
                REPO_ROOT / "CodexSkills" / "forbidden-state",
                repo_root=REPO_ROOT,
                protected_roots=[self.source],
            )
        self.assertFalse((REPO_ROOT / "CodexSkills" / "forbidden-state").exists())

    def test_existing_state_root_permissions_fail_closed(self) -> None:
        self.state.mkdir(mode=0o700)
        os.chmod(self.state, 0o755)
        with self.assertRaisesRegex(AutoRuntimeError, "STATE_ROOT_PERMISSIONS_TOO_BROAD"):
            prepare_state_root(self.state, repo_root=REPO_ROOT, protected_roots=[self.source])

    def test_atomic_failure_leaves_previous_valid_value(self) -> None:
        layout = self.layout()
        target = layout.watermarks / "state.json"
        atomic_write_bytes(target, b'{"version":1}')

        def crash(stage):
            if stage == "AFTER_FILE_FSYNC":
                raise RuntimeError("synthetic crash")

        with self.assertRaisesRegex(RuntimeError, "synthetic crash"):
            atomic_write_bytes(target, b'{"version":2}', failpoint=crash)
        self.assertEqual(read_json(target), {"version": 1})

    def test_atomic_writer_rejects_symlink_target(self) -> None:
        layout = self.layout()
        real = layout.watermarks / "real.json"
        real.write_bytes(b"{}")
        linked = layout.watermarks / "linked.json"
        linked.symlink_to(real.name)
        with self.assertRaisesRegex(AutoRuntimeError, "ATOMIC_TARGET_NOT_REGULAR"):
            atomic_write_bytes(linked, b"{}")

    def test_protected_root_mutation_is_denied_without_prefix_confusion(self) -> None:
        layout = self.layout()
        sibling = self.base / "source-copy"
        sibling.mkdir()
        registry = RootRegistry(
            (
                RootEntry("source", "SKILL_SOURCE", self.source),
                RootEntry("state", "STATE", layout.root),
                RootEntry("sibling", "STAGING", sibling),
            )
        )
        with self.assertRaisesRegex(AutoRuntimeError, "PROTECTED_ROOT_MUTATION_FORBIDDEN"):
            registry.assert_mutation("DELETE", self.source / "x")
        self.assertEqual(registry.assert_mutation("WRITE", sibling / "x").root_ref, "sibling")

    def test_two_starts_produce_one_writer(self) -> None:
        layout = self.layout()
        first = SingleFlightLock(layout, context().contract, CANDIDATE_DIGEST, clock())
        acquired = first.acquire(uid("run", 1), entropy=(1).to_bytes(10, "big"))
        self.assertEqual(acquired.status, "ACQUIRED")
        second = SingleFlightLock(layout, context().contract, CANDIDATE_DIGEST, clock())
        busy = second.acquire(uid("run", 2), entropy=(2).to_bytes(10, "big"))
        self.assertEqual(busy.status, "BUSY")

    def test_expired_lock_is_not_stolen_without_owner_probe(self) -> None:
        layout = self.layout()
        fake = clock()
        lock = SingleFlightLock(layout, context().contract, CANDIDATE_DIGEST, fake)
        acquired = lock.acquire(uid("run", 1), lease_seconds=1, entropy=(1).to_bytes(10, "big"))
        fake.advance(seconds=2)
        stale = lock.acquire(uid("run", 2), entropy=(2).to_bytes(10, "big"))
        self.assertEqual(stale.status, "STALE_REQUIRES_RECONCILIATION")
        with self.assertRaisesRegex(AutoRuntimeError, "LOCK_OWNER_STILL_ACTIVE"):
            lock.recover_stale(str(acquired.state["state_digest"]), lambda _run: True)
        generation = lock.recover_stale(str(acquired.state["state_digest"]), lambda _run: False)
        self.assertEqual(generation, 2)
        recovered = lock.acquire(uid("run", 2), generation=generation, entropy=(2).to_bytes(10, "big"))
        self.assertEqual(recovered.status, "ACQUIRED")

    def test_lock_release_requires_exact_owner_and_digest(self) -> None:
        layout = self.layout()
        lock = SingleFlightLock(layout, context().contract, CANDIDATE_DIGEST, clock())
        acquired = lock.acquire(uid("run", 1), entropy=(1).to_bytes(10, "big"))
        with self.assertRaisesRegex(AutoRuntimeError, "LOCK_OWNERSHIP_MISMATCH"):
            lock.release(uid("run", 2), str(acquired.state["state_digest"]))
        released = lock.release(uid("run", 1), str(acquired.state["state_digest"]))
        self.assertEqual(released["status"], "RELEASED")
        self.assertFalse(lock.claim.exists())

    def test_partial_corrupt_claim_needs_grace_and_explicit_proof(self) -> None:
        layout = self.layout()
        fake = clock()
        lock = SingleFlightLock(layout, context().contract, CANDIDATE_DIGEST, fake)
        lock.claim.mkdir(mode=0o700)
        os.utime(lock.claim, (fake.now().timestamp(), fake.now().timestamp()))
        evidence = lock.corrupt_claim_evidence()
        with self.assertRaisesRegex(AutoRuntimeError, "LOCK_CORRUPT_RECOVERY_GRACE_REQUIRED"):
            lock.recover_corrupt(
                str(evidence["claim_fingerprint"]),
                lambda _evidence: True,
            )
        fake.advance(seconds=121)
        refreshed = lock.corrupt_claim_evidence()
        with self.assertRaisesRegex(AutoRuntimeError, "LOCK_CORRUPT_RECOVERY_NOT_AUTHORIZED"):
            lock.recover_corrupt(
                str(refreshed["claim_fingerprint"]),
                lambda _evidence: False,
            )
        lock.recover_corrupt(
            str(refreshed["claim_fingerprint"]),
            lambda _evidence: True,
        )
        self.assertFalse(lock.claim.exists())

    def test_watermark_never_advances_without_remote_readback(self) -> None:
        layout = self.layout()
        store = WatermarkStore(
            layout.watermarks / "watermark.json",
            context().contract,
            CANDIDATE_DIGEST,
            clock(),
        )
        initial = store.initialize(
            {"REGISTRY": uid("gen", 1), "RUN_LOG": uid("gen", 2)},
            {"REGISTRY": "registry-zero", "RUN_LOG": "run-zero"},
            entropy=(3).to_bytes(10, "big"),
        )
        before = initial["state_digest"]
        evidence = RemoteSettlementEvidence(
            "REGISTRY", "1" * 64, "sha1:" + "2" * 40, False
        )
        with self.assertRaisesRegex(AutoRuntimeError, "WATERMARK_REMOTE_READBACK_REQUIRED"):
            store.settle(evidence, "registry-one")
        self.assertEqual(store.read()["state_digest"], before)

    def test_lane_settlement_updates_only_verified_lane(self) -> None:
        layout = self.layout()
        store = WatermarkStore(
            layout.watermarks / "watermark.json",
            context().contract,
            CANDIDATE_DIGEST,
            clock(),
        )
        store.initialize(
            {"REGISTRY": uid("gen", 1), "RUN_LOG": uid("gen", 2)},
            {"REGISTRY": "registry-zero", "RUN_LOG": "run-zero"},
            entropy=(3).to_bytes(10, "big"),
        )
        settled = store.settle(
            RemoteSettlementEvidence(
                "RUN_LOG", "1" * 64, "sha1:" + "2" * 40, True
            ),
            "run-one",
        )
        lanes = {item["lane"]: item for item in settled["lane_states"]}
        self.assertEqual(lanes["REGISTRY"]["cursor_token"], "registry-zero")
        self.assertEqual(lanes["RUN_LOG"]["cursor_token"], "run-one")


if __name__ == "__main__":
    unittest.main()
