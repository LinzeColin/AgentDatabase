from __future__ import annotations

import hashlib
from typing import Optional, Tuple

from project_cost_table.events import (
    EventDirection,
    EventIdentityBinding,
    LifecycleStage,
    RelationEvent,
    RelationIdentityStatus,
    SourceEventStatus,
    create_relation_event,
    relation_event_id_for_source,
)


EVIDENCE = "evidence://sha256/" + "7" * 64
EVIDENCE_B = "evidence://sha256/" + "8" * 64
INPUT_RESOLUTION = "resolution_" + "7" * 32


def hex_digest(seed: str) -> str:
    return hashlib.sha256(seed.encode("utf-8")).hexdigest()


def opaque(prefix: str, seed: str) -> str:
    return prefix + hex_digest(seed)[:32]


def relation_event(
    seed: str,
    *,
    direction: EventDirection = EventDirection.COST,
    stage: LifecycleStage = LifecycleStage.POSTED_ACTUAL,
    amount_minor: int = 10_000,
    source_key_seed: Optional[str] = None,
    digest_seed: Optional[str] = None,
    artifact_seed: Optional[str] = None,
    record_seed: Optional[str] = None,
    event_type: str = "SYNTHETIC_EVENT",
    event_status: SourceEventStatus = SourceEventStatus.SOURCE_ACTIVE,
    event_date: str = "2000-01-10",
    project: str = "PROJECT-S",
    wbs: str = "WBS-S",
    contract: str = "CONTRACT-S",
    entity: str = "ENTITY-S",
    counterparty: Optional[str] = "COUNTERPARTY-S",
    document_id: Optional[str] = None,
    document_line_id: Optional[str] = "1",
    identity_status: RelationIdentityStatus = RelationIdentityStatus.VALIDATED_IDENTITY,
    reversal_of_event_id: Optional[str] = None,
    relation_keys: Tuple[str, ...] = (),
) -> RelationEvent:
    source_key = opaque("event_line_", source_key_seed or seed)
    source_digest = hex_digest(digest_seed or ("digest:" + seed))
    artifact = hex_digest(artifact_seed or ("artifact:" + seed))
    source_refs = (opaque("rec_source_", record_seed or seed),)
    economic_event_id = relation_event_id_for_source(
        source_system_id="synthetic.r7",
        source_artifact_sha256=artifact,
        source_business_key_hash=source_key,
        source_business_digest=source_digest,
        event_type=event_type,
        direction=direction,
        lifecycle_stage=stage,
        base_amount_minor=amount_minor,
        source_record_refs=source_refs,
    )
    binding = EventIdentityBinding(
        economic_event_id=economic_event_id,
        identity_status=identity_status,
        legal_entity_id=entity,
        canonical_project_id=project if identity_status == RelationIdentityStatus.VALIDATED_IDENTITY else None,
        wbs_or_cost_code=wbs if identity_status == RelationIdentityStatus.VALIDATED_IDENTITY else None,
        canonical_contract_id=contract if identity_status == RelationIdentityStatus.VALIDATED_IDENTITY else None,
        identity_record_ref=(
            opaque("identity_record_", "identity:" + seed)
            if identity_status == RelationIdentityStatus.VALIDATED_IDENTITY
            else None
        ),
        mapping_resolution_ref=(
            opaque("identity_resolution_", "mapping:" + seed)
            if identity_status == RelationIdentityStatus.VALIDATED_IDENTITY
            else None
        ),
        evidence_refs=(EVIDENCE,),
    )
    return create_relation_event(
        economic_event_id=economic_event_id,
        source_system_id="synthetic.r7",
        source_artifact_sha256=artifact,
        source_business_key_hash=source_key,
        source_business_digest=source_digest,
        event_type=event_type,
        direction=direction,
        lifecycle_stage=stage,
        event_status=event_status,
        identity_binding=binding,
        counterparty_key=counterparty,
        document_id=document_id or ("DOC-" + seed),
        document_line_id=document_line_id,
        event_date=event_date,
        base_amount_minor=amount_minor,
        reversal_of_event_id=reversal_of_event_id,
        governed_relation_keys=tuple(sorted(relation_keys)),
        source_record_refs=source_refs,
    )
