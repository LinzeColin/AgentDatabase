---
name: awesome-selfhosted-data
description: Use when Codex needs to search, filter, compare, or shortlist self-hosted Free/Libre software from structured Awesome-Selfhosted data—by category, license, platform, project status, release freshness, or source repository—before architecture, deployment, or replacement decisions.
---

# Awesome-Selfhosted Data

Use the bundled structured snapshot in `references/source/` for precise
self-hosted software discovery. It is a catalog snapshot, not a security
assessment, compatibility guarantee, or deployment approval.

## Data map

- `references/source/software/<slug>.yml`: one project per file; includes
  name, URL, description, licenses, platforms, tags, repository, archived
  state, metadata timestamp, release, and commit-history fields when known.
- `references/source/tags/`: category definitions.
- `references/source/platforms/`: platform definitions.
- `references/source/licenses.yml` and `licenses-nonfree.yml`: license labels.
- `references/source/markdown/`: source rendering metadata.

## Workflow

1. State the constraints: function, users, deployment target, license,
   operations capacity, integrations, data sensitivity, and budget.
2. Search the project data without loading the full catalog:

   ```bash
   rg -n -i -C 3 '<feature|tag|license|platform>' references/source/software
   rg -n -i '<tag|platform>' references/source/tags references/source/platforms
   ```

3. Read only the shortlisted YAML records. Distinguish a project’s stated
   facts from missing fields and stale snapshot metadata.
4. For time-sensitive recommendations, verify the candidate’s official
   repository and documentation for maintenance, runtime support, security,
   migration/export, and licensing before recommending it.
5. Return a compact comparison: candidate, fit, source evidence, operational
   caveats, and the next verification needed.

## Constraints

- Do not equate a catalog entry, star count, or release field with production
  suitability or security.
- Do not download, deploy, or expose a listed service without explicit user
  authorization.
- This reference is pinned to
  `awesome-selfhosted/awesome-selfhosted-data` commit
  `0b4ea4e9778a39df12c78e70c9c8b7d6670377a7` (2026-07-29). Verify live
  sources whenever freshness matters.
- Preserve the upstream attribution and CC BY-SA 3.0 terms in
  `references/source/LICENSE` when redistributing or adapting the snapshot.
