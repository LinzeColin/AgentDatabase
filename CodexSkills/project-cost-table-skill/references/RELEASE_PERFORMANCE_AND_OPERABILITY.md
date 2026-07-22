# R12 release, performance and operability contract

## What R12 releases

Product `0.2.0` releases the deterministic, fail-closed Skill workflow. Release means the public package, governed configurations, security corpus, exact arithmetic, input gate, source/event/Metric pipeline, safe workbook path and private regression controls passed their release gates.

Release does **not** mean the current company inputs are sufficient. The bound current snapshot remains `BLOCKED_SOURCE` until the missing or conflicting manifest, identity, reader/accounting, payroll/time, tax, interest and payment-mapping evidence is supplied or the user makes another permitted, auditable scope decision. A release PASS must never replace that business block.

## Input precheck and terminal behavior

Every real operation still starts with input sufficiency before source-body parsing. If input is insufficient, the Skill must:

1. show one compact missing/conflict matrix;
2. request supplement, qualified alternate evidence, actual scope reduction or an explicit decision to remain blocked;
3. reject silence as permission and reject omission of any non-waivable item while its affected Metric remains requested;
4. publish only diagnostic artifacts; and
5. print absolute `OUTPUT_DIR`, `PRIMARY_OUTPUT` and `OUTPUT_INDEX` locators.

When all data and every validation gate pass, the same governed calculate path directly generates the final two-basis workbook. The Skill neither appoints a finance owner/authorized person nor manages internal company approval. The calling Codex/operator uses `INTERNAL_PROCESS_HANDOFF.md` and the absolute output locator to continue the existing process outside this Skill.

## Performance profile

`config/performance_budgets.yml` is strict and fail-closed:

- one independent cold application-process baseline plus at least three independent subsequent processes;
- each selected source is reopened and fully SHA256-verified exactly once per process;
- no application cache; operating-system file cache may help subsequent processes, but never replaces the full digest;
- every subsequent wall time and peak RSS must be at most `1.50 ×` the cold baseline;
- candidate pairs are partitioned before comparison and may not exceed `1,000,000`;
- global unpartitioned quadratic matching is forbidden;
- full tests, adversarial/property/metamorphic corpus, R10/R11 private regression, actual bundled workbook runtime and staged privacy scan are mandatory;
- R12 cannot perform global installation.

The bound current snapshot workload measures source inventory, bytes read, full-digest counts, wall time, CPU time and peak RSS. It intentionally reports `business_files_parsed=0`, `rows_parsed=0` and `real_calculation_baseline_status=NOT_EVALUATED_BLOCKED_SOURCE`: current business parsing is prohibited while required profiles/policies remain unavailable. Synthetic final-generation tests separately exercise the actual bundled spreadsheet runtime.

## Benchmark command

Use a new absolute private output directory outside the read-only input root:

```bash
PYTHONDONTWRITEBYTECODE=1 python3 scripts/run_release_benchmark.py \
  --input-root /ABSOLUTE/READ_ONLY/INPUT_ROOT \
  --current-source-contract /ABSOLUTE/PRIVATE/current_source_contract.private.json \
  --current-source-contract-sha256 <SHA256> \
  --output-dir /ABSOLUTE/PRIVATE/NEW_R12_PERFORMANCE_OUTPUT
```

Exit `0` means only the aggregate R12 performance gate passed. Exit `2` means measured budget failure. Exit `4` means the snapshot, path, worker protocol or publication gate failed. The command atomically publishes:

- `performance_summary.json`
- `OUTPUT_INDEX.md`
- `output_index.json`
- `run_seal.sha256`

The summary binds product version, the exact release-workload code fingerprint and the performance-budget digest. It otherwise contains aggregate counts/resources only—no private locators, source names, source hashes or business values. The terminal repeats absolute output locations.

## Package validator

Before staging:

```bash
PYTHONDONTWRITEBYTECODE=1 python3 scripts/validate_skill_package.py \
  --working-tree \
  --output /ABSOLUTE/PRIVATE/NEW_PACKAGE_VALIDATION.json
```

After staging, repeat against the actual index:

```bash
PYTHONDONTWRITEBYTECODE=1 python3 scripts/validate_skill_package.py \
  --staged \
  --repo-root /ABSOLUTE/REPOSITORY_ROOT \
  --module-relative-root KMFA/project-cost-table-skill \
  --output /ABSOLUTE/PRIVATE/NEW_STAGED_VALIDATION.json
```

The validator requires version `0.2.0`, R0–R12 complete, global installation state `MACHINE_LOCAL_EXTERNAL`, implemented traceability/formulas, exact performance budgets, valid schemas/test matrix, release wording, and zero requested boundary findings. The immutable `R12_GLOBAL_INSTALL_ALLOWED=0` boundary proves that R12 itself did not install; a repository cannot truthfully record completion for every machine.

## Post-R12 standalone-install parity

The global copy is installed without repository metadata. Behavioral parity therefore requires the input-preflight entrypoint to operate from a complete `$CODEX_HOME/skills/project-cost-table-skill` root while preserving the same output-containment rule: public package files cannot receive run outputs, and only the local `private_runtime` subtree is allowed inside the module. If Git metadata is unavailable and the governed package markers are incomplete, symlinked or outside the registered Codex Skills root, preflight fails with `STANDALONE_MODULE_ROOT_INVALID` before runtime directories are created.

Global-install acceptance must run the full suite from the installed directory, execute a real missing-input preflight, verify absolute locators and detached seals, and compare every installed public file byte-for-byte with the selected clean-main commit. A conventional filesystem layout or a successful copy command alone is not behavioral parity.

## Stop and rollback conditions

Stop release and do not push/merge if any of these occurs:

- any test, schema, strict YAML/CSV, workbook, private replay/current block or performance check fails;
- the official workbook runtime is missing or only a skip is observed;
- a selected source is opened/hashed more than once per run, a full digest is skipped, or global quadratic matching appears;
- the current calculation is represented as validated or final;
- staged content includes private/raw material, secrets, unsafe binary extensions, local private paths or unclassified files;
- origin changes overlap release paths without review;
- Git remote/main parity or post-merge clean-main proof fails.

Atomic outputs never overwrite prior evidence. Git rollback uses the isolated worktree and normal commit/PR history; destructive reset and immediate unreachable-object pruning are prohibited. Global installation is a separate next Run after remote/main parity is proven.

## Surprise audit

R12 explicitly guards these easy-to-miss failures:

- a fast warm run that secretly reuses an application digest cache;
- a performance PASS that omits current `BLOCKED_SOURCE` status;
- a workbook test skipped because the dependency locator hangs;
- a package validator that checks the working tree but not the staged index;
- release metadata still carrying `NOT_RELEASED`, proposed performance status or stale formula implementation labels;
- success output without an absolute locator or without a detached seal;
- final generation being mistaken for internal company approval;
- global installation happening in the same R12 run before remote/main parity.
