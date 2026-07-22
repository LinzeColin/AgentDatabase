# Feature Catalog

Status reflects released fail-closed product `0.2.0` after R12. Release proves the workflow gates; the current private calculation remains truthfully `BLOCKED_SOURCE` until required inputs are supplied.

| ID | Feature | Priority | Current status | Acceptance |
| --- | --- | --- | --- | --- |
| `F-001` | Manifest-based source selection and hash lock | P0 | IMPLEMENTED_R3; ledger bundle locks R5; multi-source locks R6; private current contract and drift review R11 | deterministic selected source set or blocking conflict; exact member inventory |
| `F-002` | Private/full and public/redacted inventory | P0 | IMPLEMENTED_R3 | public output contains no raw names, headers, hashes, or values |
| `F-003` | Strict Decimal money parser and rounding profile | P0 | IMPLEMENTED_R2 | invalid nonempty input fails; no float path |
| `F-004` | Safe ZIP/OOXML/XLS/PDF preflight | P0 | PREFLIGHT_IMPLEMENTED_R2; Kingdee XLSX integration implemented R5 | malicious corpus fails before extraction or parse |
| `F-005` | XLSX and legacy XLS readers | P0 | KINGDEE_VALUE_ONLY_XLSX_AND_BUNDLE_IMPLEMENTED_R5; included legacy XLS hard-blocks full slot | every workbook classified; all included XLSX read; no partial success |
| `F-006` | Project/entity/WBS/contract identity | P0 | IMPLEMENTED_R4 | exactly one evidence-backed identity per included fact |
| `F-007` | Economic event and lifecycle model | P0 | R6/R7 foundation + R9 explicit Metric adapters implemented | budget, commitment, accrual, actual, paid, forecast separated |
| `F-008` | Same-stage business duplicate detection | P0 | IMPLEMENTED_R7; changed versions and business equivalence require evidence | duplicate download counted once in its stage |
| `F-009` | Cross-stage event links and partial allocations | P0 | IMPLEMENTED_R7 DATA-LINK LAYER + R9 EXPLICIT METRIC INCLUSION ADAPTER | connected match group conserves zero cents |
| `F-010` | Reversal, credit, refund and supersession | P0 | SIGN + SOURCE LINEAGE R6; REVERSAL/SUPERSESSION RELATIONS R7 IMPLEMENTED | original, reversal, and residual lineage preserved |
| `F-011` | Kingdee 5001/6401/WIP basis bridge | P0 | ENGINE_IMPLEMENTED_R5; active private account/period/valuation policy required | both basis-specific control equations balance |
| `F-012` | RedCircle billed/payment/contract/collection events | P0 | GOVERNED VALUE-ONLY READERS IMPLEMENTED_R6; active private profiles required | cash, billing, and cost recognition not mixed |
| `F-013` | Fully loaded payroll and approved-time allocation | P0 | ENGINE_IMPLEMENTED_R8; active private component registry, controls, approved time and policy required | component, payroll, time, and allocation controls reconcile |
| `F-014` | Tax/VAT treatment | P0 when in scope | ENGINE_IMPLEMENTED_R8; direct project evidence or project policy required | tax base, source/recomputed tax, rate, recoverability and deltas traced |
| `F-015` | Management/interest/indirect formula registry | P0 when in scope | ALLOWLIST ENGINE + EFFECTIVE/SUPERSESSION GATES IMPLEMENTED_R8; active private inputs required | effective formula, policy, test vectors and inputs evidenced |
| `F-016` | Named Metric views and four status planes | P0 | IMPLEMENTED_R9; real current-source expected-block planes verified R11 | execution, input, calculation, generation cannot collapse |
| `F-017` | Reference replay isolated from calculate | P0 | IMPLEMENTED_R10; RELEASE-VALIDATED_R12; R11 production import/source binding remains reference-free | import and data-flow isolation plus exact replay/current block |
| `F-018` | Independent dual-channel aggregation | P0 | EVENT-LEVEL R7 + NAMED-METRIC R9 IMPLEMENTED | independent code paths differ by zero cents |
| `F-019` | Source conservation and unmatched pools | P0 | EVENT-LEVEL INCLUDED/EXCLUDED/PENDING/PARSE-ERROR POOLS IMPLEMENTED_R7 | included plus excluded plus pending plus parse error equals control total |
| `F-020` | Safe Excel/CSV reporting | P0 | TEXT GUARD R2 + VALUES-ONLY ARTIFACT-TOOL WORKBOOK R9 IMPLEMENTED | no macro, external link, or formula injection |
| `F-021` | Automatic final generation and restatement | P0 | IMPLEMENTED_R9 generation; current private run correctly blocked before calculation R11 | validated run generates final and changed input supersedes |
| `F-022` | Atomic output, rollback-safe manifest and detached seal | P0 | INPUT GATE R3 + FINAL/BLOCKED/FAILED RUN R9 IMPLEMENTED | no hash cycles; failed run leaves no final-looking artifact |
| `F-023` | Security/privacy staged scan | P0 | IMPLEMENTED_R1; WORKTREE + STAGED RELEASE GATES R12 | no classified private or raw material in Git diff |
| `F-024` | Performance baseline and candidate-pair guard | P0 | IMPLEMENTED_R12: cold/subsequent process baseline, 1.50× wall/RSS ceiling, full-digest-once and 1,000,000 pair ceiling | no unexplained regression and no global quadratic matching |
| `F-025` | Contract changes, retention and advances | P1 | CONTRACT/CHANGE CANDIDATES_R6 + CONTRACT-TO-INVOICE LINKS_R7; retention/advance balances pending | lifecycle-specific event and balance tests |
| `F-026` | Multi-currency and FX | P1 | REGISTERED_DEFERRED_R8; active FX and foreign currency block product 0.2.0 | effective rate and FX components traced |
| `F-027` | OCR/image extraction | P2 | DEFERRED | human-verified extraction pipeline before final use |
| `F-028` | Web UI/realtime integration | P2 | DEFERRED | separate approved product scope |
| `F-029` | Per-run input sufficiency and explicit handling | P0 | IMPLEMENTED_R3; exact current private insufficiency verified R11; release-validated R12 | missing inputs prompt; non-waivable gaps cannot be omitted |
| `F-030` | Absolute output locator and company-process handoff | P0 | IMPLEMENTED_R9; production/harness/benchmark/package-validator locators release-validated R12 | every run shows paths; final run writes index and handoff |

## Exclusions

The Skill does not appoint an internal approver, model the company approval workflow, or claim that file generation completes company approval. Once validation passes, the Skill generates the final file and hands the output location back to the operator for the existing internal process.
