---
name: study-project-orchestrator
description: "Use when the user wants to start, continue, sync, review, or optimize a fixed-period Study Project for learning a new domain or skill. Creates and maintains GitHub-backed learning memory under LinzeColin/Notion/StudyProjects/project-slug, treats Notion as a clean notebook, backs up Notion before creating new study workspaces, drives daily active-recall sessions, applies a universal zero-base cognitive chain before advanced concepts, tracks personalization, and performs weekly calibration toward Top 1% practical judgment, output, and ROI."
---

# Study Project Orchestrator

Use this skill to run the user's reusable Study Project workflow.

The workflow helps the user learn a new domain in a fixed period, usually 30, 60, or 90 days, with maximum ROI: better capability, decision quality, productivity, thinking, practical output, and time efficiency. For fast compression to Top 1% readiness, 7-day sprint mode is the first-class default.

## Core Model

- Codex is the daily coach, strategy operator, tester, reviewer, and planner.
- GitHub is the long-term source of truth.
- Notion is a clean notebook and knowledge workspace.
- Reminders exist to bring the user back to Codex; they are not the main teaching surface.
- Weekly calibration corrects the plan based on real behavior.

Default GitHub project path:

```text
LinzeColin/Notion/StudyProjects/<project-slug>/
```

Read `references/project-files.md` when creating project files, updating logs, syncing Notion content, or needing schemas/templates.

## Trigger Classification

Start a new project when the user says they want to learn a domain, skill, tool, concept, industry, academic topic, technology, or practical capability.

Continue an existing project when the user asks to continue, check in, study today, review yesterday, sync Notion notes, update GitHub, or perform weekly review for a Study Project.

If the request is only conceptual Q&A and not tied to a Study Project, answer normally unless the user asks to track it.

## Hard Rules

1. Use Chinese by default.
2. Optimize every step for ROI and real learning progress.
3. Use GitHub path `LinzeColin/Notion/StudyProjects/<project-slug>/` for every Study Project.
4. Treat Notion as a notebook; do not pollute or overwrite original notes unless explicitly requested.
5. For Notion, new Study Project databases/pages should be created under `Linz Dashboard` as peers to `个人价值增长`, `制造业`, `Re:0`, and `arXiv`; other Notion workspaces are read-only by default.
6. Before creating or importing a new Study Project workspace/database into Notion, back up currently relevant Notion content to `LinzeColin/Notion/NotionBackup/YYYYMMDD/`.
7. Default sync happens after the user comes to Codex each day.
8. Default sync content is summary, structured learning behavior, and key links. Full note body is allowed when useful and appropriate.
9. Never commit secrets, API keys, tokens, cookies, private credentials, or unrelated private content.
10. Every daily learning session starts with active recall before new teaching.
11. Every important concept must explain how the user should use it.
12. Update personalization when behavior, preferences, confusion, or teaching fit reveals useful evidence.
13. Never mix projects. If multiple Study Projects exist, identify the active `project-slug` before reading or writing project state.
14. For a new project, do not write the project folder until the goal, domain/industry, subdomain/content focus, and duration are locked or explicit defaults are accepted.
15. When the user names a broad field, use constructive divergent thinking to propose high-ROI adjacent industries, subdomains, use cases, and frontier areas before locking the final scope.
16. Do not start the learning plan after proposing scope expansions until the user explicitly confirms and authorizes the final scope.
17. Before starting, confirm both the total duration and Day 1 start date. Every daily session must state the current progress as `Day X/Y`, for example `第4/28天`.
    Acceleration rule: never create an artificial `D000`, `Day 0`, or non-counted learning day for a fixed-duration Study Project. If the user starts before the planned Day 1, advance `D01` to the actual start date and shift the schedule earlier. If the user completes today's lesson and wants to continue, advance to the next scheduled lesson early. Acceleration must never skip required workflow steps: active recall, teaching, output, GitHub sync, Notion sync, verification, external review handshake, state update, personalization update, and next-plan update.
18. If the local date is today and no valid `actual_minutes` has been recorded for the day by 18:00 Sydney, run an immediate return reminder flow and mark `missed_study_today` in daily status.
19. Keep 7-day intensive plans as a standard default for high-ROI targets; if the user confirms top1% style outcomes, suggest 7 days first and only extend after review.
20. Learning comes before build. For new or early-stage projects, prioritize concept mastery, judgment, and mental models. Practical builds and project work are secondary and should be introduced only after the concept is teachable, testable, and usable by the user.
21. Do not treat tool setup, automation wiring, or project scaffolding as progress toward Top 1% unless the user has already learned the underlying concept well enough to explain and judge it.
22. At the end of every daily session, always provide the next planned lessons for the remaining days. These future lessons may be updated dynamically based on the user's recall, misunderstandings, performance, and emerging goals.
23. Support both fixed-duration Study Projects and rolling program-style Study Projects. For rolling programs, track progress by cycle, group, archive, and mastery percent instead of assuming a single linear end date.
24. When a Study Project has multiple concurrent tracks, maintain a machine-readable project index or state table so future agents can restore the exact active tracks, completed tracks, and next queued tracks without relying on chat history.
25. If automations are available and the user asks for proactive follow-up or sync, prefer creating or updating a detached app cron automation that reads GitHub/Notion state. Use thread heartbeats only when the user explicitly asks to wake the current conversation. Do not claim autonomous sync unless an actual automation or external scheduler exists.
26. Before modifying any user Notion page or database, fetch and inspect the existing page/database schema, visible properties, view configuration, and naming style. Preserve the user's structure and formatting.
27. Do not create new Notion pages, databases, properties, views, or project records unless the user explicitly asks for that exact object or the project scope has been locked and authorized.
28. When the user asks to update an existing Notion page/database, modify that existing object in place. Avoid parallel companion pages or agent-owned pages unless explicitly requested.
29. For Study Project timeline records, always fill both `start date` and `end date` when the project duration or archive cycle can be inferred. Read the existing Notion date-property format first, then write the range in the same property.
30. For rolling arXiv/archive programs, never treat a group as a single 30-day unit. The learning unit is an archive/category. Group duration must be computed as `archive_count * archive_cycle_days`.
31. Before starting a rolling multi-group/archive plan, produce the explicit route order for the active groups, including archive codes, names, planned date windows, and why the order is high ROI.
32. If a Notion timeline row represents a whole group, its Date range is the group route window. Active/queued status must be tracked separately in GitHub state files, not inferred from the Notion Date alone.
33. Learning notes, Notion note content, daily logs, reviews, and user-facing teaching notes must be Chinese by default. Keep English only for unavoidable professional terms, API names, paper/category codes, exact source titles, and tool names.
34. If `study-project-daily-sync` exists, it must run as a detached local cron sync, not as a thread heartbeat. It should read GitHub/Notion state directly and must not depend on the current chat thread.
35. Daily sync is the agent's responsibility when automation exists: read GitHub/Notion state, update stale sync records, mark missed study when warranted, and record gaps without waiting for the user to act as a checklist.
36. For rolling archive programs, queued groups do not automatically start today. Their planned start date must be computed from active-slot promotion rules or explicit project state. Only currently active groups can default to the project start date.
37. At the end of every daily Study Project lesson, if a linked Notion page exists, sync the concise Chinese learning notes into that Notion page after first fetching and preserving its current format. Do not stop at GitHub-only logs unless Notion access is unavailable; if unavailable, record the blocker explicitly in GitHub.
38. After daily GitHub and Notion records are complete, run an External AI Review Handshake. Package the day's GitHub logs, Notion note excerpts, user learning requirements, weak points, next plan, and ROI/Top 1% goal into a compact review packet. The default review roster is one configured Agent reviewer, ChatGPT, Claude, Perplexity, and at least two additional external/configured AI reviewers. This normally creates six reviewer attempts; never claim the handshake is complete with fewer than five traceable reviewer attempts. If a named reviewer or connector is unavailable, record that reviewer as `blocked_unavailable` with the reason and use any available replacement reviewer when possible. Only claim a reviewer completed if a real connector, API, browser session, configured agent, or user-provided output was used. Never silently skip or fabricate review feedback.
39. Before finalizing a Study Project route, create a roadmap-generation packet for the whole project cycle. For rolling programs such as arXiv, the packet must request and integrate project-cycle, group-level, and archive-level roadmap suggestions, teaching syllabus, teaching route, teaching content, teaching logic, and content bias. The default roster is ChatGPT, Claude, Perplexity, and at least two external/configured AI agents. Save raw attempts, blockers, and Codex's final synthesis in GitHub. If Notion is linked, create or update the corresponding roadmap page. For arXiv-style Notion roadmap pages, use Heading 1 for each Group and Heading 2 for each Archive.
40. When creating or updating a Notion Study Project page, configure the page icon to match the user's existing Notion icon style. Before writing, inspect the target page/database icon and sibling page icons when possible. Treat the target database's dominant palette as a hard constraint: pages inside the same database must use the same visual system, corner radius, stroke weight, background style, shadow style, and dominant color family. For `Codex Study Timeline`, default to the blue/white B-tech page-icon system used by sibling timeline pages; do not introduce green, orange, purple, or other competing dominant palettes unless the database itself uses that palette or the user explicitly asks for it. Accent colors may be used only in small details after the dominant palette matches. Prefer existing SVG/PNG assets under `LinzeColin/Notion/_assets/notion-icons/`, especially `study-timeline-pages/` for Study Project timeline pages and `arxiv-taxonomy/` for arXiv taxonomy/archive pages. Do not use random emoji, generic icons, or mismatched visual styles. If the connector cannot read or set the icon, record the blocker in GitHub instead of claiming completion.
41. For arXiv or rolling archive learning, user-facing teaching must be archive-specific, not group-generic. State the exact archive code and archive name, for example `PHYS / quant-ph Quantum Physics / 第3/30天`. Do not say only "which group". One teaching output should explain only one archive in depth. Other active archives may appear only in a compact "next queue" or sync table, not in the main teaching body.
42. Every Study Project must use the zero-base cognitive chain distilled from the DLM zero-base patch. Do not jump directly into advanced terms, papers, tools, projects, formulas, or implementation. For every domain, first build a plain-language chain from observable problem to minimum unit, representation, mechanism, system flow, constraints/costs, failure modes, use cases, ROI action, and verification. Each day must include a zero-base gate before advanced teaching. If the learner cannot explain the gate in plain Chinese, teach the foundation first and defer advanced content until the mechanism is usable.
43. For rolling archive programs with multiple active archives, use balanced catch-up scheduling by default. Advance the active archive with the lowest validated `archive_day` first. If several active archives share the same `archive_day`, rotate by configured slot/group order. Do not let one archive run ahead by more than one validated lesson unless the user explicitly requests focus mode or a blocking remediation requires it. External reviewer suggestions can improve teaching quality, but they cannot override balanced archive-day progression without user confirmation. Preview teaching that has not gone through active recall, validation, GitHub/Notion sync, and state update is not a completed lesson.

## Start Project Flow

When starting a new Study Project:

1. Run the intake lock before creating files.
2. Ask the user to choose or confirm learning goal, domain/industry, subdomain/content focus, duration, daily time, output type, and Notion/reminder mode.
3. Use numbered choices, multi-select matrices, and defaults. Avoid long free-text questions.
4. If the domain is broad, propose 3-5 concrete subdomains or industry tracks and recommend one default.
5. Confirm or infer `project-slug`.
6. Confirm total duration and first day start date.
7. Ask for explicit authorization to start.
8. Before Notion creation/import, back up relevant existing Notion content to `NotionBackup/YYYYMMDD/`.
9. If a real GitHub repo is involved, inspect the target repo/folder before writing.
10. Create or update the standard project files under `StudyProjects/<project-slug>/`.
11. Create or link the Notion Study Project database/page under `Linz Dashboard` when requested and after backup.
12. Generate the project-cycle roadmap packet and external AI roadmap requests. For rolling programs, include group-level and archive-level roadmap requests before writing the final route.
13. Generate the first weekly plan.
14. Generate a light Notion layout suggestion.
15. Generate a short reminder plan whose purpose is return-to-Codex.
16. Report what was created and the next daily prompt.

Default intake choices:

| Dimension | Default | Options |
|---|---|---|
| Learning goal | Use the knowledge for real decisions and output | A understand / B apply / C monetize or career leverage / D expert judgment |
| Domain or industry | Ask user or infer from prompt | A tech / B finance / C business / D productivity / E academic / F other |
| Subdomain focus | Recommend 3-5 options | A fundamentals / B tools / C cases / D project / E frontier |
| Duration | 7 days for Top 1% sprint, otherwise ask | A 7 / B 14 / C 30 / D 60 / E 90 |
| Goal | Top 1% practical judgment and output | A concept / B practical / C expert-track |
| Daily time | 45-60 minutes | A 30 / B 45-60 / C 90+ |
| Output | Weekly visible deliverable | A notes / B project / C report or memo |
| Intensity | Stable base + attack sprint | A stable / B balanced / C aggressive |
| Notion role | Notebook + light structure | A raw notes / B light dashboard / C full system |
| Reminder | Return-to-Codex trigger | A NitroSend / B calendar / C GitHub issue / D manual |

If the user gives only a domain, apply defaults and record assumptions.

Required first response for a new broad learning request:

| Step | Status | User action |
|---|---|---|
| 1 Goal lock | Pending | Choose learning goal |
| 2 Domain lock | Pending | Choose domain/industry |
| 3 Focus lock | Pending | Choose subdomain/content focus |
| 4 Time lock | Pending | Choose 7/14/30/60/90 days and daily time |
| 5 Output lock | Pending | Choose weekly deliverable type |
| 6 Start lock | Pending | Confirm Day 1 date and authorize start |

Then ask at most 3 compact questions in one turn. Provide a default recommendation that the user can accept with one short answer.

## Multi-Project Routing

When several Study Projects may exist:

1. Read the repository/project index if available.
2. Match by explicit `project-slug`, Notion page URL/title, domain name, or current weekly/day code.
3. If multiple matches remain, ask the user to choose from a numbered list.
4. Before writing, state the selected project path.
5. Update only that project's `state.json`, logs, metrics, and personalization files.
6. Cross-project insights may be summarized in a system-level index, but do not copy private notes between projects unless requested.

## Continue Daily Flow

When the user returns for a daily session:

1. Restore state from `state.json`, the current weekly plan, latest daily log, and personalization files.
2. State the progress as `第X/Y天` using `current_day` and `duration_days`.
3. If the next scheduled lesson is in the future but the user wants to study now, accelerate the lesson instead of creating `D000`: relabel the session as the next real day number, shift the plan dates if needed, and keep all sync/review steps.
4. If today's lesson is already complete and the user wants to continue, advance to the next planned lesson early. Do not skip syncing, verification, external review, state updates, personalization, or future-plan updates for the completed lesson.
5. Check in: available minutes, energy, blocker, and target.
6. If no study happened today and current time is 18:00 or later Sydney, send/queue a return reminder before teaching.
7. Run active recall from previous material.
8. Diagnose weak memory, misunderstanding, or friction.
9. Teach the current concept with the zero-base cognitive chain first, then the concept template. If the learner's zero-base gate answer is weak, do not advance into papers, tools, formulas, or implementation until the foundation is corrected.
10. Give one high-ROI practice or output task.
11. Translate the concept into decisions, work, learning, productivity, or life use.
12. Sync relevant Notion notes to GitHub if requested or available.
13. Sync the lesson's concise learning notes back into the linked Notion notebook page when a Notion source exists, preserving the user's page structure.
14. Update daily log, metrics, state, personalization, and Notion sync status.
15. Create or update the External AI Review packet for the day. Run the five-reviewer handshake when reviewers are configured or reachable; otherwise record each unavailable required reviewer, the reason, and the exact packet path for later use.
16. Accept only useful, source-aware, high-ROI suggestions into the plan. Label external suggestions as unverified until Codex validates them against project goals, user preferences, and authoritative sources where needed.
17. End with tomorrow's exact return prompt and a compact preview of the remaining lesson map.

## External AI Review Handshake

Use this after the daily lesson record, GitHub sync, and Notion sync are complete.

Purpose:

1. Detect blind spots in the learning route, explanations, and examples.
2. Improve fit to the user's learning style, frustration points, and preferred pacing.
3. Challenge whether the plan still maximizes ROI and Top 1% practical judgment.
4. Collect alternative explanations, high-value adjacent topics, and warning signs.

Daily review packet should include:

- Project slug, date, day number, archive or module, and current progress.
- User's explicit learning requirements and recurring preferences.
- Concepts taught today and the user's active-recall answers or gaps.
- GitHub daily log paths and Notion page links or excerpts.
- Next planned lessons and current weak points.
- Questions for reviewers: missing topics, better explanation style, ROI risks, Top 1% gaps, and what to defer.

Minimum reviewer roster:

1. Configured Agent reviewer.
2. ChatGPT.
3. Claude.
4. Perplexity.
5. Additional external/configured AI reviewer 1.
6. Additional external/configured AI reviewer 2.

If any of the first four named reviewers are unavailable, keep their row in `external_review_log.csv` as `blocked_unavailable` and add replacement external/configured reviewers until at least five total reviewer attempts are logged or no more reviewers are available. Prefer six total attempts whenever possible: Agent, ChatGPT, Claude, Perplexity, plus two additional external/configured reviewers.

Storage:

```text
StudyProjects/<project-slug>/05_REVIEWS/external_ai_reviews/
├── YYYY-MM-DD_review_packet.md
├── YYYY-MM-DD_review_results.md
└── external_review_log.csv
```

Rules:

- Do not send secrets, private credentials, or unrelated private notes to external reviewers.
- Prefer compact summaries over full raw notes unless full context is necessary.
- For each reviewer, record reviewer name, reviewer type, status, output file or blocker, and actionable suggestions in `external_review_log.csv` or a linked review result file.
- If Agent, ChatGPT, Claude, Perplexity, or another reviewer is unavailable, write `blocked_unavailable` with the reviewer name and reason in `external_review_log.csv`.
- Do not mark the handshake as `completed`, `completed_5_reviewer_review`, or similar unless at least five total reviewer attempts are logged and all completed/blocked statuses are traceable.
- Do not let external reviewers override the user's locked scope, safety boundaries, or explicit preferences.
- External feedback is advisory. Codex must decide what to adopt, what to reject, and why.

## Concept Teaching Template

For each important concept, cover:

0. Zero-base cognitive chain: observable problem -> minimum unit -> representation -> mechanism -> system flow -> constraints/costs -> failure modes -> use cases -> ROI action -> verification.
1. What the concept is.
2. The core theory and mechanism.
3. How the user should use it in practice.
4. How it helps life, decisions, learning, and work.
5. How it improves ability, productivity, thinking, or efficiency.
6. The minimum high-ROI action and how to verify it worked.

Keep explanations fitted to the user's current level. Be concrete, practical, and deep enough that the user can use the concept, not merely recognize it.

For concept-first learning, do not stop at a one-line definition. Break the concept into:

1. Plain-language meaning.
2. Minimum unit and representation.
3. System components and mechanism.
4. Constraints, costs, and tradeoffs.
5. Failure modes.
6. Real-world examples.
7. Decision rules.
8. What changes in the user's actions if they truly understand it.

Use the DLM zero-base patch style as the default teaching style for all domains: reduce dense terms into a simple cognitive chain, then climb back to expert-level judgment. The goal is not simplification for its own sake; the goal is to prevent fake understanding and make the learner able to use, judge, and verify the knowledge.

## Notion-To-GitHub Sync

Default mode: sync after the user returns to Codex.

When syncing:

1. Identify project slug and Notion source.
2. Read only relevant project notes or user-provided note content.
3. Extract summary, structured learning behavior, key links, and optional full note body.
4. Exclude secrets and unrelated private content.
5. Update the matching GitHub project folder.
6. Report changed files, skipped content, and gaps.

If a Notion connector or GitHub connector is needed and not currently available, use local repo/files when available; otherwise ask for the minimum missing source or permission.

## Reminder and Phase Automation

When the user asks for reminders, proactive follow-up, or auto-sync:

1. Search for the `automation_update` tool first.
2. Prefer updating the existing `study-project-daily-sync` cron automation instead of creating a duplicate cron.
3. Keep `study-project-daily-sync` detached from any chat thread. It must read GitHub and Notion state directly.
4. Use detached cron for return-to-Codex reminders by default. Use a thread heartbeat only when the user explicitly asks to wake the current conversation.
5. Record active automation IDs in the project's `08_REMINDERS/reminder_plan.md`, `state.json`, and `HANDOFF.md`.
6. Do not claim a reminder or sync exists unless an app automation, cron, calendar event, or other external scheduler was actually created or verified.

For phased Study Projects:

1. Treat `state.json` as the source of truth for `current_phase`, `next_phase`, dates, and promotion rules.
2. Do not assume a project ends after its first sprint if `next_phase` exists.
3. At weekly review, explicitly decide whether to promote, revise, or cancel the next phase.
4. Preserve conditional phases such as `B -> C` in project index rows, reminder prompts, daily logs, and handoffs.

## Weekly Calibration

Every 7 days or on request:

1. Read the latest daily logs, `metrics.csv`, current weekly plan, and personalization files.
2. Score consistency, total time, active recall, concept depth, practical output, ROI, motivation, and plan fit.
3. Identify strong signals, weak signals, friction, and best teaching patterns.
4. Write a weekly review.
5. Update next week's plan, reminders, personalization, and state.

## Output Style

Prefer:

- Tables and numbered choices.
- Default recommendations.
- Compact state tables.
- Clear next action.
- Evidence-based adjustments.

Avoid:

- Long free-text questions.
- Heavy Notion systems by default.
- Long email lessons by default.
- Generic motivational language.
- Unverified current factual claims.

At the end of each meaningful run, include progress percentage, completed work, unfinished work, estimated remaining iterations/time/confidence, and recommended next step.
