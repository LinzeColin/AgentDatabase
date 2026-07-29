---
name: awesome-selfhosted
description: Use when Codex needs to discover, compare, or shortlist self-hosted Free/Libre software for deployment, replacement, or architecture work—such as analytics, backups, collaboration, databases, identity, notes, monitoring, AI, or web services—from the Awesome-Selfhosted catalog.
---

# Awesome-Selfhosted

Use the bundled catalog snapshot at `references/source/README.md` to create an
evidence-based shortlist of self-hosted software. The catalog is a discovery
source, not an endorsement, security assessment, or deployment approval.

## Workflow

1. Extract the decision constraints: workload, users, data sensitivity,
   licensing, operating system/container requirements, deployment model,
   budget, and desired integrations.
2. Search the relevant category or product term without loading the whole
   catalog:

   ```bash
   rg -n -i -C 2 '<category|feature|product>' references/source/README.md
   ```

   Useful category terms include `Generative Artificial Intelligence`,
   `Document Management`, `Identity Management`, `Monitoring`, `Note-taking`,
   `Password Managers`, and `Project Management`.
3. Read the matching entries and nearby category context only. Capture each
   candidate's stated license, project link, implementation language, and
   listed caveats.
4. For a time-sensitive choice, verify the project's official repository and
   documentation before recommending it. Check maintenance, supported runtime,
   security posture, migration/export path, and operational fit; do not infer
   these facts from a catalog row.
5. Return a short comparison with the decision constraints, candidates,
   evidence links, trade-offs, and a clearly marked recommendation or unknown.

## Output shape

| Candidate | Fit | License / deployment evidence | Caveats | Next verification |
| --- | --- | --- | --- | --- |

## Constraints

- Do not treat inclusion as a claim that a project is secure, current, or
  suitable for production.
- Do not download, install, or deploy a listed service without explicit user
  authorization.
- The reference is a pinned snapshot of
  `awesome-selfhosted/awesome-selfhosted` at commit
  `7d4d103528de45a68e63ae65c3c0f8ac431883c7` (2026-07-28). Verify current
  upstream information when freshness matters.
- Preserve the upstream attribution and CC BY-SA 3.0 terms in
  `references/source/LICENSE` when redistributing or adapting the snapshot.
