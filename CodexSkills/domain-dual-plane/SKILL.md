---
name: domain-dual-plane
description: Fail-closed domain modeling for repositories governed by machine/facts and exactly seven human-facing documents. Use only to resolve domain terms, boundaries, scenarios, or irreversible domain decisions without creating parallel governance files or crossing repositories.
metadata:
  short-description: Dual-plane, seven-document domain modeling
---

# Domain Dual Plane

Use this skill to sharpen a project's domain language, boundaries, and
high-consequence domain decisions only inside an already-governed repository.
It is a fail-closed adapter: preserve the repository's existing dual-plane
governance, document budget, and source-of-truth chain.

## Non-negotiable boundaries

- Never create CONTEXT.md, CONTEXT-MAP.md, docs/adr/, ADR files, a second
  glossary, a domain-model directory, or any new governance document or fact file.
- Never scan, clone, read, write, or infer facts from another repository. Work
  only in the active repository and its current worktree.
- The user has delegated pre-authorized, bounded maintenance inside a verified
  active repository. Apply a change without a per-change confirmation only when
  every gate, source mapping, and validation requirement below passes.
- Never edit a human-facing document directly when its header or renderer says
  it is generated. Never semantically rewrite an Owner handwritten area.
- Never make a domain change if it cannot be represented by an existing,
  approved machine-plane source and mapped to one or more of the seven human
  documents.

## When to use

Use only when at least one of these is true:

1. A business term is vague, overloaded, contradictory, or lacks a canonical
   Chinese/English definition.
2. A domain boundary, ownership rule, data contract, or invariant is unclear.
3. Concrete edge cases are needed to distinguish two plausible domain models.
4. Code, configuration, facts, and documented language contradict each other.
5. A decision is hard to reverse, surprising without context, and represents a
   real trade-off.

Do not use for ordinary implementation, merely looking up an existing term,
generic programming vocabulary, status reporting, or a decision that is easy to
reverse.

## Mandatory discovery — read-only first

Before discussing or proposing a change:

1. Report the current working directory, Git root, branch/upstream, HEAD, and
   git status --short --branch.
2. Confirm the active repository contains these seven canonical human documents:
   文档/00_我在哪.md, 01_产品需求.md, 02_系统架构.md, 03_口径字典.md,
   04_操作流程.md, 05_执行与验收.md, and 06_运维手册.md.
3. Confirm the repository's existing machine plane and its actual tools,
   including machine/facts/, machine/tools/render_human.py,
   machine/tools/check_doc_budget.py, and machine/tools/check_blocker_stop.py.
4. Read the target document header and the renderer's current mapping. Classify
   each target as GENERATED, OWNER_HANDWRITTEN, or UNKNOWN; do not infer this
   from another repository.
5. Locate an existing, schema-compatible machine-plane source. For terminology,
   this is normally the existing machine/facts/glossary.json and its current
   schema; for boundaries and decisions, use only an already approved source
   named by the local renderer or governance rules.

If any check fails, output ACTION: STOP with the missing or ambiguous governance
fact. Do not create a substitute file, field, directory, or schema.

## Dual-plane mapping

| Domain work | Only permitted source | Human-plane outcome |
|---|---|---|
| Canonical term, number, data shape, or invariant | Existing approved entry in machine/facts/glossary.json | 03_口径字典.md, using the local project's declared ownership/rendering rule |
| Boundary, ownership, relationship, or data contract | Existing approved fact/config/contract source mapped by local governance | 02_系统架构.md only through its declared source chain |
| Scenario or observable behaviour | Existing approved product, flow, acceptance, or feature source | The mapped part of 01_产品需求.md, 04_操作流程.md, or 05_执行与验收.md |
| Operational domain rule | Existing approved configuration or operations source | 06_运维手册.md through its declared source chain |
| Hard-to-reverse domain decision | An existing approved facts/events/configuration location with a declared schema | The existing mapped human document; never a new ADR |

00_我在哪.md remains a status/blocker surface, not a place to hide domain
specifications. Do not move domain modeling material there merely to make a
change fit.

## Four gates

### 1. Single-repository gate

The current Git root is the complete scope. Shared governance rules may be read
only if they are already available within that root. A cross-repository
relationship must be described as an explicit local contract reference, never
by opening or copying another repository's context.

### 2. Seven-document budget gate

Every proposed change must name one existing machine source and one or more of
the seven documents it affects. If it would require a new file, directory,
section family, or parallel taxonomy, stop.

### 3. Single-source-of-truth gate

Change only the approved machine-plane source, never duplicate the same fact in
multiple files. The human plane is updated only by the local project's declared
rendering/ownership path. A generated document is never edited directly; an
Owner handwritten document may receive only the narrow, pre-authorized
mechanical terminology or reference alignment defined below. All other Owner
changes receive proposed text only.

### 4. Qualified-change gate

For every candidate, state: canonical term or boundary, evidence, rejected
meaning(s), at least one edge case, affected source, affected human document,
and whether the change meets the three irreversible-decision criteria. If this
does not produce a material clarification, make no change.

## Default interaction and change protocol

1. Challenge ambiguous language and show the conflict or missing distinction.
2. Test it with one or two concrete edge cases.
3. Cross-check the current repository's code, configuration, facts, and
   document headers when they are in scope.
4. Return a compact domain change plan with:
   - canonical definition or boundary;
   - evidence and unresolved uncertainty;
   - existing source path and schema location;
   - affected item(s) among 00–06;
   - generated-versus-Owner classification;
   - validation and rollback plan.
5. Apply the smallest eligible change immediately under the pre-authorized
   maintenance rules below. Do not ask for a per-change confirmation.

## Pre-authorized unified maintenance

The skill may automatically perform only these minimal, local consistency
repairs after mandatory discovery:

- add or normalize a term in an existing glossary schema when its exact meaning
  is already VERIFIED by two independent local sources and no competing meaning
  exists;
- align an existing canonical term's spelling, Chinese/English label, or
  cross-reference across the seven documents without changing its meaning;
- repair a generated document only by updating its existing mapped fact source
  and running the local renderer; and
- correct an existing document reference or source annotation when the local
  renderer/header proves the target.

For an OWNER_HANDWRITTEN target, direct editing is permitted only for an exact,
mechanical terminology or reference alignment within an existing section. It
must preserve structure and surrounding prose, introduce no new semantic rule,
and pass all local validation. Any broader rewrite is a stop condition.

The following always require ACTION: STOP, not automatic maintenance:

- a new or changed business rule, invariant, ownership boundary, data contract,
  workflow, acceptance rule, configuration value, or architecture decision;
- conflicting evidence, an uncertain definition, or fewer than two independent
  local sources;
- an edit that would need a new schema field, file, directory, section family,
  or cross-repository read; or
- any attempt to bypass a generated-versus-Owner classification.

When an eligible change is applied:

1. Re-run mandatory discovery and confirm the source mapping is unchanged.
2. Modify only the existing, schema-compatible machine-plane entry, except for
   the narrow OWNER_HANDWRITTEN mechanical alignment allowed above. Do not add
   a new file, field family, directory, or human-plane duplicate.
3. Run the repository's existing renderer and governance checks:
   render_human.py, check_doc_budget.py, and check_blocker_stop.py.
4. If any validation fails, restore this skill's edit before ending and
   report the failure as ACTION: STOP. Do not leave an unrendered or
   contradictory fact behind.

## Required completion report

Begin with one of ACTION: NONE, ACTION: ACT, or ACTION: STOP, then state:

- active repository and confirmed scope;
- domain issue and canonical outcome;
- exact existing source and affected seven-document mapping;
- evidence status: VERIFIED, INFERRED, or UNKNOWN;
- checks run and their results;
- any owner decision or blocker;
- confirmation that no new governance files, schemas, or cross-repository reads
  were introduced.

## Stop conditions

Stop without mutation when any of these is true:

- the active repository lacks the verified dual-plane/seven-document contract;
- the target source or its schema does not already exist;
- the change would create CONTEXT.md, CONTEXT-MAP.md, docs/adr/, or a parallel
  glossary/decision record;
- the result requires reading or editing another repository;
- a generated-versus-Owner classification is unclear;
- the change is semantic rather than a pre-authorized mechanical consistency
  repair;
- governance validation cannot pass; or
- an Owner-only blocker is encountered.
