# Research and source completeness

## Six base lanes

1. Systematic outputs: books, papers, essays, courses, code, patents, formal artifacts.
2. Conversations under pressure: interviews, debates, Q&A, hearings, conflicts.
3. Expression and interaction: rhetoric, editing, collaboration, live response.
4. External triangulation: colleagues, competitors, criticism, biography, peer review.
5. Decisions/actions/outcomes: what was chosen, rejected, delayed, reversed, failed and learned.
6. Timeline and facets: period, role, institution, incentives and changed beliefs.

Each identity adds its own high-value sources from `registries/identity-families.json`.

## Source records

Record source ID, canonical origin, URL/local locator, author, publication/event date, retrieval date, language, rights/authorization, source tier, role/period, lane, content hash, near-duplicate cluster, transcript method, redaction, and injection flags.

## Claim graph

A Claim stores statement, epistemic type, supporting and counter sources, independent origin clusters, contexts, role/period, confidence, applicability, falsifiers, alternatives and supersession. Citation count is not source independence.

## Completeness and stopping

Use a coverage cube across identity × role × period × lane × source family × language × decision context × success/failure. After the initial pass, search only the critical gaps. Stop when two successive gap-driven rounds add no high-impact Claim and every critical cell is evidenced or explicitly unresolved. Report what could not be accessed; never claim literal global exhaustiveness.
