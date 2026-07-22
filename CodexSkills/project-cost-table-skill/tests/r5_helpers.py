from __future__ import annotations

import hashlib
from pathlib import Path
from typing import Iterable, Mapping, Optional, Sequence

from project_cost_table.accounting_basis import (
    AccountingBasisPolicy,
    AccountingScope,
    LedgerIdentityBinding,
    accounting_scope_fingerprint,
)
from project_cost_table.identity import ProjectIdentityRecord
from project_cost_table.inventory import FileIdentity, source_id_for_relative_path
from project_cost_table.manifest import SourceSelection
from project_cost_table.money import MoneyProfile
from project_cost_table.readers.kingdee import KingdeeReaderProfile, KingdeeReaderResult, read_kingdee_ledger
from project_cost_table.security import SecurityProfile

from synthetic_builders import write_tabular_xlsx


MODULE_ROOT = Path(__file__).resolve().parents[1]
EVIDENCE = "evidence://sha256/" + "a" * 64
EVIDENCE_B = "evidence://sha256/" + "b" * 64
IDENTITY_EVIDENCE = "evidence:" + "c" * 64
ACCOUNTING_SCOPES = (
    AccountingScope(
        canonical_project_id="PROJECT-CANONICAL-1",
        legal_entity_id="ENTITY-CANONICAL-1",
        wbs_or_cost_code="WBS-CANONICAL-1",
        canonical_contract_id="CONTRACT-1",
    ),
)
SCOPE_FINGERPRINT = accounting_scope_fingerprint(ACCOUNTING_SCOPES)
HEADERS = (
    "Entity",
    "Project",
    "WBS",
    "Contract",
    "Account",
    "Voucher",
    "Line",
    "DocumentDate",
    "BusinessDate",
    "PostingDate",
    "Debit",
    "Credit",
    "Balance",
    "Currency",
    "Status",
    "RowKind",
)
FIELD_BINDINGS = {
    "legal_entity_source_key": "Entity",
    "project_source_key": "Project",
    "wbs_source_key": "WBS",
    "contract_source_key": "Contract",
    "account_code": "Account",
    "voucher_id": "Voucher",
    "voucher_line_id": "Line",
    "document_date": "DocumentDate",
    "business_date": "BusinessDate",
    "posting_date": "PostingDate",
    "debit": "Debit",
    "credit": "Credit",
    "balance": "Balance",
    "currency": "Currency",
    "source_status": "Status",
    "source_row_kind": "RowKind",
}


def reader_profile_mapping(*, headers: Sequence[str] = HEADERS, status: str = "ACTIVE") -> dict:
    return {
        "schema_version": "kmfa.project_cost.kingdee_reader_profile.v1",
        "profile_id": "SYNTHETIC-KINGDEE-R5",
        "status": status,
        "reader_id": "kingdee_ledger_v2",
        "reader_version": "2.0.0",
        "schema_id": "schema.synthetic.kingdee.r5.v1",
        "sheet_name": "Ledger",
        "header_row": 1,
        "first_data_row": 2,
        "max_data_rows": 1000,
        "expected_headers": list(headers),
        "column_bindings": dict(FIELD_BINDINGS),
        "date_modes": {
            "document_date": "ISO_OR_EXCEL_SERIAL",
            "business_date": "ISO_OR_EXCEL_SERIAL",
            "posting_date": "ISO_OR_EXCEL_SERIAL",
        },
        "evidence_refs": [EVIDENCE] if status == "ACTIVE" else [],
    }


def active_reader_profile() -> KingdeeReaderProfile:
    return KingdeeReaderProfile.from_mapping(reader_profile_mapping())


def source_selection(root: Path, relative_path: str, profile: KingdeeReaderProfile) -> SourceSelection:
    path = root / relative_path
    metadata = path.stat()
    return SourceSelection(
        slot_id="general_ledger",
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


def standard_rows(*, closing: str = "20.00", cogs: str = "80.00") -> list:
    def row(
        line: str,
        account: str,
        kind: str,
        *,
        debit: Optional[str] = None,
        credit: Optional[str] = None,
        balance: Optional[str] = None,
        status: str = "POSTED",
        posting: str = "2000-01-31",
        currency: str = "CNY",
    ) -> list:
        return [
            "ENTITY-S",
            "PROJECT-S",
            "WBS-S",
            "CONTRACT-1",
            account,
            "V-" + line,
            line,
            posting,
            posting,
            posting,
            debit,
            credit,
            balance,
            currency,
            status,
            kind,
        ]

    return [
        list(HEADERS),
        row("1", "5001", "OPENING", balance="0.00", posting="2000-01-01"),
        row("2", "5001", "WIP_ADD", debit="100.00", credit="0.00"),
        row("3", "5001", "WIP_TO_COGS", debit="0.00", credit=cogs),
        row("4", "6401", "COGS", debit=cogs, credit="0.00"),
        row("5", "5001", "CLOSING", balance=closing),
        row("6", "5001", "WIP_ADD", debit="999.00", credit="0.00", status="DRAFT"),
        row("7", "5001", "WIP_ADD", debit="777.00", credit="0.00", posting="2000-02-01"),
        [None] * len(HEADERS),
    ]


def read_rows(root: Path, rows: Sequence[Sequence[object]]) -> KingdeeReaderResult:
    path = root / "ledger.xlsx"
    write_tabular_xlsx(path, rows)
    profile = active_reader_profile()
    return read_kingdee_ledger(
        input_root=root,
        selection=source_selection(root, path.name, profile),
        reader_profile=profile,
        security_profile=SecurityProfile.from_yaml(MODULE_ROOT / "config" / "security_limits.yml"),
        money_profile=MoneyProfile.from_yaml(MODULE_ROOT / "config" / "money_profile.yml"),
    )


def accounting_policy_mapping(*, closed_through: Optional[str] = None, status: str = "ACTIVE") -> dict:
    evidence = EVIDENCE if status == "ACTIVE" else None
    return {
        "schema_version": "kmfa.project_cost.accounting_basis_policy.v1",
        "policy_id": "SYNTHETIC-ACCOUNTING-BASIS-R5",
        "policy_version": "1.0.0",
        "status": status,
        "effective_from": "1999-01-01",
        "effective_to": None,
        "base_currency": "CNY",
        "evidence_refs": [EVIDENCE] if status == "ACTIVE" else [],
        "valuation_policy_ref": EVIDENCE_B if status == "ACTIVE" else None,
        "blank_counter_side_as_zero": False,
        "wip_to_cogs_control_required": True,
        "status_rules": [
            {"source_status": "POSTED", "action": "INCLUDE", "reason_code": "INCLUDED_POSTED", "evidence_ref": evidence},
            {"source_status": "DRAFT", "action": "EXCLUDE", "reason_code": "EXCLUDED_DRAFT", "evidence_ref": evidence},
        ],
        "row_kind_rules": [
            {"source_row_kind": "OPENING", "semantic": "WIP_OPENING", "evidence_ref": evidence},
            {"source_row_kind": "CLOSING", "semantic": "WIP_CLOSING", "evidence_ref": evidence},
            {"source_row_kind": "WIP_ADD", "semantic": "WIP_ADDITION", "evidence_ref": evidence},
            {"source_row_kind": "WIP_ADJUST", "semantic": "WIP_ADJUSTMENT", "evidence_ref": evidence},
            {"source_row_kind": "WIP_TRANSFER_IN", "semantic": "WIP_TRANSFER_IN", "evidence_ref": evidence},
            {"source_row_kind": "WIP_REVERSAL", "semantic": "WIP_REVERSAL", "evidence_ref": evidence},
            {"source_row_kind": "WIP_OTHER_OUT", "semantic": "WIP_OTHER_TRANSFER_OUT", "evidence_ref": evidence},
            {"source_row_kind": "WIP_TO_COGS", "semantic": "WIP_TO_COGS_TRANSFER", "evidence_ref": evidence},
            {"source_row_kind": "WIP_FROM_COGS", "semantic": "WIP_FROM_COGS_REVERSAL", "evidence_ref": evidence},
            {"source_row_kind": "COGS", "semantic": "COGS_RECOGNITION", "evidence_ref": evidence},
            {"source_row_kind": "COGS_REVERSAL", "semantic": "COGS_REVERSAL", "evidence_ref": evidence},
            {"source_row_kind": "TOTAL", "semantic": "EXCLUDE_CONTROL", "evidence_ref": evidence},
        ],
        "account_rules": [
            {
                "account_code": "5001",
                "bridge_group_id": "BRIDGE-5001-6401",
                "valid_from": "1999-01-01",
                "valid_to": None,
                "allowed_semantics": [
                    "WIP_OPENING",
                    "WIP_CLOSING",
                    "WIP_ADDITION",
                    "WIP_ADJUSTMENT",
                    "WIP_TRANSFER_IN",
                    "WIP_REVERSAL",
                    "WIP_OTHER_TRANSFER_OUT",
                    "WIP_TO_COGS_TRANSFER",
                    "WIP_FROM_COGS_REVERSAL",
                ],
                "evidence_ref": evidence,
            },
            {
                "account_code": "6401",
                "bridge_group_id": "BRIDGE-5001-6401",
                "valid_from": "1999-01-01",
                "valid_to": None,
                "allowed_semantics": ["COGS_RECOGNITION", "COGS_REVERSAL"],
                "evidence_ref": evidence,
            },
        ],
        "period_policy": {
            "calendar_id": "SYNTHETIC-CALENDAR",
            "closed_through": closed_through,
            "late_posting_mode": "REQUIRE_BOUND_PRIOR_SNAPSHOT_FOR_CLOSED_PERIOD",
        },
    }


def active_accounting_policy(*, closed_through: Optional[str] = None) -> AccountingBasisPolicy:
    return AccountingBasisPolicy.from_mapping(accounting_policy_mapping(closed_through=closed_through))


def identity_record() -> ProjectIdentityRecord:
    record = ProjectIdentityRecord(
        canonical_project_id="PROJECT-CANONICAL-1",
        legal_entity_id="ENTITY-CANONICAL-1",
        wbs_or_cost_code="WBS-CANONICAL-1",
        project_code="PROJECT-S",
        project_name=None,
        customer_id=None,
        contract_ids=("CONTRACT-1",),
        source_aliases=("source://kingdee/SYNTHETIC-PROJECT",),
        valid_from="1999-01-01",
        valid_to=None,
        identity_status="APPROVED",
        mapping_resolution_ref="identity_resolution_" + "1" * 32,
        evidence_refs=(IDENTITY_EVIDENCE,),
    )
    record.validate()
    return record


def identity_bindings(records: Iterable[object]) -> tuple:
    identity = identity_record()
    return tuple(
        LedgerIdentityBinding(
            source_record_ref=record.source_record_ref,
            identity_record=identity,
            canonical_contract_id="CONTRACT-1",
            binding_evidence_ref=EVIDENCE,
        )
        for record in records
    )
