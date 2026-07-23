# Kingdee reader and accounting-basis contract (R5)

R5 implements a locked, value-only `.xlsx` reader, a manifest-selected ledger-bundle gate, and an evidence-backed 5001/6401/WIP reconciliation engine. It does not generate a final project-cost workbook and does not appoint a finance owner, authorized person, assignee, or company approver.

## Required gates before reading

1. R3 has selected exactly one `general_ledger` source—one workbook or one governed bundle—with source ID, full digest, logical period, reader version, schema ID and schema fingerprint.
2. A selected bundle has one private `ACTIVE` bundle profile binding the container digest and the exact portable inventory of every `.xlsx`/`.xls` member. Each member is either `INCLUDE` or `EXCLUDE_QUALIFIED_SCOPE`; exclusion requires member digest, reason and hash-bound evidence. An unlisted workbook, extra declaration, or unsupported spreadsheet-like member such as `.xlsb`, `.ods` or `.csv` blocks the slot rather than being treated as an attachment.
3. R2 preflight passes root containment, single-link/type/size, CRC and recursive archive limits. Every `.xlsx` member, including an evidence-excluded member, independently passes OOXML active-content, formula, DDE, macro, external-link and connection gates in an exclusive empty private scratch directory.
4. Every included `.xlsx` has its exact private `ACTIVE` Kingdee reader profile binding sheet, header sequence, canonical columns, date modes and hash-bound schema evidence. All included workbooks are read; a missing profile or partial result blocks the complete slot.
5. An included legacy `.xls` returns `UNSUPPORTED_LEGACY_XLS_SLOT` until a separate locked read-only reader exists. A legacy workbook may be excluded only by the evidence-qualified scope decision above. No Office/WPS/LibreOffice conversion is allowed.

The reader preserves source keys, account, voucher line, document/business/posting dates, debit, credit, balance, currency, status and row kind. Bundle records additionally preserve opaque container and member lineage. Missing values remain `null`. Empty physical rows are explicitly counted. Reader row, member and amount-side controls are private; the public summary contains only aggregate counts and zero/non-zero conservation status.

## Required accounting policy

The public policy file is a non-runnable template. A calculate/restate run needs an effective-dated `ACTIVE` private policy with hash-bound evidence for:

- exact source statuses and include/exclude actions;
- exact source row kinds and ledger semantics;
- exact account-to-bridge-group mappings and allowed semantics;
- CNY/base-currency scope, blank counter-side behavior and valuation basis;
- fiscal calendar, close date and prior closed-period snapshot rules.

Unknown status, row kind, account, period policy, identity, currency or valuation evidence is a hard blocker. Free text, final-report differences and amount similarity cannot activate a rule.

## Separate cost views and controls

`JOB_COST_INCURRED` is calculated only from approved WIP additions, adjustments and transfer-ins less true reversals and transfers to another scope. A 5001-to-6401 lifecycle transfer does not create another project cost and does not reduce the same project's incurred cost.

`GL_RECOGNIZED_COGS` is recognized COGS less COGS reversals. It never adds WIP balances.

For every legal entity + project + WBS/cost code + contract + bridge group + period:

```text
opening_WIP
+ additions
+ adjustments
+ transfer_in
- reversals
- other_transfers_out
- net_recognized_6401_COGS
= expected_closing_WIP

expected_closing_WIP - reported_closing_WIP = 0 cents
net_5001_to_6401_transfer - net_recognized_6401_COGS = 0 cents
```

The second equation prevents a 5001 credit and matching 6401 debit from being silently double-counted. Both deltas are non-waivable; a non-zero value blocks both named bases.

Every included/control row must have one effective R4 identity binding to canonical project + legal entity + WBS/cost code + contract. Only an exact requested canonical scope may enter a basis view; other fully resolved scopes are retained as `OUTSIDE_REQUESTED_SCOPE` exclusions and cannot be cross-aggregated. The requested scopes deterministically create the scope fingerprint used by closed-period snapshots. Account-level debit/credit controls and semantic counts are retained separately from the cross-account WIP bridge.

## Cutoff and restatement

`COST_POSTED_ACTUAL` uses posting date. Rows before the period, after the period, or after `as_of` are excluded with exact reasons and remain in source conservation. A run touching a closed period requires a bound prior snapshot. New, removed or changed closed-period ledger lines return `RESTATEMENT_REQUIRED`; only `restate` with an explicit superseded-run reference may proceed. Historical snapshots are never overwritten.

R5 success is `R5_RECONCILED_NOT_FINAL`: it proves the reader and basis controls passed for downstream work. Final generation remains a later Run and only occurs after every in-scope data and product gate passes.
