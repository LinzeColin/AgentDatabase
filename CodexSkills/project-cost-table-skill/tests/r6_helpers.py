from __future__ import annotations

import hashlib
from pathlib import Path
from typing import Dict, Optional, Sequence

from project_cost_table.inventory import FileIdentity, source_id_for_relative_path
from project_cost_table.manifest import SourceSelection
from project_cost_table.money import MoneyProfile
from project_cost_table.readers.lifecycle import (
    LIFECYCLE_READER_VERSION,
    SLOT_READER_IDS,
    LifecycleReaderProfile,
    LifecycleReaderResult,
    read_lifecycle_source,
)
from project_cost_table.security import SecurityProfile

from synthetic_builders import write_tabular_xlsx


MODULE_ROOT = Path(__file__).resolve().parents[1]
EVIDENCE = "evidence://sha256/" + "d" * 64
EVIDENCE_B = "evidence://sha256/" + "e" * 64
HEADERS = (
    "Entity",
    "Project",
    "WBS",
    "Contract",
    "Counterparty",
    "Document",
    "Line",
    "EventType",
    "Status",
    "RowKind",
    "ReversalOf",
    "Note",
    "DocumentDate",
    "ApprovalDate",
    "InvoiceDate",
    "PaymentDate",
    "CollectionDate",
    "EffectiveDate",
    "ReversalDate",
    "TransactionAmount",
    "GrossAmount",
    "NetAmount",
    "TaxAmount",
    "Currency",
    "Extra",
)
FIELD_BINDINGS = {
    "legal_entity_source_key": "Entity",
    "project_source_key": "Project",
    "wbs_source_key": "WBS",
    "contract_source_key": "Contract",
    "counterparty_source_key": "Counterparty",
    "document_id": "Document",
    "document_line_id": "Line",
    "source_event_type": "EventType",
    "source_status": "Status",
    "source_row_kind": "RowKind",
    "reversal_of_source_key": "ReversalOf",
    "free_text": "Note",
    "document_date": "DocumentDate",
    "approval_date": "ApprovalDate",
    "invoice_date": "InvoiceDate",
    "payment_date": "PaymentDate",
    "collection_date": "CollectionDate",
    "effective_date": "EffectiveDate",
    "reversal_date": "ReversalDate",
    "transaction_amount": "TransactionAmount",
    "gross_amount": "GrossAmount",
    "net_amount": "NetAmount",
    "tax_amount": "TaxAmount",
    "currency": "Currency",
}
DATE_MODES = {
    "document_date": "ISO_OR_EXCEL_SERIAL",
    "approval_date": "ISO_OR_EXCEL_SERIAL",
    "invoice_date": "ISO_OR_EXCEL_SERIAL",
    "payment_date": "ISO_OR_EXCEL_SERIAL",
    "collection_date": "ISO_OR_EXCEL_SERIAL",
    "effective_date": "ISO_OR_EXCEL_SERIAL",
    "reversal_date": "ISO_OR_EXCEL_SERIAL",
}


def _event_rules(slot_id: str, evidence: Optional[str]) -> list:
    definitions = {
        "project_billing": (
            ("INVOICE", "CUSTOMER_INVOICE", "REVENUE", "BILLED", 1),
            ("CREDIT_NOTE", "CUSTOMER_CREDIT_NOTE", "REVENUE", "BILLED", -1),
        ),
        "cash_out": (
            ("PAYMENT", "SUPPLIER_PAYMENT", "CASH_OUT", "PAID", 1),
            ("REFUND", "SUPPLIER_REFUND", "CASH_OUT", "PAID", -1),
        ),
        "cash_in": (
            ("RECEIPT", "CUSTOMER_COLLECTION", "CASH_IN", "COLLECTED", 1),
            ("REFUND", "CUSTOMER_COLLECTION_REFUND", "CASH_IN", "COLLECTED", -1),
        ),
        "contract_and_changes": (
            ("CUSTOMER_CONTRACT", "CUSTOMER_CONTRACT_VALUE", "REVENUE", "CONTRACT_VALUE", 1),
            ("CUSTOMER_REDUCTION", "CUSTOMER_CONTRACT_REDUCTION", "REVENUE", "CONTRACT_VALUE", -1),
            ("SUPPLIER_COMMITMENT", "SUPPLIER_COMMITMENT", "COST", "COMMITMENT", 1),
            ("SUPPLIER_REDUCTION", "SUPPLIER_COMMITMENT_REDUCTION", "COST", "COMMITMENT", -1),
        ),
    }
    return [
        {
            "source_event_type": source_type,
            "event_type": event_type,
            "direction": direction,
            "lifecycle_stage": stage,
            "amount_multiplier": multiplier,
            "evidence_ref": evidence,
        }
        for source_type, event_type, direction, stage, multiplier in definitions[slot_id]
    ]


def reader_profile_mapping(slot_id: str, *, status: str = "ACTIVE") -> dict:
    evidence = EVIDENCE if status == "ACTIVE" else None
    required = ["document_id", "source_event_type", "source_status", "transaction_amount", "currency"]
    if slot_id == "project_billing":
        required.extend(["invoice_date", "gross_amount", "net_amount", "tax_amount"])
    elif slot_id == "cash_out":
        required.append("payment_date")
    elif slot_id == "cash_in":
        required.append("collection_date")
    elif slot_id == "contract_and_changes":
        required.extend(["approval_date", "effective_date"])
    else:
        raise ValueError("unsupported synthetic lifecycle slot")
    return {
        "schema_version": "kmfa.project_cost.lifecycle_reader_profile.v1",
        "profile_id": "SYNTHETIC-R6-" + slot_id.upper(),
        "status": status,
        "slot_id": slot_id,
        "reader_id": SLOT_READER_IDS[slot_id],
        "reader_version": LIFECYCLE_READER_VERSION,
        "schema_id": "schema.synthetic.r6.%s.v1" % slot_id,
        "sheet_name": "Lifecycle",
        "header_row": 1,
        "first_data_row": 2,
        "max_data_rows": 1000,
        "expected_headers": list(HEADERS),
        "column_bindings": dict(FIELD_BINDINGS),
        "date_modes": dict(DATE_MODES),
        "default_currency": None,
        "required_business_fields": required,
        "status_rules": [
            {"source_status": "APPROVED", "event_status": "SOURCE_ACTIVE", "evidence_ref": evidence},
            {"source_status": "PENDING", "event_status": "SOURCE_PENDING", "evidence_ref": evidence},
            {"source_status": "CANCELLED", "event_status": "SOURCE_CANCELLED", "evidence_ref": evidence},
            {"source_status": "REVERSED", "event_status": "SOURCE_REVERSED", "evidence_ref": evidence},
        ],
        "event_type_rules": _event_rules(slot_id, evidence),
        "default_event_rule": None,
        "row_kind_rules": [
            {
                "source_row_kind": "BUSINESS",
                "action": "EMIT_EVENT",
                "reason_code": None,
                "evidence_ref": evidence,
            },
            {
                "source_row_kind": "TOTAL",
                "action": "EXCLUDE_CONTROL",
                "reason_code": "EXCLUDED_SOURCE_TOTAL",
                "evidence_ref": evidence,
            },
        ],
        "automatic_project_assignment_allowed": False,
        "reader_decides_final_metric_inclusion": False,
        "evidence_refs": [EVIDENCE, EVIDENCE_B] if status == "ACTIVE" else [],
    }


def active_reader_profile(slot_id: str) -> LifecycleReaderProfile:
    return LifecycleReaderProfile.from_mapping(reader_profile_mapping(slot_id))


def source_selection(root: Path, relative_path: str, profile: LifecycleReaderProfile) -> SourceSelection:
    path = root / relative_path
    metadata = path.stat()
    return SourceSelection(
        slot_id=profile.slot_id,
        source_id=source_id_for_relative_path(relative_path),
        private_relative_path=relative_path,
        sha256=hashlib.sha256(path.read_bytes()).hexdigest(),
        identity=FileIdentity(
            device=metadata.st_dev,
            inode=metadata.st_ino,
            size_bytes=metadata.st_size,
            mtime_ns=metadata.st_mtime_ns,
            link_count=metadata.st_nlink,
        ),
        reader=profile.reader_id,
        reader_version=profile.reader_version,
        logical_source_period="2000-01",
        schema_id=profile.schema_id,
        schema_fingerprint=profile.schema_fingerprint,
        selection_resolution_ref=None,
    )


def business_row(
    slot_id: str,
    *,
    document_id: Optional[str] = "DOC-1",
    line_id: str = "1",
    event_type: Optional[str] = None,
    status: str = "APPROVED",
    amount: str = "100.00",
    project: Optional[str] = "PROJECT-S",
    note: Optional[str] = None,
    row_kind: str = "BUSINESS",
    gross: Optional[str] = None,
    net: Optional[str] = None,
    tax: Optional[str] = None,
    reversal_of: Optional[str] = None,
    reversal_date: Optional[str] = None,
    currency: str = "CNY",
    document_date: str = "2000-01-10",
    extra: Optional[str] = None,
) -> list:
    default_type = {
        "project_billing": "INVOICE",
        "cash_out": "PAYMENT",
        "cash_in": "RECEIPT",
        "contract_and_changes": "CUSTOMER_CONTRACT",
    }[slot_id]
    values: Dict[str, object] = {
        "Entity": "ENTITY-S",
        "Project": project,
        "WBS": "WBS-S",
        "Contract": "CONTRACT-S",
        "Counterparty": "COUNTERPARTY-S",
        "Document": document_id,
        "Line": line_id,
        "EventType": event_type or default_type,
        "Status": status,
        "RowKind": row_kind,
        "ReversalOf": reversal_of,
        "Note": note,
        "DocumentDate": document_date,
        "ApprovalDate": "2000-01-09" if slot_id == "contract_and_changes" else None,
        "InvoiceDate": "2000-01-10" if slot_id == "project_billing" else None,
        "PaymentDate": "2000-01-11" if slot_id == "cash_out" else None,
        "CollectionDate": "2000-01-12" if slot_id == "cash_in" else None,
        "EffectiveDate": "2000-01-10" if slot_id == "contract_and_changes" else None,
        "ReversalDate": reversal_date,
        "TransactionAmount": amount,
        "GrossAmount": gross if gross is not None else (amount if slot_id == "project_billing" else None),
        "NetAmount": net if net is not None else ("90.00" if slot_id == "project_billing" else None),
        "TaxAmount": tax if tax is not None else ("10.00" if slot_id == "project_billing" else None),
        "Currency": currency,
        "Extra": extra,
    }
    return [values.get(header) for header in HEADERS]


def write_source(path: Path, slot_id: str, rows: Sequence[Sequence[object]]) -> LifecycleReaderProfile:
    profile = active_reader_profile(slot_id)
    write_tabular_xlsx(path, [list(HEADERS), *rows], sheet_name=profile.sheet_name)
    return profile


def read_rows(root: Path, slot_id: str, rows: Sequence[Sequence[object]], *, name: str = "source.xlsx") -> LifecycleReaderResult:
    path = root / name
    profile = write_source(path, slot_id, rows)
    return read_lifecycle_source(
        input_root=root,
        selection=source_selection(root, path.name, profile),
        reader_profile=profile,
        security_profile=SecurityProfile.from_yaml(MODULE_ROOT / "config" / "security_limits.yml"),
        money_profile=MoneyProfile.from_yaml(MODULE_ROOT / "config" / "money_profile.yml"),
    )
