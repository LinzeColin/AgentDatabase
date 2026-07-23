# Two rounds × six reviewer-role cross-review

## Independence disclosure

The delivery environment did not expose a true independent SubAgent execution interface. The release therefore uses six **isolated reviewer roles with sealed domain checklists**, applies them in two materially different rounds, and backs each gate with executable static checks and integration tests. This is stronger than an unstructured self-review but weaker than six separately sampled external models; no file describes it as independent external-agent evidence.

## Round 1 — architecture and threat-model review

Six roles, 24 checks, all passed.

| Reviewer | Critical finding | Fix applied |
|---|---|---|
| Cognitive fidelity | “Like a person” lacked capabilities, strategy, negative capability, and contradiction handling | layered operating model, capability envelope, stop/refusal rules, divergence map |
| Research/provenance | URL count could masquerade as independent evidence | canonical origin clustering, Claim/source graph, coverage cube, saturation gaps |
| Agentic execution | Persona could answer without using real tools | identity gate plus model/plan/act/verify/record loop; fabricated tool success prohibited |
| Evaluation | target name and catchphrases could leak pretrained cues | anonymous-name, no-Skill baseline, foil, style-decoy, decision and long-horizon suites |
| Security/governance | merging private/fictional into one menu item could erase consent/canon rules | independent `subject_origin`; private/self authority gate; fictional/historical provenance rules |
| DevOps/efficiency | legacy path/frontmatter and broad context loading risked incompatibility and token waste | `.agents/skills`, only name/description frontmatter, explicit invocation, progressive disclosure |

## Round 2 — adversarial operations and longevity review

Six roles, 39 checks, all passed. This round adds crash, corruption, privacy, drift, and long-run failure probes rather than repeating Round 1.

| Reviewer | Adversarial finding | Fix applied |
|---|---|---|
| Cognitive fidelity | runtime convenience could mutate core identity; weighted identities could average incompatible rules | memory/model firewall, evidence-gated promotion, domain-relevance conflict routing |
| Research/provenance | runtime package could leak local paths/private locators; rewritten copies could create false consensus | sanitized ledger, private URL removal, origin/near-duplicate protocol, residual-limit disclosure |
| Agentic execution | crash between run-directory commit and state update could reuse or skip ambiguously | history/state reconciliation, stale-run recovery, immutable failure closeout, artifact hash manifest |
| Evaluation | static prompt tests could miss tool misuse, identity routing failure, or overlong context | tool-use, task-completion, identity-routing, planning and token-efficiency regression suites |
| Security/governance | source text could self-authorize access; empty/duplicate checksum lists could falsely verify | all source instructions treated as data; consent hard gate; checksum hardening |
| DevOps/efficiency | correct source package did not prove correct installed copy | post-copy verification, deterministic one-root ZIP, current and legacy path separation |

Machine-readable results: `audit/reviews/round-1.json` and `audit/reviews/round-2.json`.

## Residual risks

Target-specific fidelity still depends on lawful source access, source quality, host-model/tool capability, and genuinely independent held-out judging. This dependency-free release does not bundle an embedding model; semantic near-duplicate detection is a host-assisted protocol layered on content hashes, canonical origins, and manual adjudication. A filesystem counter is process-safe on one shared installation, but multi-machine distributed allocation requires an external transactional store.
